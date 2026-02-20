from django.core.cache import cache

CACHE_TTL = 3600  # 1 hora


def get_cached_solutions(token):
    """
    Returns (list_of_raw_solutions, was_cached).
    Calls SDP only on cache miss; stores result for CACHE_TTL seconds.
    """
    data = cache.get("sdp:solutions")
    if data is not None:
        return data, True

    from resources.solutions.sdp_solutions import SDPSolutions
    data = SDPSolutions.get_all_paginated(token)
    cache.set("sdp:solutions", data, timeout=CACHE_TTL)
    return data, False


def get_cached_topics(token):
    """
    Returns (list_of_topics, was_cached).
    Topics are derived from solutions; cached separately.
    """
    data = cache.get("sdp:topics")
    if data is not None:
        return data, True

    from resources.solutions.sdp_solutions import SDPSolutions
    data = SDPSolutions.get_topics(token)
    cache.set("sdp:topics", data, timeout=CACHE_TTL)
    return data, False


def flush_cache():
    """Invalidate both cached keys manually."""
    cache.delete("sdp:solutions")
    cache.delete("sdp:topics")
