"""
sync.py — shared upsert logic used by:
  - management/commands/sync_solutions.py  (CLI / cron)
  - views.py  (on-the-fly fallback when DB is empty)
"""
from django.db import transaction
from .models import Topic, Solution


def upsert_solutions(raw_list: list) -> list:
    """
    Upsert a list of raw SDP solution dicts into the DB.
    Returns the list of serialized dicts for immediate use.
    """
    serialized = []

    with transaction.atomic():
        for raw in raw_list:
            # ── Topic ────────────────────────────────────────
            raw_topic = raw.get("topic") or {}
            topic_obj = None
            if raw_topic.get("id"):
                topic_obj, _ = Topic.objects.update_or_create(
                    sdp_id=raw_topic["id"],
                    defaults={
                        "name":     raw_topic.get("name", ""),
                        "icon_key": raw_topic.get("folder_name", "") or "",
                    },
                )

            # ── Solution ──────────────────────────────────────
            sdp_id = raw.get("id", "")
            if not sdp_id:
                continue

            fields = {
                "display_id":  (raw.get("display_id") or {}).get("display_value", ""),
                "title":       raw.get("title", "Sin título"),
                "description": raw.get("description") or "",
                "topic":       topic_obj,
                "status":      (raw.get("approval_status") or {}).get("name", ""),
                "author":      (raw.get("created_by") or {}).get("name", ""),
                "updated_sdp": (raw.get("last_updated_time") or {}).get("display_value", ""),
                "hits":        int(raw.get("no_of_hits") or 0),
                "keywords":    raw.get("keywords") or "",
                "is_public":   raw.get("is_public", False),
            }

            sol, _ = Solution.objects.update_or_create(sdp_id=sdp_id, defaults=fields)

            serialized.append({
                "id":          sol.sdp_id,
                "display_id":  fields["display_id"],
                "title":       fields["title"],
                "description": fields["description"],
                "topic":       topic_obj.name if topic_obj else "",
                "status":      fields["status"],
                "author":      fields["author"],
                "updated":     fields["updated_sdp"],
                "hits":        fields["hits"],
                "keywords":    fields["keywords"],
                "is_public":   fields["is_public"],
            })

    return serialized
