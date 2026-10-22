import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from alerts.models import Alert
from pipelines.models import PipelineRun
from validations.models import ValidationRun


def _create_user():
    return User.objects.create_superuser(username="admin", email="admin@test.com", password="admin123")


@pytest.mark.django_db
def _validation_run():
    pipeline = PipelineRun.objects.create(status=PipelineRun.RunStatuses.COMPLETED)

    return ValidationRun.objects.create(pipeline_run=pipeline, status=ValidationRun.ValidationRunStatuses.COMPLETED)


@pytest.mark.django_db
def _alert(vr, column_name):
    return Alert.objects.create(
        validation_run=vr,
        alert_type=Alert.AlertType.VALUE_OVERLAP,
        severity=Alert.SeverityType.CRITICAL,
        schema_name="public",
        table_name="invoices",
        column_name=column_name,
        message="overlap",
    )


@pytest.mark.django_db
def test_alert_list_redirects_when_anonymous(client):
    response = client.get(reverse("alerts:alert-list"))

    assert response.status_code == 302
    assert "/admin/login/" in response.url


@pytest.mark.django_db
def test_alert_list_ok_when_logged_in(client):
    vr = _validation_run()
    _alert(vr, "column")

    admin_user = _create_user()
    client.force_login(admin_user)
    response = client.get(reverse("alerts:alert-list"))

    assert response.status_code == 200
    assert response.context["alert_list"].count() == 1
    assert "alert_list" in response.context


@pytest.mark.django_db
def test_alert_resolve_post_marks_resolved(client):
    vr = _validation_run()
    alert = _alert(vr, "column")

    admin_user = _create_user()
    client.force_login(admin_user)

    response = client.post(reverse("alerts:alert-resolve", args=[alert.id]))

    alert.refresh_from_db()

    assert alert.is_resolved == True
    assert alert.resolved_at is not None
    assert response.status_code == 302
    assert response.url == reverse("alerts:alert-list")


@pytest.mark.django_db
def test_alert_resolve_get_does_not_resolve(client):
    vr = _validation_run()
    alert = _alert(vr, "column")

    admin_user = _create_user()
    client.force_login(admin_user)

    response = client.get(reverse("alerts:alert-resolve", args=[alert.id]))

    alert.refresh_from_db()

    assert alert.is_resolved == False
    assert alert.resolved_at is None
    assert response.status_code == 302
