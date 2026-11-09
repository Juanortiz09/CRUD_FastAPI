from typing import List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..views.persona import PersonaCreate, PersonaUpdate, PersonaRead
from ..services import persona_service

router = APIRouter(prefix="/personas", tags=["personas"])
class PoblarRequest(BaseModel):
    cantidad: int


@router.post("/poblar", status_code=status.HTTP_201_CREATED)
def poblar_personas_endpoint(
    datos: PoblarRequest,
    db: Session = Depends(get_db)
):
    if datos.cantidad < 1 or datos.cantidad > 1000:
        raise HTTPException(
            status_code=400,
            detail="La cantidad debe estar entre 1 y 1000"
        )

    cantidad_creada = persona_service.poblar_personas(db, datos.cantidad)

    return {
        "mensaje": "Personas creadas correctamente",
        "cantidad_creada": cantidad_creada
    }


@router.post("", response_model=PersonaRead, status_code=status.HTTP_201_CREATED)
def create_persona(persona_in: PersonaCreate, db: Session = Depends(get_db)):
    """Create a new Persona delegating to service layer."""
    # Let domain errors bubble up to global handlers
    return persona_service.create_persona(db, persona_in)


@router.get("", response_model=List[PersonaRead])
def list_personas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List Personas with pagination via service layer."""
    return persona_service.list_personas(db, skip=skip, limit=limit)

@router.delete("/reset")
def reset_personas_endpoint(db: Session = Depends(get_db)):
    cantidad_eliminada = persona_service.reset_personas(db)

    return {
        "mensaje": "Personas eliminadas correctamente",
        "deleted_count": cantidad_eliminada
    }
@router.get("/estadisticas/dominios")
def estadisticas_dominios_endpoint(db: Session = Depends(get_db)):
    return persona_service.estadisticas_dominios(db)
@router.get("/{persona_id}", response_model=PersonaRead)
def get_persona(persona_id: int, db: Session = Depends(get_db)):
    """Retrieve a Persona by ID via service layer."""
    return persona_service.get_persona(db, persona_id)


@router.put("/{persona_id}", response_model=PersonaRead)
def update_persona(persona_id: int, persona_in: PersonaUpdate, db: Session = Depends(get_db)):
    """Update an existing Persona (partial) via service layer."""
    return persona_service.update_persona(db, persona_id, persona_in)


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_persona(persona_id: int, db: Session = Depends(get_db)):
    """Delete a Persona by ID via service layer."""
    persona_service.delete_persona(db, persona_id)
    return None

from sqlalchemy import func, or_

# 4. Estadísticas de edad
@router.get("/estadisticas/edad")
def obtener_estadisticas_edad(db: Session = Depends(get_db)):
    edad_expr = func.timestampdiff(func.text('YEAR'), Persona.birth_date, func.curdate())
    stats = db.query(
        func.round(func.avg(edad_expr), 1).label("edad_promedio"),
        func.min(edad_expr).label("edad_minima"),
        func.max(edad_expr).label("edad_maxima")
    ).first()
    return {
        "edad_promedio": float(stats.edad_promedio or 0),
        "edad_minima": int(stats.edad_minima or 0),
        "edad_maxima": int(stats.edad_maxima or 0)
    }

# 5. Buscador general
@router.get("/buscar/{termino}")
def buscar_personas(termino: str, db: Session = Depends(get_db)):
    busqueda = f"%{termino}%"
    resultados = db.query(Persona).filter(
        or_(
            Persona.first_name.ilike(busqueda),
            Persona.last_name.ilike(busqueda),
            Persona.email.ilike(busqueda)
        )
    ).all()
    return resultados

# 6. Reporte de activos
@router.get("/reporte/activos")
def reporte_activos(db: Session = Depends(get_db)):
    personas_activas = db.query(Persona).filter(Persona.is_active == True).all()
    reporte = [
        {
            "id": p.id,
            "email": p.email,
            "phone": p.phone,
            "is_active": p.is_active
        }
        for p in personas_activas
    ]
    return reporte
