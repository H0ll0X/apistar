import os
import typing

import dj_database_url
import pytest

from apistar import App, Route, TestClient, http, typesystem
from apistar.backends import django_orm
from apistar.backends.django_orm import Session


class Kitten(typesystem.Object):
    properties = {
        'id': typesystem.Integer,
        'name': typesystem.String
    }


def list_kittens(session: Session) -> typing.List[Kitten]:
    records = session.Kitten.objects.all()
    return [Kitten(record) for record in records]


def create_kitten(session: Session, name: http.QueryParam, force_fail: http.QueryParam) -> Kitten:
    record = session.Kitten(name=name)
    record.save()
    if force_fail:
        raise Exception
    return Kitten(record)


routes = [
    Route('/kittens/', 'GET', list_kittens),
    Route('/kittens/', 'POST', create_kitten),
]

settings = {
    'DATABASES': {
        'default': dj_database_url.config(
            default=os.environ.get('DB_URL', 'sqlite://')
        )
    },
    'INSTALLED_APPS': ['django_app']
}

app = App(
    routes=routes,
    settings=settings,
    commands=django_orm.commands,
    components=django_orm.components
)

client = TestClient(app)

app.main(['migrate'])


def test_list_create():
    # Successfully create a new record.
    response = client.post('/kittens/?name=minky')
    assert response.status_code == 200
    created_kitten = response.json()
    assert created_kitten['name'] == 'minky'

    # List all the existing records.
    response = client.get('/kittens/')
    assert response.status_code == 200
    assert response.json() == [created_kitten]

    # Rollback a session without creating a new record.
    with pytest.raises(Exception):
        response = client.post('/kittens/?name=fluffums&force_fail=1')
    response = client.get('/kittens/')
    assert response.status_code == 200
    assert response.json() == [created_kitten]