"""Persistent JSON storage for CV analyses and metrics."""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

AREAS_ORDER = ["Infrastructure", "Networking", "Platform", "Data", "Other"]
# Estimated human review time per CV (minutes) — thorough technical review
HUMAN_REVIEW_MINUTES = 45


class Storage:
    def __init__(self, data_dir: Path = None):
        self._path = (data_dir or Path(__file__).resolve().parent.parent / "data") / "analyses.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write([])

    # ── internal helpers ───────────────────────────────────────────────────────

    def _read(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _write(self, data: List[Dict[str, Any]]) -> None:
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── CRUD ───────────────────────────────────────────────────────────────────

    def save_analysis(
        self,
        filename: str,
        result: Dict[str, Any],
        analysis_time_seconds: float,
    ) -> str:
        analyses = self._read()
        analysis_id = str(uuid.uuid4())
        metrics = result.get("metrics") or {}
        record = {
            "id": analysis_id,
            "filename": filename,
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_time_seconds": round(analysis_time_seconds, 2),
            "api_calls": metrics.get("api_calls", 0),
            "total_tokens": metrics.get("total_tokens", 0),
            "model_used": metrics.get("model_used", "gemini-3-pro"),
            "human_review_minutes": HUMAN_REVIEW_MINUTES,
            "result": result,
        }
        analyses.append(record)
        self._write(analyses)
        return analysis_id

    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        for a in self._read():
            if a.get("id") == analysis_id:
                return a
        return None

    def delete_analysis(self, analysis_id: str) -> bool:
        analyses = self._read()
        new = [a for a in analyses if a.get("id") != analysis_id]
        if len(new) == len(analyses):
            return False
        self._write(new)
        return True

    def list_analyses(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        analyses = self._read()
        total = len(analyses)
        # Sort newest first
        sorted_analyses = sorted(analyses, key=lambda x: x.get("timestamp", ""), reverse=True)
        page = sorted_analyses[offset: offset + limit]
        # Return slim version (no full result blob)
        slim = []
        for a in page:
            res = a.get("result") or {}
            slim.append({
                "id": a["id"],
                "filename": a.get("filename", ""),
                "timestamp": a.get("timestamp", ""),
                "analysis_time_seconds": a.get("analysis_time_seconds", 0),
                "api_calls": a.get("api_calls", 0),
                "total_tokens": a.get("total_tokens", 0),
                "model_used": a.get("model_used", ""),
                "most_fitted_area": res.get("most_fitted_area", ""),
                "area_scores": res.get("area_scores", {}),
                "candidate_summary": res.get("candidate_summary", ""),
                "human_review_minutes": a.get("human_review_minutes", HUMAN_REVIEW_MINUTES),
            })
        return {"total": total, "items": slim}

    # ── Metrics ────────────────────────────────────────────────────────────────

    def get_metrics(self) -> Dict[str, Any]:
        analyses = self._read()
        total = len(analyses)
        if total == 0:
            return {
                "total_analyses": 0,
                "total_api_calls": 0,
                "total_tokens": 0,
                "avg_analysis_time_seconds": 0,
                "min_analysis_time_seconds": 0,
                "max_analysis_time_seconds": 0,
                "total_human_time_saved_minutes": 0,
                "avg_human_time_saved_minutes": HUMAN_REVIEW_MINUTES,
                "human_review_minutes_per_cv": HUMAN_REVIEW_MINUTES,
                "analyses_by_area": {a: 0 for a in AREAS_ORDER},
                "analyses_by_model": {},
                "recent_times": [],
            }

        times = [a.get("analysis_time_seconds", 0) for a in analyses]
        total_api_calls = sum(a.get("api_calls", 0) for a in analyses)
        total_tokens = sum(a.get("total_tokens", 0) for a in analyses)
        total_ai_minutes = sum(times) / 60
        total_human_minutes = total * HUMAN_REVIEW_MINUTES
        total_saved = round(total_human_minutes - total_ai_minutes, 1)

        by_area: Dict[str, int] = {a: 0 for a in AREAS_ORDER}
        by_model: Dict[str, int] = {}
        for a in analyses:
            area = (a.get("result") or {}).get("most_fitted_area", "Other")
            if area in by_area:
                by_area[area] += 1
            model = a.get("model_used", "unknown")
            by_model[model] = by_model.get(model, 0) + 1

        # Last 30 analyses for time trend chart
        sorted_a = sorted(analyses, key=lambda x: x.get("timestamp", ""))[-30:]
        recent_times = [
            {
                "timestamp": a.get("timestamp", ""),
                "analysis_time_seconds": a.get("analysis_time_seconds", 0),
                "api_calls": a.get("api_calls", 0),
            }
            for a in sorted_a
        ]

        return {
            "total_analyses": total,
            "total_api_calls": total_api_calls,
            "total_tokens": total_tokens,
            "avg_analysis_time_seconds": round(sum(times) / total, 1),
            "min_analysis_time_seconds": round(min(times), 1),
            "max_analysis_time_seconds": round(max(times), 1),
            "total_human_time_saved_minutes": max(0, total_saved),
            "avg_human_time_saved_minutes": round(HUMAN_REVIEW_MINUTES - (sum(times) / total / 60), 1),
            "human_review_minutes_per_cv": HUMAN_REVIEW_MINUTES,
            "analyses_by_area": by_area,
            "analyses_by_model": by_model,
            "recent_times": recent_times,
        }

    # ── Best candidates ────────────────────────────────────────────────────────

    def get_best_candidates(self) -> Dict[str, Any]:
        analyses = self._read()
        best: Dict[str, Optional[Dict[str, Any]]] = {a: None for a in AREAS_ORDER}

        for a in analyses:
            res = a.get("result") or {}
            area_scores = res.get("area_scores") or {}
            for area in AREAS_ORDER:
                score = area_scores.get(area, 1.0)
                current_best = best[area]
                if current_best is None or score > (current_best.get("area_scores", {}).get(area, 0)):
                    best[area] = {
                        "id": a["id"],
                        "filename": a.get("filename", ""),
                        "timestamp": a.get("timestamp", ""),
                        "most_fitted_area": res.get("most_fitted_area", ""),
                        "area_scores": area_scores,
                        "candidate_summary": res.get("candidate_summary", ""),
                        "best_specializations": res.get("best_specializations", []),
                        "education_list": res.get("education_list", []),
                        "score_in_area": score,
                    }

        return {"best_by_area": best}
