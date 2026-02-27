"""Prompt templates for CV evaluation against Google Team role matrix."""

SYSTEM_ROLE = """You are an expert recruiter and technical assessor for Google Cloud support and engineering teams. You evaluate candidate CVs against a precise skill matrix for different specializations.

CRITICAL — Accuracy: You MUST match the candidate's actual profile to the correct area and score (1-5). Do NOT be overly conservative. If the CV clearly shows strong background in a domain (e.g. AI/ML, data science), you MUST assign score 4 or 5 (High) for the matching specialization (e.g. Data — AI and ML). Underestimating a clear profile fit is an error. Score 4-5 = High (strong fit); 3 = Medium; 1-2 = Basic. Respond only with valid JSON when asked for structured output."""


def _skills_to_text(spec_data: dict) -> str:
    """Format a specialization's skills from skill_matrix for the prompt."""
    lines = []
    for category, key in [
        ("Core Skills", "core_skills"),
        ("Web & Networking", "web_networking"),
        ("Additional Knowledge", "additional"),
        ("Soft Skills", "soft_skills"),
    ]:
        block = spec_data.get(key)
        if not block:
            continue
        lines.append(f"\n{category}:")
        if isinstance(block, dict):
            for skill, req in block.items():
                if isinstance(req, dict):
                    r = req.get("requirement", "")
                    lvl = req.get("level", "")
                    lines.append(f"  - {skill}: {r} - {lvl}")
                else:
                    lines.append(f"  - {skill}: {req}")
        else:
            for item in block:
                lines.append(f"  - {item}")
    return "\n".join(lines) if lines else "N/A"


def build_role_requirements_text(area: str, specialization: str, spec_data: dict) -> str:
    """Build the requirement block for one role (area + specialization)."""
    skills_text = _skills_to_text(spec_data)
    return f"""## Role: {area} — {specialization}

Required skills and levels (Mandatory = must have; Needed = important; level = Basic/Intermediate/Advanced):

{skills_text}
"""


EVALUATION_PROMPT = """Evaluate the following candidate CV against this Google Team role requirement.

{requirements}

---
CANDIDATE CV (excerpt):
---
{cv_text}
---

Based only on the CV content, assign a fit score from 0 to 100 (integer) for this role. Consider:
- Match of mandatory skills and level (Advanced/Intermediate/Basic).
- Relevance of experience and technologies.
- Gaps in required areas.

Respond with a JSON object only, no other text:
{{"score": <0-100>, "summary": "<2-3 sentences on fit>", "strengths": ["<strength1>", "<strength2>"], "gaps": ["<gap1>", "<gap2>"]}}
"""


SUMMARY_AND_RECOMMENDATION_PROMPT = """You have evaluated a candidate CV against multiple Google Team specializations. Here are the per-role scores and summaries:

{per_role_results}

---
Original CV excerpt (for context):
---
{cv_excerpt}
---

Tasks:
1. Write a short, manager-friendly candidate summary (3-5 sentences): background, main technical strengths, and overall fit for Google Cloud / support roles.
2. Recommend the single best role (Area + Specialization) for this candidate based on the scores and strengths, and explain in 1-2 sentences why.

Respond with a JSON object only:
{{"candidate_summary": "<paragraph>", "recommended_role": "<Area - Specialization>", "recommendation_reason": "<1-2 sentences>"}}
"""


def get_evaluation_prompt(requirements: str, cv_text: str) -> str:
    return EVALUATION_PROMPT.format(requirements=requirements, cv_text=cv_text[:12000])


def get_summary_prompt(per_role_results: str, cv_excerpt: str) -> str:
    return SUMMARY_AND_RECOMMENDATION_PROMPT.format(
        per_role_results=per_role_results,
        cv_excerpt=cv_excerpt[:6000],
    )


# --- Area scores (5 areas, sum = 100%) ---
AREA_SCORES_PROMPT = """You are evaluating a candidate CV for Google Cloud team roles. The candidate can fit across five AREAS only:

1. Infrastructure
2. Networking
3. Platform
4. Data
5. Other

Distribute a total of 100% across these five areas according to how well the CV fits each area (based on skills, experience, and technologies). The five percentages MUST sum to exactly 100.

---
CANDIDATE CV (excerpt):
---
{cv_text}
---

Respond with a JSON object only, no other text. Use integer percentages. Example format:
{{"Infrastructure": 25, "Networking": 15, "Platform": 30, "Data": 20, "Other": 10}}
"""


def get_area_scores_prompt(cv_text: str) -> str:
    return AREA_SCORES_PROMPT.format(cv_text=cv_text[:12000])


