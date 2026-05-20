import pytest
from unittest.mock import MagicMock, patch
from reviews.services import AIService


@pytest.fixture
def mock_gemini_response():
    mock_response = MagicMock()
    mock_response.text = '{"sentiment": "NEGATIVE", "category": "Bug", "urgency_score": 5, "summary": "App crashes on login"}'  # noqa: E501
    return mock_response


@patch('reviews.services.genai.Client')
def test_analyze_feedback_with_gemini_mock(mock_client_class, mock_gemini_response):  # noqa: E501
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_gemini_response
    mock_client_class.return_value = mock_client

    with patch('django.conf.settings.GEMINI_API_KEY', 'valid_mock_key'):
        service = AIService()
        result = service.analyze_feedback(
            "O aplicativo fecha sozinho toda vez que tento logar.")

        assert result["sentiment"] == "NEGATIVE"
        assert result["category"] == "Bug"
        assert result["urgency_score"] == 5
        assert result["summary"] == "App crashes on login"
        mock_client.models.generate_content.assert_called_once()


def test_analyze_feedback_when_api_key_not_configured():
    with patch('django.conf.settings.GEMINI_API_KEY', 'your-key-here'):
        service = AIService()
        result = service.analyze_feedback("Qualquer texto")

        assert result["sentiment"] == "NEUTRAL"
        assert result["category"] == "Uncategorized"
        assert result["urgency_score"] == 3
        assert "not configured" in result["summary"]
