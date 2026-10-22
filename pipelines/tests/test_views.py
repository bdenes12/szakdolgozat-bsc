import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from pipelines.models import PipelineRun
from validations.models import ValidationReport, ValidationRun


def _create_user():
    return User.objects.create_superuser(username="admin", email="admin@test.com", password="admin123")


@pytest.mark.django_db
def _pipeline():
    return PipelineRun.objects.create(status=PipelineRun.RunStatuses.COMPLETED)


@pytest.mark.django_db
def test_pipeline_list_redirects_when_anonymous(client):
    response = client.get(reverse("pipelines:pipeline-list"))

    assert response.status_code == 302
    assert "/admin/login/" in response.url


@pytest.mark.django_db
def test_pipeline_list_ok_when_logged_in(client):
    admin_user = _create_user()
    client.force_login(admin_user)
    response = client.get(reverse("pipelines:pipeline-list"))

    assert response.status_code == 200
    assert "pipeline_list" in response.context


@pytest.mark.django_db
def test_pipeline_detail_unknown_id_returns_404(client):
    admin_user = _create_user()
    client.force_login(admin_user)

    response = client.get(reverse("pipelines:pipeline-detail", args=[99999]))

    assert 404 == response.status_code


@pytest.mark.django_db
def test_pipeline_detail_known_id_returns_200(client):
    admin_user = _create_user()
    client.force_login(admin_user)

    pipeline = _pipeline()

    response = client.get(reverse("pipelines:pipeline-detail", args=[pipeline.id]))

    assert 200 == response.status_code


@pytest.mark.django_db
def test_pipeline_report_without_report_returns_404(client):
    admin_user = _create_user()
    client.force_login(admin_user)

    pipeline = _pipeline()

    response = client.get(reverse("pipelines:pipeline-report", args=[pipeline.id]))

    assert 404 == response.status_code


@pytest.mark.django_db
def test_pipeline_report_returns_stored_html(client):
    admin_user = _create_user()
    client.force_login(admin_user)

    pipeline = _pipeline()
    vr = ValidationRun.objects.create(pipeline_run=pipeline, status=ValidationRun.ValidationRunStatuses.COMPLETED)
    ValidationReport.objects.create(validation_run=vr, html_content="<p>teszt-riport</p>")

    response = client.get(reverse("pipelines:pipeline-report", args=[pipeline.id]))

    assert response.status_code == 200
    assert b"teszt-riport" in response.content
