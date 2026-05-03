from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def healthcheck(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()

    return JsonResponse(
        {
            "status": "ok",
            "debug": settings.DEBUG,
            "database": "ok",
            "app": "ssc-education",
        }
    )
