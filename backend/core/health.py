from django.db import connection
from django.http import JsonResponse


def health_check(request):
    try:
        connection.ensure_connection()
        return JsonResponse({
            "status": "healthy",
            "database": "connected",
        })
    except Exception:
        return JsonResponse({
            "status": "unhealthy",
            "database": "unavailable",
        }, status=503)
