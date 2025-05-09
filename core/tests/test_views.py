import os
from urllib.parse import urlencode

import pytest
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.messages import get_messages
from django.http import HttpResponse
from django.test import Client, override_settings
from django.urls import reverse

from access_tokens.models import AccessToken


@pytest.mark.django_db
def test_homepage():
    client = Client()
    response: HttpResponse = client.get(reverse("core:home"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_dashboard_is_only_accessible_when_logged_in(sample_user: AbstractBaseUser):  # noqa: F811
    client = Client()
    response: HttpResponse = client.get(reverse("core:dashboard"))
    assert response.status_code == 302

    assert client.login(username=os.environ["DJANGO_TEST_USER"], password=os.environ["DJANGO_TEST_PASSWORD"])
    response: HttpResponse = client.get(reverse("core:dashboard"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_access_token_creation(sample_user: AbstractBaseUser):  # noqa: F811
    client = Client()
    assert client.login(username=os.environ["DJANGO_TEST_USER"], password=os.environ["DJANGO_TEST_PASSWORD"])

    uri = reverse("core:settings")
    form_data = urlencode({"description": "Test Token"})
    response = client.post(uri, form_data, content_type="application/x-www-form-urlencoded")
    assert response.status_code == 200
    messages = list(get_messages(response.wsgi_request))
    assert any(m.message == "New access token created" for m in messages)
    access_tokens = AccessToken.objects.filter(user=sample_user).all()
    assert len(access_tokens) == 1


@pytest.mark.django_db
def test_logout_redirect(sample_user: AbstractBaseUser):
    client = Client()
    assert client.login(username=os.environ["DJANGO_TEST_USER"], password=os.environ["DJANGO_TEST_PASSWORD"])

    with override_settings(
        KEYCLOAK_SERVER_URL="https://test-domain.com",
        KEYCLOAK_CLIENT_ID="test-client-id",
        KEYCLOAK_END_SESSION_ENDPOINT="https://test-domain.com/realms/sbomify/protocol/openid-connect/logout",
        APP_BASE_URL="http://test-return.url",
        USE_KEYCLOAK=True,
    ):
        response: HttpResponse = client.get(reverse("core:logout"))
        assert response.status_code == 302
        assert response.url.startswith("https://test-domain.com/realms/sbomify/protocol/openid-connect/logout")
        assert "client_id=test-client-id" in response.url
        assert "post_logout_redirect_uri=http://test-return.url" in response.url


@pytest.mark.django_db
def test_logout_view_with_keycloak(client: Client, sample_user: AbstractBaseUser):
    """Test that logout view works correctly with Keycloak enabled."""
    client.force_login(sample_user)
    with override_settings(
        KEYCLOAK_SERVER_URL="https://test-domain.com",
        KEYCLOAK_CLIENT_ID="test-client-id",
        KEYCLOAK_REALM="sbomify",
        USE_KEYCLOAK=True,
        APP_BASE_URL="http://test-return.url",
    ):
        response = client.get(reverse("core:logout"))
        assert response.status_code == 302
        assert response.url.startswith("https://test-domain.com/realms/sbomify/protocol/openid-connect/logout")
        assert "client_id=test-client-id" in response.url
        assert "post_logout_redirect_uri=http://test-return.url" in response.url


@pytest.mark.django_db
def test_logout_view_without_keycloak(client: Client, sample_user: AbstractBaseUser):
    """Test that logout view works correctly with Keycloak disabled."""
    client.force_login(sample_user)
    with override_settings(USE_KEYCLOAK=False):
        response = client.get(reverse("core:logout"))
        assert response.status_code == 302
        assert response.url == reverse("core:home")


@pytest.mark.django_db
def test_delete_nonexistent_access_token(sample_user: AbstractBaseUser):
    client = Client()
    assert client.login(username=os.environ["DJANGO_TEST_USER"], password=os.environ["DJANGO_TEST_PASSWORD"])

    response = client.post(reverse("core:delete_access_token", kwargs={"token_id": 999}))
    assert response.status_code == 404
    # No message is actually added in the view for this case, just the 404 response


@pytest.mark.django_db
def test_delete_another_users_token(guest_user: AbstractBaseUser, sample_user: AbstractBaseUser):
    # Create token with guest user
    client = Client()
    assert client.login(username="guest", password="guest")

    # Properly format form data and set content type
    form_data = urlencode({"description": "Guest Token"})
    response = client.post(
        reverse("core:settings"),
        form_data,
        content_type="application/x-www-form-urlencoded"
    )

    # Verify successful token creation
    assert response.status_code == 200
    messages = list(get_messages(response.wsgi_request))
    assert any(m.message == "New access token created" for m in messages)

    guest_token = AccessToken.objects.filter(user=guest_user).first()
    assert guest_token is not None, "Token should have been created for guest user"

    # Switch to sample user and try to delete
    client.logout()
    assert client.login(
        username=os.environ["DJANGO_TEST_USER"],
        password=os.environ["DJANGO_TEST_PASSWORD"]
    )

    response = client.post(reverse("core:delete_access_token", kwargs={"token_id": guest_token.id}))
    assert response.status_code == 403
    assert AccessToken.objects.filter(id=guest_token.id).exists()


@pytest.mark.django_db
def test_settings_invalid_form_submission(sample_user: AbstractBaseUser):
    client = Client()
    assert client.login(username=os.environ["DJANGO_TEST_USER"], password=os.environ["DJANGO_TEST_PASSWORD"])

    initial_count = AccessToken.objects.count()

    # Submit empty form
    response = client.post(
        reverse("core:settings"),
        {"description": ""},  # Invalid empty description
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 200
    assert AccessToken.objects.count() == initial_count
    messages = list(get_messages(response.wsgi_request))
    assert not any(m.message == "New access token created" for m in messages)
