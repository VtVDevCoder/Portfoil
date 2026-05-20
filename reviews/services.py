import json
from django.conf import settings
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Literal

# Define o esquema estrito de resposta que a IA DEVE seguir


class FeedbackAnalysisSchema(BaseModel):
    sentiment: Literal["POSITIVE", "NEGATIVE", "NEUTRAL"]
    category: str = Field(
        description="The functional category of the feedback (e.g., Bug, UI/UX, Feature Request, Support)")  # noqa: E501
    urgency_score: int = Field(
        ge=1, le=5, description="Urgency score from 1 (low) to 5 (critical)")
    summary: str = Field(
        description="A brief 1-sentence summary of the user feedback")


class AIService:
    def __init__(self):
        # Inicializa o cliente se a chave estiver configurada
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.client = genai.Client(
            api_key=api_key) if api_key and api_key != "your-key-here" else None  # noqa: E501

    def analyze_feedback(self, text: str) -> dict:
        if not self.client:
            return {
                "sentiment": "NEUTRAL",
                "category": "Uncategorized",
                "urgency_score": 3,
                "summary": "AI service not configured."
            }

        # Configura a requisição para forçar o output estruturado via Pydantic
        config = types.GenerateContentConfig(
            system_instruction="You are an expert customer feedback analyzer. Analyze the text and extract sentiment, category, urgency, and a brief summary.",  # noqa: E501
            response_mime_type="application/json",
            response_schema=FeedbackAnalysisSchema,
            temperature=0.1
        )

        response = self.client.models.generate_content(
            model='gemini-1.5-flash',
            contents=text,
            config=config
        )

        if response.text is None:
            raise ValueError('Empty response from Gemini')

        return json.loads(response.text)
