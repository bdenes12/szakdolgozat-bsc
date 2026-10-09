from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from pipelines.models import PipelineRun
from pipelines.services import PipelineService
from validations.models import ValidationRun, ValidationResult, ValidationReport
from alerts.models import Alert

@login_required
def pipeline_list_view(request):

    if request.method == "POST":
        pipeline_obj = PipelineService().start_pipeline()

        return redirect(pipeline_obj.get_absolute_url())

    unresolved_alerts = Alert.objects.filter(is_resolved=False).count()

    last_validation_run = ValidationRun.objects.order_by('-id').first()
    
    pass_validation_status_count = ValidationResult.objects.filter(status=ValidationResult.ValidationResultStatuses.PASS, validation_run=last_validation_run).count()
    warning_validation_status_count = ValidationResult.objects.filter(status=ValidationResult.ValidationResultStatuses.WARNING, validation_run=last_validation_run).count()
    fail_validation_status_count = ValidationResult.objects.filter(status=ValidationResult.ValidationResultStatuses.FAIL, validation_run=last_validation_run).count()

    total = pass_validation_status_count + warning_validation_status_count + fail_validation_status_count

    if total != 0:
        pass_pct = round(pass_validation_status_count / total * 100, 2)
        warning_pct = round(warning_validation_status_count / total * 100, 2)
        fail_pct = round(fail_validation_status_count / total * 100, 2)
    else:
        pass_pct = warning_pct = fail_pct = 0

    pipeline_queryset = list(PipelineRun.objects.all().order_by("-id")[:10])

    alert_severity_info = Alert.objects.filter(is_resolved=False, severity=Alert.SeverityType.INFO).count()
    alert_severity_warning = Alert.objects.filter(is_resolved=False, severity=Alert.SeverityType.WARNING).count()
    alert_severity_critical = Alert.objects.filter(is_resolved=False, severity=Alert.SeverityType.CRITICAL).count()

    context = {
        "last_validation_run": last_validation_run,
        "unresolved_alerts": unresolved_alerts,
        "pass_validation_status_count": pass_validation_status_count,
        "warning_validation_status_count": warning_validation_status_count,
        "fail_validation_status_count": fail_validation_status_count,
        "total": total,
        "pass_pct": pass_pct,
        "warning_pct": warning_pct,
        "fail_pct": fail_pct,
        "pipeline_list": pipeline_queryset,
        "alert_severity_info": alert_severity_info,
        "alert_severity_warning": alert_severity_warning,
        "alert_severity_critical": alert_severity_critical
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

@login_required
def pipeline_report(request, my_id):
    
    pipeline = get_object_or_404(PipelineRun, id=my_id)
    validation_run = ValidationRun.objects.filter(pipeline_run=pipeline).order_by("-id").first()
    report = ValidationReport.objects.filter(validation_run=validation_run).order_by("-id").first()

    if validation_run is None or report is None:
        raise Http404("Nincs validációs riport ehhez a futáshoz.")

    return HttpResponse(report.html_content)