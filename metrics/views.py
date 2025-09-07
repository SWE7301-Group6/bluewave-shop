from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from api_integration.utils import fetch_metrics

@login_required
def dashboard(request):
    # Default: last 7 days
    end = timezone.now()
    start = end - timedelta(days=7)
    return render(request, "metrics/dashboard.html", {"start": start.isoformat(), "end": end.isoformat()})

@login_required
def metrics_proxy(request):
    start = request.GET.get("start")
    end = request.GET.get("end")
    if not (start and end):
        return JsonResponse({"error": "start and end required"}, status=400)
    data, error = fetch_metrics(start, end)
    if error:
        return JsonResponse({"error": error}, status=502)
    return JsonResponse(data, safe=False)
