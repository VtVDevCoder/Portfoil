import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_user_registration(api_client):
    url = reverse('auth_register')
    data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "securepassword123"
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="testuser").exists()


@pytest.mark.django_db
def test_user_login_returns_jwt_tokens(api_client):
    User.objects.create_user(
        username="loginuser", email="loginuser@example.com", password="password123")  # noqa: E501

    url = reverse('token_obtain_pair')
    data = {
        "username": "loginuser",
        "password": "password123"
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert 'access' in response.data
    assert 'refresh' in response.data
