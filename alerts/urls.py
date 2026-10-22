from django.urls import path

from alerts.views import alert_list_view, alert_resolve_view

app_name = "alerts"
urlpatterns = [
    path("<int:my_id>/resolve/", alert_resolve_view, name="alert-resolve"),
    path("", alert_list_view, name="alert-list"),
]
