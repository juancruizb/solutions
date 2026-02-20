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
    Query params:
      ?topic=Internet       → filter by topic name
      ?status=Approved      → filter by approval status
    """
    try:
        token = _get_token()
        raw, cached = get_cached_solutions(token)

        results = [{
            "id":         s.get("id", ""),
            "display_id": s.get("display_id", {}).get("display_value", ""),
            "title":      s.get("title", "Sin título"),
            "description": s.get("description", ""),
            "topic":      s.get("topic", {}).get("name", ""),
            "status":     s.get("approval_status", {}).get("name", ""),
            "author":     s.get("created_by", {}).get("name", ""),
            "updated":    s.get("last_updated_time", {}).get("display_value", ""),
            "hits":       int(s.get("no_of_hits", 0) or 0),
            "keywords":   s.get("keywords", ""),
            "is_public":  s.get("is_public", False),
        } for s in raw]

        # Optional filters
        if topic := request.GET.get("topic"):
            results = [r for r in results if r["topic"] == topic]
        if status := request.GET.get("status"):
            results = [r for r in results if r["status"].lower() == status.lower()]

        return JsonResponse({
            "count":   len(results),
            "cached":  cached,
            "results": results,
        })

    except Exception as e:
        return JsonResponse({"error": str(e), "results": []}, status=500)


def solution_detail(request, solution_id):
    """
    GET /api/v1/solutions/<solution_id>/
    Returns raw detail from SDP (not normalised — full data available).
    """
    try:
        token = _get_token()
        from resources.solutions.sdp_solutions import SDPSolutions
        data = SDPSolutions.get_by_id(token, solution_id)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def topics_list(request):
    """
    GET /api/v1/topics/
    """
    try:
        token = _get_token()
        topics, cached = get_cached_topics(token)
        return JsonResponse({
            "count":   len(topics),
            "cached":  cached,
            "results": topics,
        })
    except Exception as e:
        return JsonResponse({"error": str(e), "results": []}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def cache_flush(request):
    """
    POST /api/v1/cache/flush/
    Manually invalidates cached solutions and topics.
    """
    flush_cache()
    return JsonResponse({
        "flushed": ["sdp:solutions", "sdp:topics"],
        "message": "Cache cleared. Next request will fetch fresh data from SDP Cloud.",
    })
