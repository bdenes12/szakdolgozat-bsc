from django.shortcuts import render, redirect, get_object_or_404
from pipelines.models import PipelineRun
from validations.models import ValidationRun, ValidationResult
from alerts.models import Alert

def pipeline_list_view(request):

    pipeline_queryset = PipelineRun.objects.all()

    context = {
        "pipeline_list": pipeline_queryset
    }

    return render(request, "pipelines/pipeline_list.html", context)

def pipeline_detail_view(request, my_id):

    pipeline = get_object_or_404(PipelineRun, id=my_id)
    validation_run = ValidationRun.objects.filter(pipeline_run=pipeline).order_by("-id").first()

    results = []
    alerts = []

    if validation_run:
        results = ValidationResult.objects.filter(validation_run=validation_run)
        alerts = Alert.objects.filter(validation_run=validation_run)
    
    context = {
        "pipeline": pipeline,
        "validation_run": validation_run,
        "validation_results": results,
        "alerts": alerts
    }
    return render(request, "pipelines/pipeline_detail.html", context)
