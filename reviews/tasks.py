from celery import shared_task
from .models import FeedbackBatch, FeedbackItem, AnalysisResult
from .services import AIService


@shared_task
def process_feedback_batch_task(batch_id):
    # Evaluate queryset immediately before update
    items = list(FeedbackItem.objects.filter(
        batch_id=batch_id, status='PENDING'))

    if not items:
        return f"Batch {batch_id}: No pending items to process."

    ids = [item.id for item in items]
    FeedbackItem.objects.filter(id__in=ids).update(status='PROCESSING')

    ai_service = AIService()

    for item in items:
        item.status = 'PROCESSING'
        try:
            analysis_data = ai_service.analyze_feedback(item.raw_text)
            AnalysisResult.objects.create(
                feedback_item=item,
                sentiment=analysis_data['sentiment'],
                category=analysis_data['category'],
                urgency_score=analysis_data['urgency_score'],
                summary=analysis_data['summary'],
            )
            item.status = 'COMPLETED'
        except Exception:
            item.status = 'FAILED'
        finally:
            item.save()

    FeedbackBatch.objects.filter(id=batch_id).update(is_processed=True)
    return f"Batch {batch_id} processed successfully."