# Strong-fit signals per (area, specialization) for accurate profile matching (e.g. AI background → Data)
PROFILE_SIGNALS = {
    ("Data", "AI and ML"): "Strong-fit evidence: machine learning, ML, AI, data science, TensorFlow, Keras, PyTorch, model development, neural networks, Python for ML, data pipelines, SQL/BQL, ETL. If the candidate has clear AI/ML or data-science background, assign score 4 or 5 (High).",
    ("Data", "Data Analytics"): "Strong-fit evidence: data analytics, SQL, MapReduce, Spark, Hadoop, HDFS, batch/streaming pipelines, data warehousing. If the candidate has strong analytics/engineering background, assign score 4 or 5 (High).",
    ("Infrastructure", "Compute"): "Strong-fit evidence: Linux, databases, command line, system administration, OS internals. Assign 4-5 only with clear systems/compute focus.",
    ("Platform", "GKE & Anthos"): "Strong-fit evidence: Kubernetes, GKE, Anthos, containers, Docker, cloud platforms. Assign 4-5 with strong K8s/cloud experience.",
    ("Other", "Looker"): "Strong-fit evidence: Looker, BI, data visualization, SQL, analytics tools. Assign 4-5 with clear BI/analytics focus.",
}


def _get_profile_signals(area: str, specialization: str) -> str:
    return PROFILE_SIGNALS.get((area, specialization), "")


# --- Specialization: score 1-5 and category Basic / Medium / High ---
SPEC_LEVEL_PROMPT = """Evaluate the candidate CV fit for this specific role with STRICT ACCURACY. Match the candidate's actual profile to the correct score; do not underestimate clear fits.

Role: {area} — {specialization}

Required skills (summary):
{requirements_summary}
{profile_signals_block}

---
CANDIDATE CV (excerpt):
---
{cv_text}
---

Score scale 1-5 (integer only):
- 5 = Excellent fit: CV clearly shows strong, direct experience and skills for this role. For Data — AI and ML, clear AI/ML or data science background = 5 or 4.
- 4 = Strong fit: clear relevant experience.
- 3 = Medium fit: some relevant experience but not dominant.
- 2 = Basic fit: limited evidence.
- 1 = Poor fit: little or no evidence.

Categories: 1-2 = Basic, 3 = Medium, 4-5 = High.

Respond with a JSON object only:
{{"score": <integer 1-5>}}
"""


# --- One description per area (based on strongest specializations) ---
AREA_DESCRIPTION_PROMPT = """For each of the five areas below, the candidate has been rated per specialization (score 1-5, category Basic/Medium/High). Write exactly ONE short description (1-2 sentences) per area, focusing on the strongest specializations and overall fit for that area. Be consistent with the scores: areas with higher scores (4-5, High) should sound stronger.

Specialization scores by area (1-5, Basic/Medium/High):
{specs_by_area}

---
CANDIDATE CV (excerpt, for context):
---
{cv_text}
---

Respond with a JSON object only. Keys must be exactly: Infrastructure, Networking, Platform, Data, Other.
{{"Infrastructure": "<1-2 sentences>", "Networking": "<1-2 sentences>", "Platform": "<1-2 sentences>", "Data": "<1-2 sentences>", "Other": "<1-2 sentences>"}}
"""


def get_spec_level_prompt(area: str, specialization: str, requirements_summary: str, cv_text: str) -> str:
    signals = _get_profile_signals(area, specialization)
    profile_signals_block = f"\nProfile accuracy — {specialization}:\n{signals}\n" if signals else ""
    return SPEC_LEVEL_PROMPT.format(
        area=area,
        specialization=specialization,
        requirements_summary=requirements_summary[:2000],
        profile_signals_block=profile_signals_block,
        cv_text=cv_text[:8000],
    )


def get_area_description_prompt(specs_by_area: str, cv_text: str) -> str:
    return AREA_DESCRIPTION_PROMPT.format(
        specs_by_area=specs_by_area,
        cv_text=cv_text[:6000],
    )


# --- Education, soft skills, and previous jobs extraction (as short list items) ---
EDUCATION_SOFT_SKILLS_JOBS_PROMPT = """From the candidate CV below, extract the following as JSON. Use arrays of short bullet-style strings (one line each).

1. education: list of short items — each degree, certification, or training (e.g. "MSc Computer Science, University X", "AWS Certified"). If none found, return ["Not specified in CV"].
2. soft_skills: list of short items — each observed soft skill or strength (e.g. "Client-facing communication", "English proficiency", "Team leadership"). Max 8 items.
3. previous_jobs: list of short items — each role as "Role — Company (dates or duration)" (e.g. "ML Engineer — Acme Corp (2020–2023)"). Chronological order, most recent first. Max 10 items. If none clearly listed, return ["Not specified in CV"].

---
CANDIDATE CV (excerpt):
---
{cv_text}
---

Respond with a JSON object only:
{{"education": ["item1", "item2", ...], "soft_skills": ["item1", "item2", ...], "previous_jobs": ["Role — Company (dates)", ...]}}
"""


def get_education_soft_skills_prompt(cv_text: str) -> str:
    return EDUCATION_SOFT_SKILLS_JOBS_PROMPT.format(cv_text=cv_text[:10000])
