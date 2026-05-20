from celery import shared_task
from .models import FeedbackItem, AnalysisResult
from .services import AIService


@shared_task
def process_feedback_batch_task(batch_id):
    # Busca os itens pendentes do lote
    items = FeedbackItem.objects.filter(batch_id=batch_id, status='PENDING')
    if not items.exists():
        return f"Batch {batch_id}: No pending items to process."

    # Atualiza o status para processando para evitar duplicidade
    items.update(status='PROCESSING')
    ai_service = AIService()

    for item in items:
        try:
            # Chama o serviço de IA real (Gemini)
            analysis_data = ai_service.analyze_feedback(item.raw_text)

            # Salva o resultado no banco de dados
            AnalysisResult.objects.create(
                feedback_item=item,
                sentiment=analysis_data['sentiment'],
                category=analysis_data['category'],
                urgency_score=analysis_data['urgency_score'],
                summary=analysis_data['summary']
            )
            item.status = 'COMPLETED'
        except Exception:
            item.status = 'FAILED'
        finally:
            item.save()

    # Atualiza o lote principal como processado
    from .models import FeedbackBatch
    FeedbackBatch.objects.filter(id=batch_id).update(is_processed=True)

    return f"Batch {batch_id} processed successfully."
