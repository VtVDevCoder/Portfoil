from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView  # noqa: E501
from rest_framework.routers import DefaultRouter
from .views import RegisterView, FeedbackBatchViewSet

router = DefaultRouter()
router.register(r'feedback-batches', FeedbackBatchViewSet,
                basename='feedback-batch')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # noqa: E501
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # noqa: E501

    path('', include(router.urls)),
]
