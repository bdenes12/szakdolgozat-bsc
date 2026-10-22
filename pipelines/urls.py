from django.urls import path

from pipelines.views import pipeline_detail_view, pipeline_list_view, pipeline_report

app_name = "pipelines"
urlpatterns = [
    path("<int:my_id>/", pipeline_detail_view, name="pipeline-detail"),
    path("", pipeline_list_view, name="pipeline-list"),
    path("<int:my_id>/report/", pipeline_report, name="pipeline-report"),
]
