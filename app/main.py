from fastapi import FastAPI
from .database import engine
from .database import Base
from .controllers import persona_controller
from .error_handlers import register_exception_handlers


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(title="FastAPI Persona CRUD (MySQL)", version="1.0.0")

    # Register global exception handlers (domain → HTTP)
    register_exception_handlers(app)

    @app.on_event("startup")
    def on_startup() -> None:
        # Create tables at startup (demo purpose)
        Base.metadata.create_all(bind=engine)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(persona_controller.router)
    return app


app = create_app()
"# Ajuste menor" 
"# Ajuste menor 2" 
"# Ajuste menor 3" 
"# Comentario de ajuste 7" 
"# Comentario de ajuste 8" 
"# Comentario de ajuste 9" 
"# Comentario de ajuste 10" 
