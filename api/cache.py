from django.core.cache import cache

CACHE_TTL = 3600  # 1 hora


def _serialize_solution(sol):
    """Convert a Solution ORM instance to a plain dict."""
    return {
        "id":          sol.sdp_id,
        "display_id":  sol.display_id,
        "title":       sol.title,
        "description": sol.description,
        "topic":       sol.topic.name if sol.topic else "",
        "status":      sol.status,
        "author":      sol.author,
        "updated":     sol.updated_sdp,
        "hits":        sol.hits,
        "keywords":    sol.keywords,
        "is_public":   sol.is_public,
    }


def get_cached_solutions():
    """
    Returns (list_of_dicts | None, was_cached).
    None means DB is also empty — caller should sync from SDP.
    """
    data = cache.get("sdp:solutions")
    if data is not None:
        return data, True

    from .models import Solution
    qs = Solution.objects.select_related("topic").all()
    if not qs.exists():
        return None, False

    data = [_serialize_solution(s) for s in qs]
    cache.set("sdp:solutions", data, timeout=CACHE_TTL)
    return data, False


def get_cached_topics():
    """
    Returns (list_of_dicts | None, was_cached).
    """
    data = cache.get("sdp:topics")
    if data is not None:
        return data, True

    from .models import Topic
    topics = (
        Topic.objects
        .prefetch_related("solutions")
        .all()
    )
    if not topics.exists():
        return None, False

    data = [{"name": t.name, "count": t.solutions.count()} for t in topics]
    cache.set("sdp:topics", data, timeout=CACHE_TTL)
    return data, False


def flush_cache():
    """Invalidate both cache keys — next request reads from DB."""
    cache.delete("sdp:solutions")
    cache.delete("sdp:topics")
