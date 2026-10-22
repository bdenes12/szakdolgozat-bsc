from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from alerts.models import Alert


@login_required
def alert_list_view(request):
    alert_queryset = Alert.objects.filter(is_resolved=False)

    context = {"alert_list": alert_queryset}

    return render(request, "alerts/alert_list.html", context)


@login_required
def alert_resolve_view(request, my_id):
    if request.method == "POST":
        alert = get_object_or_404(Alert, id=my_id)
        alert.resolve()

    return redirect("alerts:alert-list")
