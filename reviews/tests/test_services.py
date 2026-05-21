import pytest
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from reviews.models import AnalysisResult, FeedbackBatch, FeedbackItem
from reviews.services import AIService
from reviews.tasks import process_feedback_batch_task


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    user = User.objects.create_user(
        username="testuser", password="password123")
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
def test_create_feedback_batch_unauthenticated(api_client):
    url = reverse('feedback-batch-list')
    response = api_client.post(
        url, {"raw_text_list": ["Texto"]}, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@patch('reviews.tasks.AIService.analyze_feedback')
def test_create_feedback_batch_api_and_celery_integration(mock_analyze, authenticated_client):  # noqa: E501
    mock_analyze.return_value = {
        "sentiment": "POSITIVE",
        "category": "UI/UX",
        "urgency_score": 1,
        "summary": "Great dark mode feature",
    }

    url = reverse('feedback-batch-list')
    data = {
        "raw_text_list": [
            "Adorei o novo modo escuro do sistema!",
            "O app fecha na tela de carregamento.",
        ]
    }

    response = authenticated_client.post(url, data, format='json')

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert "batch_id" in response.data

    batch_id = response.data["batch_id"]

    # on_commit never fires in test (no real DB commit) — call task directly
    process_feedback_batch_task(batch_id)

    batch = FeedbackBatch.objects.get(id=batch_id)
    assert batch.is_processed is True

    items = FeedbackItem.objects.filter(batch=batch)
    assert items.count() == 2
    for item in items:
        item.refresh_from_db()
        assert item.status == 'COMPLETED'

    assert AnalysisResult.objects.filter(
        feedback_item__batch=batch).count() == 2
    first_analysis = AnalysisResult.objects.filter(
        feedback_item__batch=batch).first()
    assert first_analysis is not None
    assert first_analysis.sentiment == "POSITIVE"
    assert first_analysis.category == "UI/UX"
    assert first_analysis.urgency_score == 1
    assert mock_analyze.call_count == 2


@pytest.mark.django_db
def test_feedback_batch_list_returns_own_batches(authenticated_client):
    """Covers FeedbackBatchViewSet.get_queryset (views.py line 30)"""
    url = reverse('feedback-batch-list')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)


@pytest.mark.django_db
def test_task_skips_when_no_pending_items():
    """Covers tasks.py early-return branch (line 11)"""
    user = User.objects.create_user(username="taskuser2", password="pass")
    batch = FeedbackBatch.objects.create(user=user)
    result = process_feedback_batch_task(str(batch.id))
    assert "No pending items" in result


@pytest.mark.django_db
@patch('reviews.tasks.AIService.analyze_feedback')
def test_task_marks_item_failed_on_exception(mock_analyze):
    """Covers tasks.py exception path"""
    mock_analyze.side_effect = Exception("AI error")
    user = User.objects.create_user(username="failuser", password="pass")
    batch = FeedbackBatch.objects.create(user=user)
    FeedbackItem.objects.create(batch=batch, raw_text="test", status='PENDING')

    process_feedback_batch_task(str(batch.id))

    item = FeedbackItem.objects.get(batch=batch)
    assert item.status == 'FAILED'


def test_ai_service_fallback_when_unconfigured():
    """Covers AIService no-client path"""
    service = AIService()
    service.client = None
    result = service.analyze_feedback("any text")
    assert result['sentiment'] == 'NEUTRAL'
    assert result['category'] == 'Uncategorized'


def test_ai_service_analyze_with_valid_response():
    """Covers AIService actual API call path (services.py lines 29-54)"""
    service = AIService()
    mock_response = MagicMock()
    mock_response.text = (
        '{"sentiment": "POSITIVE", "category": "Bug",'
        ' "urgency_score": 3, "summary": "Works great"}'
    )
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    service.client = mock_client

    result = service.analyze_feedback("The app works great!")

    assert result['sentiment'] == 'POSITIVE'
    assert result['category'] == 'Bug'
    assert result['urgency_score'] == 3
    mock_client.models.generate_content.assert_called_once()


def test_ai_service_raises_on_empty_response():
    """Covers AIService ValueError raise path"""
    service = AIService()
    mock_response = MagicMock()
    mock_response.text = None
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    service.client = mock_client

    with pytest.raises(ValueError, match="Empty response from Gemini"):
        service.analyze_feedback("some text")
