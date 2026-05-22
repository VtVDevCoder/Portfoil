import pytest  # noqa: F401
from django.urls import resolve, reverse  # noqa: F401


def test_core_url_resolves_auth_endpoints():
    resolver = resolve('/api/auth/register/')
    assert resolver.view_name == 'auth_register'
