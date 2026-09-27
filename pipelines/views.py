from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from pipelines.models import PipelineRun
from pipelines.services import PipelineService
from validations.models import ValidationRun, ValidationResult
from alerts.models import Alert

@login_required
def pipeline_list_view(request):

    unresolved_alerts = Alert.objects.filter(is_resolved=False).count()

    last_validation_run = ValidationRun.objects.order_by('-id').first()
    pass_validation_status_count = ValidationResult.objects.filter(status=ValidationResult.ValidationResultStatuses.PASS, validation_run=last_validation_run).count()
    fail_validation_status_count = ValidationResult.objects.filter(status=ValidationResult.ValidationResultStatuses.FAIL, validation_run=last_validation_run).count()

    if request.method == "POST":
        pipeline_obj = PipelineService().start_pipeline()

        return redirect(pipeline_obj.get_absolute_url())

    pipeline_queryset = PipelineRun.objects.all().order_by("-id")

    context = {
        "unresolved_alerts": unresolved_alerts,
        "pass_validation_status_count": pass_validation_status_count,
        "fail_validation_status_count": fail_validation_status_count,
        "pipeline_list": pipeline_queryset
    }

    return render(request, "pipelines/pipeline_list.html", context)

@login_required
def pipeline_detail_view(request, my_id):

    pipeline = get_object_or_404(PipelineRun, id=my_id)
    validation_run = ValidationRun.objects.filter(pipeline_run=pipeline).order_by("-id").first()

    results = []
    alerts = []

    not_resolved_alerts = Alert.objects.filter(validation_run=validation_run, is_resolved=False).count()

    if validation_run:
        results = ValidationResult.objects.filter(validation_run=validation_run)
        alerts = Alert.objects.filter(validation_run=validation_run, severity__in=[Alert.SeverityType.CRITICAL, Alert.SeverityType.WARNING])
    
    context = {
        "pipeline": pipeline,
        "validation_run": validation_run,
        "validation_results": results,
        "alerts": alerts,
        "not_resolved_alerts": not_resolved_alerts
    }
    return render(request, "pipelines/pipeline_detail.html", context)
