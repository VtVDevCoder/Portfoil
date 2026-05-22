from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, QuerySet
from rest_framework import generics, status, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AnalysisResult, FeedbackBatch, FeedbackItem
from .parsers import parse_uploaded_file
from .serializers import FeedbackBatchSerializer, FeedbackItemSerializer, RegisterSerializer  # noqa: E501
from .tasks import process_feedback_batch_task


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class FeedbackBatchViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackBatchSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self) -> QuerySet[FeedbackBatch]:
        return FeedbackBatch.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        raw_text_list = []

        # --- Caso 1: upload de arquivo (.txt, .csv, .json) ---
        if "file" in request.FILES:
            try:
                raw_text_list = parse_uploaded_file(request.FILES["file"])
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)  # noqa: E501

        # --- Caso 2: JSON body (comportamento original) ---
        elif "raw_text_list" in request.data:
            raw_text_list = request.data["raw_text_list"]
            if not isinstance(raw_text_list, list):
                return Response(
                    {"error": "raw_text_list deve ser uma lista de strings."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        else:
            return Response(
                {"error": "Envie um arquivo (file) ou raw_text_list no corpo da requisição."},  # noqa: E501
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_text_list = [t.strip() for t in raw_text_list if str(t).strip()]
        if not raw_text_list:
            return Response(
                {"error": "Nenhum texto encontrado. Verifique o conteúdo enviado."},  # noqa: E501
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data={"raw_text_list": raw_text_list})
        serializer.is_valid(raise_exception=True)
        batch = serializer.save()

        transaction.on_commit(
            lambda: process_feedback_batch_task.delay(str(batch.id))
        )

        return Response(
            {
                "message": "Feedback batch accepted and processing in background.",  # noqa: E501
                "batch_id": str(batch.id),
                "total_items": len(raw_text_list),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_batches = FeedbackBatch.objects.filter(user=request.user)
        items = FeedbackItem.objects.filter(batch__in=user_batches)
        completed_items = items.filter(status="COMPLETED")

        sentiment_data = (
            AnalysisResult.objects
            .filter(feedback_item__in=completed_items)
            .values("sentiment")
            .annotate(count=Count("sentiment"))
        )

        category_data = (
            AnalysisResult.objects
            .filter(feedback_item__in=completed_items)
            .values("category")
            .annotate(count=Count("category"))
            .order_by("-count")[:10]
        )

        recent_items = (
            completed_items
            .select_related("analysis")
            .order_by("-created_at")[:20]
        )

        return Response({
            "sentiment_distribution": list(sentiment_data),
            "top_categories": list(category_data),
            "recent_items": FeedbackItemSerializer(recent_items, many=True).data,   # noqa: E501
            "total_batches": user_batches.count(),
            "total_items": items.count(),
        })
