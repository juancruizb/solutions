import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# Base URL from .env  e.g: https://sdpondemand.manageengine.com/app/itdesk
SDP_BASE_URL = os.getenv("SDP_BASE_URL", "https://sdpondemand.manageengine.com/app/itdesk")


class SDPSolutions:
    """
    Static methods for interacting with the SDP Cloud Solutions module.
    All methods require a valid access_token (use SDPAuth.get_access_token()).

    Pagination note:
      - start_index: 0  → first batch
      - start_index: 100 → next 100, and so on
    """

    @staticmethod
    def _headers(access_token: str) -> dict:
        """Standard headers for SDP Cloud API calls."""
        return {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Accept": "application/vnd.manageengine.sdp.v3+json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    @staticmethod
    def get_all(access_token: str, start_index: int = 0, row_count: int = 1000) -> dict:
        """
        GET a batch of solutions from SDP Cloud.
        - start_index: offset (0 = first batch, 1000 = next batch, etc.)
        - row_count: max results per call (SDP max is typically 1000)
        Returns the full API response dict with 'solutions' and 'list_info'.
        """
        url = f"{SDP_BASE_URL}/api/v3/solutions"

        list_info = {
            "row_count": str(row_count),
            "start_index": str(start_index),
            "sort_field": "created_time",
            "sort_order": "desc",
        }

        params = {"input_data": json.dumps({"list_info": list_info})}

        response = requests.get(
            url,
            headers=SDPSolutions._headers(access_token),
            params=params,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_all_paginated(access_token: str, row_count: int = 1000) -> list:
        """
        Fetches ALL solutions by paginating automatically.
        Returns a flat list of all solution dicts.
        """
        all_solutions = []
        start_index = 0

        while True:
            data = SDPSolutions.get_all(access_token, start_index=start_index, row_count=row_count)
            batch = data.get("solutions", [])
            all_solutions.extend(batch)

            # Stop if we got fewer results than requested (last page)
            if len(batch) < row_count:
                break

            start_index += row_count

        return all_solutions

    @staticmethod
    def get_by_id(access_token: str, solution_id: str) -> dict:
        """
        GET a single solution by its ID.
        Returns the solution detail dict.
        """
        url = f"{SDP_BASE_URL}/api/v3/solutions/{solution_id}"
        response = requests.get(url, headers=SDPSolutions._headers(access_token))
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_topics(access_token: str) -> list:
        """
        Derives unique topics from all solutions.
        Returns a sorted list of dicts:
          [{"id": "...", "name": "...", "icon_key": "...", "count": N}, ...]
        """
        all_solutions = SDPSolutions.get_all_paginated(access_token)

        seen = {}  # topic_id -> dict
        for s in all_solutions:
            topic = s.get("topic", {})
            if not topic:
                continue
            tid = topic.get("id", "")
            if tid not in seen:
                seen[tid] = {
                    "id":       tid,
                    "name":     topic.get("name", "General"),
                    "icon_key": topic.get("icon_key", ""),
                    "count":    0,
                }
            seen[tid]["count"] += 1

        return sorted(seen.values(), key=lambda t: t["name"])

