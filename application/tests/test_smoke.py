import pytest

from django.contrib.auth import get_user_model


@pytest.fixture
def logged_in_user(db):
    User = get_user_model()
    user = User(
        username="smokeuser",
        email="smokeuser@sfsu.edu",
        sfsu_email="smokeuser@sfsu.edu",
    )
    user.set_password("StrongPass1!")
    user.password_hash = user.password
    user.save()
    return user


@pytest.fixture
def logged_in_client(client, logged_in_user):
    client.force_login(logged_in_user)
    return client


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    [
        "/",
        "/team",
        "/login/",
        "/register/",
        "/search/?q=test",
    ],
)
def test_public_marketplace_pages_load(client, url):
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    [
        "/account/",
        "/chat/",
        "/listings/new/",
    ],
)
def test_authenticated_marketplace_pages_load(logged_in_client, url):
    response = logged_in_client.get(url)
    assert response.status_code == 200
