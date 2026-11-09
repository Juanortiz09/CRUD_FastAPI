from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from sqlalchemy.exc import IntegrityError

from ..models.persona import Persona
from ..views.persona import PersonaCreate, PersonaUpdate
from .errors import PersonaNotFoundError, EmailAlreadyExistsError

import random
import re
import unicodedata
from faker import Faker

def create_persona(db: Session, payload: PersonaCreate) -> Persona:
    """Create a Persona ensuring unique email."""
    # Optimistic check; DB unique constraint is the final guard
    if db.query(Persona).filter(Persona.email == payload.email).first():
        raise EmailAlreadyExistsError()
    obj = Persona(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
        birth_date=payload.birth_date,
        is_active=payload.is_active,
        notes=payload.notes,
    )
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # Catch race conditions on unique email
        raise EmailAlreadyExistsError() from e
    db.refresh(obj)
    return obj


def list_personas(db: Session, skip: int = 0, limit: int = 100) -> Sequence[Persona]:
    """Return paginated list of Personas."""
    return db.query(Persona).offset(skip).limit(limit).all()


def get_persona(db: Session, persona_id: int) -> Persona:
    """Return Persona by ID or raise if not found."""
    obj = db.query(Persona).filter(Persona.id == persona_id).first()
    if not obj:
        raise PersonaNotFoundError()
    return obj


def update_persona(db: Session, persona_id: int, payload: PersonaUpdate) -> Persona:
    """Update Persona partially, enforcing unique email."""
    obj = db.query(Persona).filter(Persona.id == persona_id).first()
    if not obj:
        raise PersonaNotFoundError()

    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"] != obj.email:
        if db.query(Persona).filter(Persona.email == data["email"], Persona.id != persona_id).first():
            raise EmailAlreadyExistsError()

    for field, value in data.items():
        setattr(obj, field, value)

    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise EmailAlreadyExistsError() from e
    db.refresh(obj)
    return obj


def delete_persona(db: Session, persona_id: int) -> None:
    """Delete Persona by ID or raise if not found."""
    obj = db.query(Persona).filter(Persona.id == persona_id).first()
    if not obj:
        raise PersonaNotFoundError()
    db.delete(obj)
    db.commit()

def poblar_personas(db: Session, cantidad: int) -> int:
    """Generar personas aleatorias usando Faker."""

    fake = Faker("es_CO")
    dominios = ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com"]

    correos_existentes = {
        correo.lower()
        for (correo,) in db.query(Persona.email).all()
    }

    personas = []

    for _ in range(cantidad):
        first_name = fake.first_name()
        last_name = fake.last_name()

        nombre = unicodedata.normalize("NFKD", first_name)
        nombre = "".join(c for c in nombre if not unicodedata.combining(c))
        nombre = re.sub(r"[^a-zA-Z0-9]", "", nombre).lower()

        apellido = unicodedata.normalize("NFKD", last_name)
        apellido = "".join(c for c in apellido if not unicodedata.combining(c))
        apellido = re.sub(r"[^a-zA-Z0-9]", "", apellido).lower()

        dominio = random.choice(dominios)
        correo_base = f"{nombre}.{apellido}"
        email = f"{correo_base}@{dominio}"

        consecutivo = 1
        while email in correos_existentes:
            email = f"{correo_base}{consecutivo}@{dominio}"
            consecutivo += 1

        correos_existentes.add(email)

        persona = Persona(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=fake.numerify(text="3#########"),
            birth_date=fake.date_of_birth(minimum_age=18, maximum_age=85),
            is_active=fake.boolean(),
            notes=fake.sentence(nb_words=6) if random.choice([True, False]) else None,
        )

        personas.append(persona)

    db.add_all(personas)
    db.commit()

    return len(personas)

def reset_personas(db: Session) -> int:
    """Eliminar todas las personas de la base de datos."""

    cantidad_eliminada = db.query(Persona).count()

    db.query(Persona).delete(synchronize_session=False)

    db.commit()

    return cantidad_eliminada

def estadisticas_dominios(db: Session):
    """Contar personas por dominio de correo."""

    dominio = func.substr(
        Persona.email,
        func.instr(Persona.email, "@") + 1
    )

    resultados = (
        db.query(
            dominio.label("dominio"),
            func.count(Persona.id).label("cantidad")
        )
        .group_by(dominio)
        .order_by(func.count(Persona.id).desc())
        .all()
    )

    return [
        {
            "dominio": resultado.dominio,
            "cantidad": resultado.cantidad
        }
        for resultado in resultados
    ]

    resultados = (
        db.query(
            func.substring_index(Persona.email, "@", -1).label("dominio"),
            func.count(Persona.id).label("cantidad")
        )
        .group_by(func.substring_index(Persona.email, "@", -1))
        .order_by(func.count(Persona.id).desc())
        .all()
    )

    return [
        {
            "dominio": resultado.dominio,
            "cantidad": resultado.cantidad
        }
        for resultado in resultados
    ]
def cumpleanios_por_mes(db: Session, numero_mes: int):
    """Retornar personas que cumplen años en el mes indicado."""

    resultados = (
        db.query(Persona)
        .filter(extract("month", Persona.birth_date) == numero_mes)
        .all()
    )

    return resultados

    return resultados
def desactivar_personas_masivo(db: Session, ids: list[int]):
    """Desactivar varias personas mediante sus IDs."""

    personas = (
        db.query(Persona)
        .filter(Persona.id.in_(ids))
        .all()
    )

    ids_encontrados = [persona.id for persona in personas]
    ids_no_encontrados = [
        persona_id for persona_id in ids
        if persona_id not in ids_encontrados
    ]

    for persona in personas:
        persona.is_active = False

    db.commit()

    return {
        "desactivados": ids_encontrados,
        "no_encontrados": ids_no_encontrados,
        "total_desactivados": len(ids_encontrados)
    }