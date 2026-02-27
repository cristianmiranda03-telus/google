"""CV evaluation — areas scores, specialization levels, metrics tracking."""
import json
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.fuelix_client import chat_completion
from config.settings import get_settings, get_skill_matrix
from src.prompts import (
    SYSTEM_ROLE,
    build_role_requirements_text,
    get_area_description_prompt,
    get_education_soft_skills_prompt,
    get_spec_level_prompt,
    get_summary_prompt,
)


def _parse_json_from_response(text: str) -> Optional[dict]:
    text = text.strip()
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        return None
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return None


def _list_roles(skill_matrix: dict) -> List[Tuple[str, str, dict]]:
    roles = []
    areas = skill_matrix.get("areas") or {}
    for area, area_data in areas.items():
        specs = (area_data or {}).get("specializations") or {}
        for spec_name, spec_data in specs.items():
            roles.append((area, spec_name, spec_data))
    return roles


def _score_to_level(score: int) -> str:
    if score >= 4:
        return "High"
    if score == 3:
        return "Medium"
    return "Basic"


LEVEL_TO_POINTS = {"Basic": 1, "Medium": 2, "High": 3}
LEVEL_ORDER = ["High", "Medium", "Basic"]
AREAS_ORDER = ["Infrastructure", "Networking", "Platform", "Data", "Other"]


