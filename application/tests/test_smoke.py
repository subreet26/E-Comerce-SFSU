import pytest


@pytest.mark.django_db
def test_homepage_loads(client):
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_team_page_loads(client):
    response = client.get("/team")
    assert response.status_code == 200
