from rest_framework import viewsets, status
from .tasks import process_feedback_batch_task
from .serializers import FeedbackBatchSerializer
from .models import FeedbackBatch
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer
from django.db.models import QuerySet
from django.db import transaction


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class FeedbackBatchViewSet(viewsets.ModelViewSet):
    queryset = FeedbackBatch.objects.all().order_by('-created_at')
    serializer_class = FeedbackBatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[FeedbackBatch]:
        # Garante que um usuário veja apenas os seus próprios lotes de feedback
        return FeedbackBatch.objects.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Salva o lote e os itens no banco de dados (Status: PENDING)
        batch = serializer.save()

        # DISPARO ASSÍNCRONO: Envia para a fila do Celery e libera o HTTP imediatamente  # noqa: E501
        transaction.on_commit(
            # type: ignore
            lambda: process_feedback_batch_task.delay(batch.id))

        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Feedback batch accepted and processing in background.",  # noqa: E501
                "batch_id": batch.id},
            status=status.HTTP_202_ACCEPTED,
            headers=headers
        )
