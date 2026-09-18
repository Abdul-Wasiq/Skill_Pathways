"""
AI Post Assistant (spec §15).

Takes draft post text + a requested action (improve, fix grammar, make
professional, make concise, expand, rewrite, change tone) and returns
a suggested revision. The API layer must NEVER auto-publish this —
it's returned to the user as a suggestion for them to review and
explicitly submit via the normal post-creation endpoint.
"""
from app.schemas.ai import PostAssistantResponse
from app.services.ai_service import ai_service, AIServiceError

_VALID_ACTIONS = {
    "improve", "fix_grammar", "make_professional", "make_concise",
    "expand", "generate_title", "suggest_hashtags", "rewrite", "change_tone",
}

_ACTION_INSTRUCTIONS = {
    "improve": "Improve the overall clarity and quality of the writing.",
    "fix_grammar": "Fix grammar and spelling only — preserve the author's voice and meaning as closely as possible.",
    "make_professional": "Rewrite in a more professional, polished tone suitable for a career platform.",
    "make_concise": "Make this significantly more concise while keeping the key message.",
    "expand": "Expand this with more detail and context, staying true to the original point.",
    "generate_title": "Keep the content mostly as-is, but focus on generating a strong suggested_title.",
    "suggest_hashtags": "Keep the content as-is, but focus on generating relevant suggested_hashtags.",
    "rewrite": "Rewrite this from scratch conveying the same core message differently.",
    "change_tone": "Adjust the tone as requested by the user (see their instructions), keeping meaning intact.",
}

_SYSTEM_PROMPT = """You help users write posts for a professional career/social platform.
You are given draft text, a requested action, and optional extra instructions. Follow the
action. Never fabricate facts, achievements, or claims not present in the original draft.
Respond ONLY with a JSON object:
{"revised_content": "...", "suggested_title": "optional short title or empty string",
 "suggested_hashtags": ["#tag1", "#tag2"]}
suggested_hashtags: 0-5 relevant hashtags, only if genuinely useful for this post."""


async def assist_post(draft_content: str, action: str, extra_instructions: str = "") -> PostAssistantResponse:
    if action not in _VALID_ACTIONS:
        raise ValueError(f"Unknown action: {action}. Must be one of {sorted(_VALID_ACTIONS)}")

    instruction = _ACTION_INSTRUCTIONS[action]
    user_prompt = f"ACTION: {instruction}\n"
    if extra_instructions:
        user_prompt += f"EXTRA INSTRUCTIONS: {extra_instructions}\n"
    user_prompt += f"DRAFT:\n{draft_content}"

    try:
        result = await ai_service.complete_json(_SYSTEM_PROMPT, user_prompt, temperature=0.5)
    except AIServiceError:
        # Fallback: return the original content unchanged rather than crashing,
        # so the UI can still show *something* and the user can edit manually.
        return PostAssistantResponse(
            revised_content=draft_content,
            suggested_title="",
            suggested_hashtags=[],
        )
    return PostAssistantResponse(**result)
