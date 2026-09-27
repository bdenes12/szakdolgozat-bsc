from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from alerts.models import Alert

def alert_list_view(request):
    alert_queryset = Alert.objects.filter(is_resolved=False)

    context = {
        "alert_list": alert_queryset
    }

    return render(request, "alerts/alert_list.html", context)

def alert_resolve_view(request, my_id):
    
    if request.method == "POST":
        
        alert = get_object_or_404(Alert, id=my_id)
        alert.resolve()

    return redirect('alerts:alert-list')

