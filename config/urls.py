from django.contrib import admin
from django.urls import include, path

from pipelines.views import help_view

admin.site.site_url = "/pipelines/"
admin.site.site_header = "Anonimizáció admin"
admin.site.index_title = "Modellek"

urlpatterns = [
    path("pipelines/", include("pipelines.urls")),
    path("alerts/", include("alerts.urls")),
    path("help/", help_view, name="help"),
    path("admin/", admin.site.urls),
]
