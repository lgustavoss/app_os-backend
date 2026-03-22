"""
Endpoints leves para load balancer / orquestrador (sem autenticação).
"""
from django.db import connection
from django.http import JsonResponse
from django.views import View


class HealthLiveView(View):
    """Liveness: processo a responder (não verifica BD)."""

    http_method_names = ['get', 'head', 'options']

    def get(self, request):
        return JsonResponse({'status': 'ok'})


class HealthReadyView(View):
    """Readiness: verifica conexão com a base de dados."""

    http_method_names = ['get', 'head', 'options']

    def get(self, request):
        try:
            connection.ensure_connection()
        except Exception:
            return JsonResponse(
                {'status': 'unavailable', 'detail': 'database'},
                status=503,
            )
        return JsonResponse({'status': 'ok'})
