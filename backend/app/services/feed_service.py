"""
Personalized Feed Ranking Service (spec §19-20).

Per spec: "a practical rule-based + AI/semantic ranking system is
acceptable" for v1. This computes a relevance score per item from
real signals (skill overlap, recency, prior interactions) rather than
just returning posts in raw chronological order. It's structured as a
standalone service so the ranking function can be swapped/improved
later (e.g. with embeddings) without touching the API layer.
"""
import math
from datetime import datetime, timezone

from app.database import get_cursor


def _recency_score(created_at: datetime, half_life_hours: float = 48.0) -> float:
    """Exponential decay — newer items score closer to 1.0."""
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
    return math.exp(-age_hours / half_life_hours) if age_hours >= 0 else 1.0


def _get_user_skill_names(user_id: str) -> set[str]:
    with get_cursor() as cur:
        cur.execute(
            "SELECT s.name FROM user_skills us JOIN skills s ON s.id = us.skill_id WHERE us.user_id = %s",
            (user_id,),
        )
        return {row["name"].lower() for row in cur.fetchall()}


def _get_user_interacted_post_ids(user_id: str) -> set[str]:
    with get_cursor() as cur:
        cur.execute(
            "SELECT DISTINCT target_id FROM feed_interactions WHERE user_id = %s AND target_type = 'post'",
            (user_id,),
        )
        return {str(row["target_id"]) for row in cur.fetchall()}


def get_personalized_feed(user_id: str, limit: int = 20) -> dict:
    user_skills = _get_user_skill_names(user_id)
    interacted_posts = _get_user_interacted_post_ids(user_id)

    with get_cursor() as cur:
        # Recent posts with engagement counts
        cur.execute(
            """
            SELECT p.id, p.author_id, p.content, p.post_type, p.created_at,
                   u.name AS author_name,
                   (SELECT COUNT(*) FROM post_likes WHERE post_id = p.id) AS like_count,
                   (SELECT COUNT(*) FROM post_comments WHERE post_id = p.id) AS comment_count
            FROM posts p JOIN users u ON u.id = p.author_id
            ORDER BY p.created_at DESC
            LIMIT 100
            """
        )
        posts = cur.fetchall()

        # Open opportunities with their required/preferred skills for overlap scoring
        cur.execute(
            """
            SELECT op.id, op.title, op.type, op.location, op.created_at,
                   o.name AS organization_name
            FROM opportunities op JOIN organizations o ON o.id = op.organization_id
            WHERE op.status = 'open'
            ORDER BY op.created_at DESC
            LIMIT 100
            """
        )
        opportunities = cur.fetchall()

        cur.execute("SELECT opportunity_id, skill_id FROM opportunity_skills")
        opp_skill_links = cur.fetchall()
        cur.execute("SELECT id, name FROM skills")
        skill_names = {row["id"]: row["name"].lower() for row in cur.fetchall()}

    opp_skills_map: dict[str, set[str]] = {}
    for link in opp_skill_links:
        opp_id = str(link["opportunity_id"])
        opp_skills_map.setdefault(opp_id, set()).add(skill_names.get(link["skill_id"], ""))

    # --- Score posts ---
    ranked_posts = []
    for p in posts:
        recency = _recency_score(p["created_at"])
        engagement = math.log1p(p["like_count"] + 2 * p["comment_count"]) / 5.0  # soft-capped signal
        already_seen_penalty = 0.15 if str(p["id"]) in interacted_posts else 0.0
        score = round((recency * 0.5 + min(engagement, 1.0) * 0.5) - already_seen_penalty, 4)
        ranked_posts.append({**p, "relevance_score": max(score, 0)})
    ranked_posts.sort(key=lambda x: x["relevance_score"], reverse=True)

    # --- Score opportunities ---
    ranked_opportunities = []
    for o in opportunities:
        recency = _recency_score(o["created_at"], half_life_hours=24 * 14)  # opportunities decay slower
        opp_skills = opp_skills_map.get(str(o["id"]), set())
        skill_overlap = (
            len(opp_skills & user_skills) / len(opp_skills) if opp_skills and user_skills else 0.3
        )
        score = round(recency * 0.3 + skill_overlap * 0.7, 4)
        ranked_opportunities.append({**o, "relevance_score": score})
    ranked_opportunities.sort(key=lambda x: x["relevance_score"], reverse=True)

    return {
        "posts": ranked_posts[:limit],
        "opportunities": ranked_opportunities[:limit],
    }


def record_interaction(user_id: str, target_type: str, target_id: str, interaction: str) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO feed_interactions (user_id, target_type, target_id, interaction)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, target_type, target_id, interaction),
        )
