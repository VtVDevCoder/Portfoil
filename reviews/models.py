import uuid
from django.db import models
from django.contrib.auth.models import User


class FeedbackBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='batches')  # noqa: E501
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']


class FeedbackItem(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(FeedbackBatch, on_delete=models.CASCADE, related_name='items')  # noqa: E501
    raw_text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')  # noqa: E501
    created_at = models.DateTimeField(auto_now_add=True)


class AnalysisResult(models.Model):
    SENTIMENT_CHOICES = [
        ('POSITIVE', 'Positive'),
        ('NEGATIVE', 'Negative'),
        ('NEUTRAL', 'Neutral'),
    ]

    feedback_item = models.OneToOneField(
        FeedbackItem, on_delete=models.CASCADE, related_name='analysis')
    sentiment = models.CharField(max_length=10, choices=SENTIMENT_CHOICES)
    category = models.CharField(max_length=50, db_index=True)
    urgency_score = models.IntegerField(db_index=True)
    summary = models.TextField()
    processed_at = models.DateTimeField(auto_now_add=True)
