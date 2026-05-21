import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from reviews.models import AnalysisResult, FeedbackBatch, FeedbackItem


@pytest.mark.django_db
class TestDashboardStatsView:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='dashuser', password='pass123')
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated_returns_401(self):
        res = APIClient().get('/api/dashboard-stats/')
        assert res.status_code == 401

    def test_returns_expected_keys(self):
        res = self.client.get('/api/dashboard-stats/')
        assert res.status_code == 200
        for key in ('sentiment_distribution', 'top_categories', 'recent_items',
                    'total_batches', 'total_items'):
            assert key in res.data

    def test_empty_for_new_user(self):
        res = self.client.get('/api/dashboard-stats/')
        assert res.data['total_batches'] == 0
        assert res.data['total_items'] == 0

    def test_counts_only_own_data(self):
        other = User.objects.create_user(username='other', password='pass')
        other_batch = FeedbackBatch.objects.create(user=other)
        FeedbackItem.objects.create(
            batch=other_batch, raw_text='x', status='COMPLETED')

        batch = FeedbackBatch.objects.create(user=self.user)
        item = FeedbackItem.objects.create(
            batch=batch, raw_text='y', status='COMPLETED')
        AnalysisResult.objects.create(
            feedback_item=item, sentiment='POSITIVE',
            category='Bug', urgency_score=3, summary='ok'
        )

        res = self.client.get('/api/dashboard-stats/')
        assert res.data['total_batches'] == 1
        assert res.data['total_items'] == 1
        assert res.data['sentiment_distribution'][0]['sentiment'] == 'POSITIVE'
        assert res.data['sentiment_distribution'][0]['count'] == 1

    def test_top_categories_sorted_by_count(self):
        batch = FeedbackBatch.objects.create(user=self.user)
        for cat, n in [('Bug', 3), ('UI/UX', 1)]:
            for _ in range(n):
                item = FeedbackItem.objects.create(
                    batch=batch, raw_text='t', status='COMPLETED')
                AnalysisResult.objects.create(
                    feedback_item=item, sentiment='NEGATIVE',
                    category=cat, urgency_score=2, summary='s'
                )

        res = self.client.get('/api/dashboard-stats/')
        cats = [c['category'] for c in res.data['top_categories']]
        assert cats[0] == 'Bug'
