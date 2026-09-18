"""
AI Opportunity Matching Engine.

Design (per spec §11, §29, §47): the numeric score is NEVER just
"ask an LLM for a percentage." It is computed by transparent,
measurable, rule-based logic with configurable weights. The AI
provider is used ONLY to generate a human-readable explanation of
a score that has already been computed deterministically — and even
that explanation is validated/sanitized before being shown to the user.

If the AI provider is unavailable or misconfigured, the feature still
works: it falls back to a template-based explanation rather than
crashing or lying about eligibility.
"""
from app.schemas.ai import MatchAnalysis
from app.services.ai_service import ai_service, AIServiceError

# Configurable weights (spec §47) — sum to 100.
WEIGHTS = {
    "skills": 40,
    "education": 20,
    "experience": 15,
    "eligibility": 15,
    "career_interests": 10,
}


def _score_skills(user_skill_names: set[str], required: list[str], preferred: list[str]) -> tuple[int, list[str], list[str]]:
    required_set = {s.lower() for s in required}
    preferred_set = {s.lower() for s in preferred}
    user_set = {s.lower() for s in user_skill_names}

    matched = sorted(s for s in required if s.lower() in user_set)
    matched += sorted(s for s in preferred if s.lower() in user_set and s not in matched)
    missing_required = sorted(s for s in required if s.lower() not in user_set)
    missing_preferred = sorted(s for s in preferred if s.lower() not in user_set)
    missing = missing_required + missing_preferred

    if not required_set and not preferred_set:
        return 100, [], []

    required_hit = len(required_set & user_set)
    preferred_hit = len(preferred_set & user_set)

    # Required skills weigh far more heavily than preferred ones.
    required_score = (required_hit / len(required_set) * 80) if required_set else 80
    preferred_score = (preferred_hit / len(preferred_set) * 20) if preferred_set else 20
    score = round(required_score + preferred_score)
    return min(score, 100), matched, missing


_STOPWORDS = {"in", "of", "or", "and", "a", "the", "related", "field", "degree", "with"}


def _significant_words(text: str) -> set[str]:
    return {w for w in text.lower().replace(",", " ").split() if w not in _STOPWORDS and len(w) > 1}


def _score_education(profile: dict, education_requirement: str | None) -> tuple[int, str]:
    if not education_requirement:
        return 100, "No specific education requirement listed."
    if not profile.get("degree") and not profile.get("field_of_study"):
        return 40, "Requirement not confirmed — your profile has no education info listed."

    req_words = _significant_words(education_requirement)
    degree_words = _significant_words(profile.get("degree") or "")
    field_words = _significant_words(profile.get("field_of_study") or "")

    # Word-overlap match rather than a brittle exact-substring check, so
    # "BS Computer Science" still matches "BS in Computer Science or related field".
    degree_overlap = len(degree_words & req_words) / len(degree_words) if degree_words else 0
    field_overlap = len(field_words & req_words) / len(field_words) if field_words else 0
    best_overlap = max(degree_overlap, field_overlap)

    if best_overlap >= 0.6:
        return 100, "Your degree/field closely matches the stated education requirement."
    if best_overlap >= 0.3:
        return 80, "Your degree/field partially aligns with the stated education requirement."
    return 55, "Education requirement not clearly confirmed from your profile — please review manually."


def _score_experience(years_experience: float, min_required: float) -> int:
    if min_required <= 0:
        return 100
    if years_experience >= min_required:
        return 100
    if years_experience <= 0:
        return 20
    return round(min(years_experience / min_required, 1.0) * 100)


def _score_eligibility(profile: dict, opportunity: dict) -> tuple[int, list[str]]:
    """Hard eligibility gates (e.g. minimum CGPA) — distinct from skill match."""
    notes = []
    score = 100

    min_cgpa = opportunity.get("min_cgpa")
    if min_cgpa is not None:
        user_cgpa = profile.get("cgpa")
        if user_cgpa is None:
            score -= 30
            notes.append(
                f"This opportunity requires a minimum CGPA of {min_cgpa}, but your "
                f"profile does not list a CGPA — eligibility could not be confirmed."
            )
        elif float(user_cgpa) < float(min_cgpa):
            score -= 60
            notes.append(
                f"Your listed CGPA is below the required minimum of {min_cgpa} for this opportunity."
            )
        else:
            notes.append(f"CGPA requirement of {min_cgpa} is satisfied.")

    return max(score, 0), notes


