import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.persona import Persona


SQLALCHEMY_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture
def client():
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def test_poblar_crea_cantidad_solicitada(client):
    respuesta = client.post(
        "/personas/poblar",
        json={"cantidad": 5},
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["cantidad_creada"] == 5

    with TestingSessionLocal() as db:
        assert db.query(Persona).count() == 5


def test_poblar_rechaza_cantidad_cero(client):
    respuesta = client.post(
        "/personas/poblar",
        json={"cantidad": 0},
    )

    assert respuesta.status_code == 400


def test_poblar_rechaza_cantidad_superior_al_limite(client):
    respuesta = client.post(
        "/personas/poblar",
        json={"cantidad": 1001},
    )

    assert respuesta.status_code == 400


def test_poblar_no_genera_correos_duplicados(client):
    respuesta = client.post(
        "/personas/poblar",
        json={"cantidad": 30},
    )

    assert respuesta.status_code == 201

    with TestingSessionLocal() as db:
        correos = [
            persona.email
            for persona in db.query(Persona).all()
        ]

    assert len(correos) == 30
    assert len(correos) == len(set(correos))

def test_reset_elimina_todas_las_personas(client):
    client.post(
        "/personas",
        json={
            "first_name": "Ana",
            "last_name": "Prueba",
            "email": "ana.reset@example.com",
            "phone": "3001234567",
            "birth_date": "1995-05-10",
            "is_active": True,
        },
    )

    respuesta = client.delete("/personas/reset")

    assert respuesta.status_code == 200
    assert respuesta.json()["deleted_count"] == 1


def test_reset_sin_personas(client):
    respuesta = client.delete("/personas/reset")

    assert respuesta.status_code == 200
    assert respuesta.json()["deleted_count"] == 0

def test_estadisticas_dominios_cuenta_correctamente(client):
    correos = [
        "ana@gmail.com",
        "juan@gmail.com",
        "pedro@hotmail.com",
    ]

    for i, correo in enumerate(correos):
        client.post(
            "/personas",
            json={
                "first_name": f"Persona{i}",
                "last_name": "Prueba",
                "email": correo,
                "phone": f"300123456{i}",
                "birth_date": "1995-05-10",
                "is_active": True,
            },
        )

    respuesta = client.get("/personas/estadisticas/dominios")

    assert respuesta.status_code == 200
    datos = {item["dominio"]: item["cantidad"] for item in respuesta.json()}
    assert datos["gmail.com"] == 2
    assert datos["hotmail.com"] == 1


def test_estadisticas_dominios_sin_personas(client):
    respuesta = client.get("/personas/estadisticas/dominios")

    assert respuesta.status_code == 200
    assert respuesta.json() == []

def test_poblar_rechaza_cantidad_faltante(client):
    respuesta = client.post("/personas/poblar", json={})

    assert respuesta.status_code == 422


def test_poblar_rechaza_cantidad_no_numerica(client):
    respuesta = client.post(
        "/personas/poblar",
        json={"cantidad": "muchas"}
    )

    assert respuesta.status_code == 422