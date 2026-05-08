import pytest

from marketplace.models import User


@pytest.mark.django_db
def test_register_sets_sfsu_email_and_does_not_crash(client):
    resp = client.post(
        "/register/",
        data={
            "username": "alice",
            "email": "alice@sfsu.edu",
            "password1": "StrongPass1!",
            "password2": "StrongPass1!",
        },
    )

    # Successful registration redirects to home.
    assert resp.status_code in (302, 303)

    user = User.objects.get(username="alice")
    assert user.email == "alice@sfsu.edu"
    assert user.sfsu_email == "alice@sfsu.edu"


@pytest.mark.django_db
def test_register_two_users_no_duplicate_empty_sfsu_email(client):
    resp1 = client.post(
        "/register/",
        data={
            "username": "bob",
            "email": "bob@sfsu.edu",
            "password1": "StrongPass1!",
            "password2": "StrongPass1!",
        },
    )
    assert resp1.status_code in (302, 303)

    resp2 = client.post(
        "/register/",
        data={
            "username": "carol",
            "email": "carol@sfsu.edu",
            "password1": "StrongPass1!",
            "password2": "StrongPass1!",
        },
    )
    assert resp2.status_code in (302, 303)

    assert User.objects.filter(sfsu_email="").count() == 0
