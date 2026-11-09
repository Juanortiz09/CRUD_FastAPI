
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# Base de datos SQLite independiente, solo para pruebas
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


def crear_persona(client, email, birth_date="1995-05-10"):
    return client.post(
        "/personas",
        json={
            "first_name": "Ana",
            "last_name": "Prueba",
            "email": email,
            "phone": "3001234567",
            "birth_date": birth_date,
            "is_active": True,
            "notes": "Registro de prueba",
        },
    )


def test_g_cumpleanios_por_mes(client):
    respuesta = crear_persona(
        client, "ana.mayo@example.com", "1995-05-10"
    )
    assert respuesta.status_code == 201

    respuesta = client.get("/personas/cumpleanios/mes/5")

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1


def test_g_rechaza_mes_invalido(client):
    respuesta = client.get("/personas/cumpleanios/mes/13")

    assert respuesta.status_code == 400


def test_h_desactivar_personas(client):
    respuesta = crear_persona(client, "ana.bulk@example.com")
    assert respuesta.status_code == 201

    persona_id = respuesta.json()["id"]

    respuesta = client.patch(
        "/personas/bulk/desactivar",
        json={"ids": [persona_id, 99999]},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["total_desactivados"] == 1
    assert respuesta.json()["no_encontrados"] == [99999]


def test_h_rechaza_lista_vacia(client):
    respuesta = client.patch(
        "/personas/bulk/desactivar",
        json={"ids": []},
    )

    assert respuesta.status_code == 400


def test_i_exportar_csv(client):
    crear_persona(client, "ana.csv@example.com")

    respuesta = client.get("/personas/exportar/csv")

    assert respuesta.status_code == 200
    assert "text/csv" in respuesta.headers["content-type"]
    assert "ana.csv@example.com" in respuesta.text
    assert "first_name" in respuesta.text
def test_h_rechaza_ids_no_positivos(client):
    respuesta = client.patch(
        "/personas/bulk/desactivar",
        json={"ids": [0, -1]},
    )

    assert respuesta.status_code == 400


def test_h_rechaza_mas_de_100_ids(client):
    respuesta = client.patch(
        "/personas/bulk/desactivar",
        json={"ids": list(range(1, 102))},
    )

    assert respuesta.status_code == 400


def test_h_desactivar_varias_personas(client):
    persona1 = crear_persona(client, "ana1.bulk@example.com")
    persona2 = crear_persona(client, "ana2.bulk@example.com")

    assert persona1.status_code == 201
    assert persona2.status_code == 201

    id1 = persona1.json()["id"]
    id2 = persona2.json()["id"]

    respuesta = client.patch(
        "/personas/bulk/desactivar",
        json={"ids": [id1, id2]},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["total_desactivados"] == 2
    assert respuesta.json()["no_encontrados"] == []
def test_g_cumpleanios_en_enero(client):
    respuesta = crear_persona(
        client, "enero@example.com", "1995-01-15"
    )
    assert respuesta.status_code == 201

    respuesta = client.get("/personas/cumpleanios/mes/1")

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1


def test_g_cumpleanios_en_diciembre(client):
    respuesta = crear_persona(
        client, "diciembre@example.com", "1995-12-20"
    )
    assert respuesta.status_code == 201

    respuesta = client.get("/personas/cumpleanios/mes/12")

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1


def test_g_mes_sin_cumpleanios(client):
    respuesta = client.get("/personas/cumpleanios/mes/8")

    assert respuesta.status_code == 200
    assert respuesta.json() == []
def test_i_exportar_csv_tiene_encabezados_y_nombre(client):
    respuesta = client.get("/personas/exportar/csv")

    assert respuesta.status_code == 200
    assert "attachment; filename=personas.csv" in (
        respuesta.headers["content-disposition"]
    )

    encabezados = respuesta.text.splitlines()[0]

    columnas_esperadas = [
        "id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "birth_date",
        "is_active",
        "notes",
        "created_at",
    ]

    for columna in columnas_esperadas:
        assert columna in encabezados


def test_i_exportar_csv_sin_registros(client):
    respuesta = client.get("/personas/exportar/csv")

    assert respuesta.status_code == 200
    assert "text/csv" in respuesta.headers["content-type"]
    assert "first_name" in respuesta.text