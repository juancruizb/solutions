import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from dotenv import load_dotenv

load_dotenv()

from .cache import get_cached_solutions, get_cached_topics, flush_cache


def _get_token():
    from resources.token.sdp_auth import SDPAuth
    return SDPAuth.get_access_token(
        client_id=os.getenv("SDP_CLIENT_ID"),
        client_secret=os.getenv("SDP_CLIENT_SECRET"),
    )


def solutions_list(request):
    """
    GET /api/v1/solutions/
    Flow: LocMemCache → DB → (if DB empty) SDP Cloud
    Filters: ?topic=Internet  ?status=Approved
    """
    try:
        data, cached = get_cached_solutions()

        if data is None:
            # DB empty — fall back to live SDP call and sync on the fly
            token = _get_token()
            from resources.solutions.sdp_solutions import SDPSolutions
            raw = SDPSolutions.get_all_paginated(token)
            from .sync import upsert_solutions
            data = upsert_solutions(raw)
            cached = False

        # Optional filters
        if topic := request.GET.get("topic"):
            data = [r for r in data if r["topic"] == topic]
        if status := request.GET.get("status"):
            data = [r for r in data if r["status"].lower() == status.lower()]

        return JsonResponse({
            "count":   len(data),
            "cached":  cached,
            "results": data,
        })

    except Exception as e:
        return JsonResponse({"error": str(e), "results": []}, status=500)


def solution_detail(request, solution_id):
    """
    GET /api/v1/solutions/<solution_id>/
    Reads from DB — no token required.
    """
    try:
        from .models import Solution
        sol = Solution.objects.select_related("topic").get(sdp_id=solution_id)
        return JsonResponse({
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
            "synced_at":   sol.synced_at.isoformat(),
        })
    except Exception as e:
        from django.http import Http404
        from .models import Solution
        try:
            Solution.objects.get(sdp_id=solution_id)
        except Solution.DoesNotExist:
            return JsonResponse({"error": "Solution not found"}, status=404)
        return JsonResponse({"error": str(e)}, status=500)


def topics_list(request):
    """
    GET /api/v1/topics/
    Flow: LocMemCache → DB
    """
    try:
        data, cached = get_cached_topics()

        if data is None:
            token = _get_token()
            from resources.solutions.sdp_solutions import SDPSolutions
            raw = SDPSolutions.get_topics(token)
            data = raw
            cached = False

        return JsonResponse({
            "count":   len(data),
            "cached":  cached,
            "results": data,
        })

    except Exception as e:
        return JsonResponse({"error": str(e), "results": []}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def cache_flush(request):
    """
    POST /api/v1/cache/flush/
    Invalidates both cache keys so next request re-reads from DB.
    """
    flush_cache()
    return JsonResponse({
        "flushed": ["sdp:solutions", "sdp:topics"],
        "message": "Cache cleared. Next request will read from DB.",
    })
