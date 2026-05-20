import pytest
from unittest.mock import patch
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from reviews.models import FeedbackBatch, FeedbackItem, AnalysisResult


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    user = User.objects.create_user(
        username="testuser", password="password123")
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db(transaction=True)  # ← real commits so on_commit fires
@patch('reviews.tasks.AIService.analyze_feedback')
def test_create_feedback_batch_api_and_celery_integration(mock_analyze, authenticated_client):  # noqa: E501
    mock_analyze.return_value = {
        "sentiment": "POSITIVE",
        "category": "UI/UX",
        "urgency_score": 1,
        "summary": "Great dark mode feature"
    }

    url = reverse('feedback-batch-list')
    data = {
        "raw_text_list": [
            "Adorei o novo modo escuro do sistema!",
            "O app fecha na tela de carregamento."
        ]
    }

    response = authenticated_client.post(url, data, format='json')

    # 1. Endpoint response
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert "batch_id" in response.data

    # 2. Batch in DB
    batch_id = response.data["batch_id"]
    batch = FeedbackBatch.objects.get(id=batch_id)
    batch.refresh_from_db()
    assert batch.is_processed is True

    # 3. Items processed
    items = FeedbackItem.objects.filter(batch=batch)
    assert items.count() == 2
    for item in items:
        item.refresh_from_db()
        assert item.status == 'COMPLETED'

    # 4. AI results saved
    assert AnalysisResult.objects.filter(
        feedback_item__batch=batch).count() == 2

    first_analysis = AnalysisResult.objects.filter(
        feedback_item__batch=batch).first()
    assert first_analysis is not None  # narrows type for type checkers
    assert first_analysis.sentiment == "POSITIVE"
    assert first_analysis.category == "UI/UX"
    assert first_analysis.urgency_score == 1
    assert mock_analyze.call_count == 2


@pytest.mark.django_db
def test_create_feedback_batch_unauthenticated(api_client):
    url = reverse('feedback-batch-list')
    data = {"raw_text_list": ["Texto"]}
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
