import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_user_registration_success(api_client):
    url = reverse('auth_register')
    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "securepassword123"
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="newuser").exists()

    assert response.data["username"] == "newuser"
    assert response.data["email"] == "newuser@example.com"


@pytest.mark.django_db
def test_user_registration_invalid_data(api_client):
    url = reverse('auth_register')
    # Enviando dados sem senha para forçar erro no serializer
    data = {
        "username": "invaliduser",
        "email": "not-an-email"
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


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


@pytest.mark.django_db
def test_token_refresh_endpoint(api_client):
    User.objects.create_user(username="refreshuser", password="password123")

    # Faz login para pegar o refresh token
    login_url = reverse('token_obtain_pair')
    login_res = api_client.post(
        login_url, {"username": "refreshuser", "password": "password123"}, format='json')  # noqa: E501
    refresh_token = login_res.data['refresh']

    # Testando a rota de refresh
    url = reverse('token_refresh')
    response = api_client.post(url, {"refresh": refresh_token}, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert 'access' in response.data