def compute_match(profile: dict, user_skill_names: list[str], years_experience: float,
                   opportunity: dict, required_skills: list[str], preferred_skills: list[str]) -> dict:
    """Pure, deterministic scoring — no AI call. This is the source of truth."""
    skills_score, matched, missing = _score_skills(set(user_skill_names), required_skills, preferred_skills)
    education_score, education_note = _score_education(profile, opportunity.get("education_requirement"))
    experience_score = _score_experience(years_experience, float(opportunity.get("min_experience_years") or 0))
    eligibility_score, eligibility_notes = _score_eligibility(profile, opportunity)

    # Career-interest similarity is a soft signal; without an embeddings
    # pipeline yet (spec §48 marks this as future work) we use a neutral
    # baseline so it doesn't unfairly penalize or inflate scores.
    career_interest_score = 70

    overall = round(
        skills_score * WEIGHTS["skills"] / 100
        + education_score * WEIGHTS["education"] / 100
        + experience_score * WEIGHTS["experience"] / 100
        + eligibility_score * WEIGHTS["eligibility"] / 100
        + career_interest_score * WEIGHTS["career_interests"] / 100
    )

    return {
        "match_score": overall,
        "eligibility_score": eligibility_score,
        "skills_score": skills_score,
        "education_score": education_score,
        "experience_score": experience_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "eligibility_notes": " ".join(eligibility_notes) if eligibility_notes else "No hard eligibility issues detected.",
        "education_note": education_note,
    }


def _fallback_explanation(computed: dict) -> str:
    """Used if the AI provider is unavailable — still explainable, just less fluent."""
    lines = []
    if computed["matched_skills"]:
        lines.append("Matched skills: " + ", ".join(computed["matched_skills"]) + ".")
    if computed["missing_skills"]:
        lines.append("Missing skills: " + ", ".join(computed["missing_skills"]) + ".")
    lines.append(computed["education_note"])
    lines.append(computed["eligibility_notes"])
    return " ".join(lines)


async def generate_explanation(computed: dict, opportunity_title: str) -> str:
    """Asks the AI provider to phrase the already-computed numbers as a
    friendly, honest explanation. Falls back to a template on any failure."""
    system_prompt = (
        "You are an assistant that explains career-opportunity match scores to a user. "
        "You are given already-computed scores and facts — do NOT invent new scores or "
        "claims. Never say someone is 'definitely eligible'; use cautious language like "
        "'appears to meet' or 'likely eligible' when appropriate. Respond ONLY with a JSON "
        'object of the form {"explanation": "..."} — 2-4 sentences, honest and specific.'
    )
    user_prompt = (
        f"Opportunity: {opportunity_title}\n"
        f"Match score: {computed['match_score']}\n"
        f"Skills score: {computed['skills_score']}, matched: {computed['matched_skills']}, "
        f"missing: {computed['missing_skills']}\n"
        f"Education note: {computed['education_note']}\n"
        f"Eligibility notes: {computed['eligibility_notes']}\n"
    )
    try:
        result = await ai_service.complete_json(system_prompt, user_prompt)
        explanation = result.get("explanation")
        if not explanation or not isinstance(explanation, str):
            raise AIServiceError("Malformed explanation from AI provider.")
        return explanation
    except AIServiceError:
        return _fallback_explanation(computed)


async def analyze_opportunity_match(profile: dict, user_skill_names: list[str], years_experience: float,
                                     opportunity: dict, required_skills: list[str],
                                     preferred_skills: list[str]) -> MatchAnalysis:
    computed = compute_match(profile, user_skill_names, years_experience, opportunity,
                              required_skills, preferred_skills)
    explanation = await generate_explanation(computed, opportunity.get("title", "this opportunity"))

    return MatchAnalysis(
        match_score=computed["match_score"],
        eligibility_score=computed["eligibility_score"],
        skills_score=computed["skills_score"],
        education_score=computed["education_score"],
        experience_score=computed["experience_score"],
        matched_skills=computed["matched_skills"],
        missing_skills=computed["missing_skills"],
        explanation=explanation,
        eligibility_notes=computed["eligibility_notes"],
    )
