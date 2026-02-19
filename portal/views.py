import os
from django.shortcuts import render
from django.http import JsonResponse
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the kb/ root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def home(request):
    return render(request, 'portal/solutionsportal.html')


def historico(request):
    return render(request, 'portal/historico.html')


def api_solutions(request):
    """
    GET /api/solutions/
    Fetches all solutions from SDP Cloud and returns normalized JSON.
    No authentication required on this endpoint (public portal).
    """
    try:
        from resources.token.sdp_auth import SDPAuth
        from resources.solutions.sdp_solutions import SDPSolutions

        token = SDPAuth.get_access_token(
            client_id=os.getenv("SDP_CLIENT_ID"),
            client_secret=os.getenv("SDP_CLIENT_SECRET"),
        )

        raw_solutions = SDPSolutions.get_all_paginated(token)

        # Normalize fields for the frontend
        solutions = []
        for s in raw_solutions:
            solutions.append({
                "id":          s.get("id", ""),
                "display_id":  s.get("display_id", {}).get("display_value", ""),
                "title":       s.get("title", "Sin título"),
                "description": s.get("description", ""),
                "topic":       s.get("topic", {}).get("name", "General"),
                "status":      s.get("approval_status", {}).get("name", ""),
                "author":      s.get("created_by", {}).get("name", ""),
                "updated":     s.get("last_updated_time", {}).get("display_value", ""),
                "hits":        int(s.get("no_of_hits", 0) or 0),
                "keywords":    s.get("keywords", ""),
                "is_public":   s.get("is_public", False),
            })

        return JsonResponse({"solutions": solutions, "total": len(solutions)})

    except Exception as e:
        return JsonResponse({"error": str(e), "solutions": []}, status=500)


def api_topics(request):
    """
    GET /api/topics/
    Returns all unique topics derived from existing solutions,
    sorted alphabetically with a solution count per topic.
    """
    try:
        from resources.token.sdp_auth import SDPAuth
        from resources.solutions.sdp_solutions import SDPSolutions

        token = SDPAuth.get_access_token(
            client_id=os.getenv("SDP_CLIENT_ID"),
            client_secret=os.getenv("SDP_CLIENT_SECRET"),
        )

        topics = SDPSolutions.get_topics(token)
        return JsonResponse({"topics": topics, "total": len(topics)})

    except Exception as e:
        return JsonResponse({"error": str(e), "topics": []}, status=500)