def _area_counts(specializations: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {a: 0 for a in AREAS_ORDER}
    for s in specializations:
        area = s.get("area")
        if area in counts:
            counts[area] += 1
    return counts


def _area_scores_from_specializations(specializations: List[Dict[str, Any]]) -> Dict[str, float]:
    sums: Dict[str, float] = {a: 0.0 for a in AREAS_ORDER}
    counts = _area_counts(specializations)
    for s in specializations:
        area = s.get("area")
        if area in sums:
            sc = s.get("score")
            if isinstance(sc, (int, float)):
                sums[area] += max(1, min(5, int(sc)))
            else:
                sums[area] += 1
    out: Dict[str, float] = {}
    for a in AREAS_ORDER:
        n = counts.get(a, 0)
        out[a] = round(sums[a] / n, 1) if n else 1.0
    return out


def _most_fitted_area_from_specializations(specializations: List[Dict[str, Any]]) -> str:
    area_scores = _area_scores_from_specializations(specializations)
    by_area: Dict[str, List[Dict[str, Any]]] = {}
    for s in specializations:
        a = s.get("area")
        if a in AREAS_ORDER:
            by_area.setdefault(a, []).append(s)

    def _area_key(a: str) -> tuple:
        avg = area_scores.get(a, 1.0)
        n_high = sum(1 for s in by_area.get(a, []) if s.get("level") == "High")
        n_med = sum(1 for s in by_area.get(a, []) if s.get("level") == "Medium")
        return (avg, n_high, n_med)

    return max(AREAS_ORDER, key=_area_key)


def _best_specializations_for_area(area: str, specializations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    in_area = [s for s in specializations if s.get("area") == area]

    def _rank(s: Dict[str, Any]) -> tuple:
        score = s.get("score")
        sc = max(1, min(5, int(score))) if isinstance(score, (int, float)) else 1
        lvl = (s.get("level") or "Basic").strip()
        lvl_idx = LEVEL_ORDER.index(lvl) if lvl in LEVEL_ORDER else 2
        return (-sc, lvl_idx)

    return sorted(in_area, key=_rank)


def _extract_tokens(response: dict) -> int:
    usage = response.get("usage") or {}
    return usage.get("total_tokens", 0) or usage.get("completion_tokens", 0) or 0


def evaluate_cv(
    cv_text: str,
    *,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: int = 120,
    max_cv_chars: int = 12000,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> Dict[str, Any]:
    """
    Evaluate CV against all Google Team specializations.
    Returns scores, descriptions, profile info, and usage metrics.
    """
    settings = get_settings()
    api_key = api_key or settings.get("api_key")
    api_cfg = settings.get("api") or {}
    model = model or api_cfg.get("model", "gemini-3-pro")
    base_url = base_url or api_cfg.get("base_url")
    timeout = timeout or api_cfg.get("timeout_seconds", 120)
    temperature = (settings.get("evaluation") or {}).get("temperature", 0.2)

    if not api_key:
        raise ValueError("FUELIX_API_KEY (or FUELIX_SECRET_TOKEN) must be set in .env")

    skill_matrix = get_skill_matrix()
    roles = _list_roles(skill_matrix)
    cv_trimmed = (cv_text or "")[:max_cv_chars]

    api_call_count = 0
    total_tokens = 0
    api_times: List[float] = []

    def _call(messages: list, temp: Optional[float] = None) -> dict:
        nonlocal api_call_count, total_tokens
        t0 = time.time()
        out = chat_completion(
            messages=messages,
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            temperature=temp if temp is not None else temperature,
        )
        api_times.append(time.time() - t0)
        api_call_count += 1
        total_tokens += _extract_tokens(out)
        return out

    def _progress(pct: int, step: str) -> None:
        if progress_callback:
            progress_callback(pct, step)

    # ── 1. Per-specialization level ──────────────────────────────────────────
    _progress(5, "Preparing analysis…")
    specializations: List[Dict[str, Any]] = []
    total_specs = len(roles)

    for i, (area, specialization, spec_data) in enumerate(roles):
        pct = 5 + int((i / total_specs) * 58)
        _progress(pct, f"Evaluating {area} — {specialization}…")

        requirements_summary = build_role_requirements_text(area, specialization, spec_data)
        prompt = get_spec_level_prompt(area, specialization, requirements_summary, cv_trimmed)
        messages = [
            {"role": "system", "content": SYSTEM_ROLE},
            {"role": "user", "content": prompt},
        ]
        score = 1
        try:
            out = _call(messages, temp=temperature)
            choice = (out.get("choices") or [{}])[0]
            content = (choice.get("message") or {}).get("content") or ""
            parsed = _parse_json_from_response(content)
            if parsed:
                raw = parsed.get("score")
                if isinstance(raw, (int, float)):
                    score = max(1, min(5, int(raw)))
        except Exception:
            pass
        level = _score_to_level(score)
        specializations.append({
            "area": area,
            "specialization": specialization,
            "score": score,
            "level": level,
        })

    # ── 2. Area scores + most fitted ─────────────────────────────────────────
    area_scores = _area_scores_from_specializations(specializations)
    most_fitted_area = _most_fitted_area_from_specializations(specializations)
    best_specializations = _best_specializations_for_area(most_fitted_area, specializations)

    # ── 3. Area descriptions ─────────────────────────────────────────────────
    _progress(66, "Generating area descriptions…")
    area_descriptions: Dict[str, str] = {a: "" for a in AREAS_ORDER}
    by_area: Dict[str, List[Dict[str, Any]]] = {}
    for s in specializations:
        a = s.get("area", "Other")
        by_area.setdefault(a, []).append(s)
    specs_by_area_text = "\n".join(
        f"{area}: " + ", ".join(f"{s['specialization']} (score {s['score']}, {s['level']})" for s in by_area.get(area, []))
        for area in AREAS_ORDER
    )
    try:
        messages = [
            {"role": "system", "content": SYSTEM_ROLE},
            {"role": "user", "content": get_area_description_prompt(specs_by_area_text, cv_trimmed)},
        ]
        out = _call(messages)
        choice = (out.get("choices") or [{}])[0]
        content = (choice.get("message") or {}).get("content") or ""
        parsed = _parse_json_from_response(content)
        if parsed:
            for a in AREAS_ORDER:
                area_descriptions[a] = (parsed.get(a) or "").strip()
    except Exception:
        pass

    # ── 4. Education, soft skills, previous jobs ─────────────────────────────
    _progress(78, "Extracting profile information…")
    education_list: List[str] = []
    soft_skills_list: List[str] = []
    previous_jobs_list: List[str] = []
    try:
        messages = [
            {"role": "system", "content": SYSTEM_ROLE},
            {"role": "user", "content": get_education_soft_skills_prompt(cv_trimmed)},
        ]
        out = _call(messages)
        choice = (out.get("choices") or [{}])[0]
        content = (choice.get("message") or {}).get("content") or ""
        parsed = _parse_json_from_response(content)
        if parsed:
            ed = parsed.get("education")
            if isinstance(ed, list):
                education_list = [str(x).strip() for x in ed if x]
            elif isinstance(ed, str) and ed.strip():
                education_list = [ed.strip()]
            ss = parsed.get("soft_skills")
            if isinstance(ss, list):
                soft_skills_list = [str(x).strip() for x in ss if x]
            elif isinstance(ss, str) and ss.strip():
                soft_skills_list = [ss.strip()]
            pj = parsed.get("previous_jobs")
            if isinstance(pj, list):
                previous_jobs_list = [str(x).strip() for x in pj if x]
            elif isinstance(pj, str) and pj.strip():
                previous_jobs_list = [pj.strip()]
    except Exception:
        pass

    # ── 5. Candidate summary ─────────────────────────────────────────────────
    _progress(88, "Generating candidate summary…")
    results_text = f"Most fitted area: {most_fitted_area}\n"
    results_text += "Best specializations: " + ", ".join(
        f"{s['specialization']} (score {s['score']}, {s['level']})" for s in best_specializations
    ) + "\n"
    results_text += "All specializations:\n" + "\n".join(
        f"- {r['area']} - {r['specialization']}: {r['score']} ({r['level']})" for r in specializations
    )
    summary_messages = [
        {"role": "system", "content": SYSTEM_ROLE},
        {"role": "user", "content": get_summary_prompt(results_text, cv_trimmed)},
    ]
    candidate_summary = ""
    recommended_role = ""
    recommendation_reason = ""
    try:
        out = _call(summary_messages)
        choice = (out.get("choices") or [{}])[0]
        content = (choice.get("message") or {}).get("content") or ""
        summary_parsed = _parse_json_from_response(content)
        if summary_parsed:
            candidate_summary = summary_parsed.get("candidate_summary", "")
            recommended_role = (
                f"{most_fitted_area} - {best_specializations[0]['specialization']}"
                if best_specializations else most_fitted_area
            )
            recommendation_reason = summary_parsed.get("recommendation_reason", "")
        else:
            candidate_summary = content[:500] if content else "Summary not available."
            recommended_role = (
                f"{most_fitted_area} - {best_specializations[0]['specialization']}"
                if best_specializations else most_fitted_area
            )
    except Exception as e:
        candidate_summary = f"Summary generation failed: {e}"
        recommended_role = (
            f"{most_fitted_area} - {best_specializations[0]['specialization']}"
            if best_specializations else most_fitted_area
        )

    most_fitted_reason = (area_descriptions.get(most_fitted_area) or recommendation_reason or "").strip()
    if not most_fitted_reason and best_specializations:
        high_s = [s for s in best_specializations if s.get("level") == "High"]
        med_s = [s for s in best_specializations if s.get("level") == "Medium"]
        parts = []
        if high_s:
            parts.append(f"Strongest subarea expertise: {', '.join(s['specialization'] for s in high_s)} (High).")
        if med_s:
            parts.append(f"Good fit: {', '.join(s['specialization'] for s in med_s)} (Medium).")
        most_fitted_reason = " ".join(parts)

    _progress(96, "Finalizing…")

    return {
        "area_scores": area_scores,
        "area_descriptions": area_descriptions,
        "specializations": specializations,
        "most_fitted_area": most_fitted_area,
        "best_specializations": best_specializations,
        "most_fitted_reason": most_fitted_reason,
        "education_list": education_list,
        "soft_skills_list": soft_skills_list,
        "previous_jobs_list": previous_jobs_list,
        "candidate_summary": candidate_summary,
        "recommended_role": recommended_role,
        "recommendation_reason": recommendation_reason,
        "metrics": {
            "api_calls": api_call_count,
            "total_tokens": total_tokens,
            "avg_api_call_seconds": round(sum(api_times) / len(api_times), 2) if api_times else 0,
            "model_used": model,
        },
    }
