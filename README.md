# FastAPI Persona CRUD (MySQL por defecto)

Proyecto de demostración con FastAPI + SQLAlchemy y estructura MVC para un CRUD de `Persona`. Usa MySQL por defecto y permite apuntar a otra base SQL mediante la variable de entorno `DATABASE_URL` (configurable en `.env`).

## Requisitos

- Python 3.10+ (recomendado 3.11)

## Instalación y ejecución

1. Crear entorno virtual e instalar dependencias:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   # Edita .env con tus credenciales de MySQL
   # Por defecto: DATABASE_URL=mysql+pymysql://user:password@localhost:3306/fastapi_demo
   ```

3. Ejecutar el servidor:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Documentación interactiva:
   - Swagger UI: <http://localhost:8000/docs>
   - ReDoc: <http://localhost:8000/redoc>

## Conexión a otras bases de datos

Edita `DATABASE_URL` en `.env`.
- MySQL: `mysql+pymysql://user:password@localhost:3306/mydb`

> Nota: Instala el driver correspondiente (psycopg2, PyMySQL, pyodbc, etc.).

## Ejemplo de `.env` (MySQL local)

```env
DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost:3306/nombre_basedatos
```

## Endpoints principales

- `GET /health` → estado del servicio
- `POST /personas` → crear persona
- `GET /personas` → listar personas (`skip`, `limit`)
- `GET /personas/{id}` → obtener persona por ID
- `PUT /personas/{id}` → actualizar (parcial) persona
- `DELETE /personas/{id}` → eliminar persona

### Esquemas (JSON)

- Crear:
  ```json
  {
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "juan.perez@example.com",
    "phone": "+57 3000000000",
    "birth_date": "1990-05-20",
    "is_active": true,
    "notes": "Cliente frecuente"
  }
  ```

- Actualizar (parcial):
  ```json
  {
    "email": "juan.perez2@example.com",
    "notes": "Actualizado"
  }
  ```

## Colección de Postman

Importa `FastAPI-CRUD-Demo.postman_collection.json` en Postman. Variables:

- `base_url` (por defecto `http://localhost:8000`)
- `persona_id` (por defecto `1`)

## Notas

- Las tablas se crean automáticamente al iniciar (solo con fines de demo).
- Asegúrate de crear la base de datos en MySQL y de que el usuario tenga permisos (por ejemplo, `CREATE DATABASE fastapi_demo;`).

## Estructura MVC

- `app/models/` → modelos SQLAlchemy (por ejemplo, `persona.py`).
- `app/views/` → esquemas Pydantic (por ejemplo, `persona.py`).
- `app/controllers/` → routers/controladores FastAPI (por ejemplo, `persona_controller.py`).

## Pruebas rápidas (curl)

```bash
# Health
curl -s http://127.0.0.1:8000/health

# Crear persona
curl -s -X POST http://127.0.0.1:8000/personas \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name":"Juan",
    "last_name":"Perez",
    "email":"juan.perez@example.com",
    "phone":"+57 3000000000",
    "birth_date":"1990-05-20",
    "is_active":true,
    "notes":"Cliente frecuente"
  }'

# Listar
curl -s http://127.0.0.1:8000/personas

# Obtener por ID
curl -s http://127.0.0.1:8000/personas/1

# Actualizar parcial
curl -s -X PUT http://127.0.0.1:8000/personas/1 \
  -H 'Content-Type: application/json' \
  -d '{"email":"juan.perez2@example.com","notes":"Actualizado"}'

# Eliminar
curl -s -X DELETE http://127.0.0.1:8000/personas/1 -i

## Detener el servidor

- Si lo iniciaste en la misma terminal: usa `CTRL+C`.
- Si corre en background, puedes cerrar esa terminal o matar el proceso de uvicorn (`pkill -f uvicorn`).


## Funcionalidades adicionales del laboratorio

### Desarrollo de Juan Pablo Ortiz
1. **POST `/personas/poblar`**: genera personas aleatorias utilizando Faker. Valida que la cantidad esté entre 1 y 1000.
2. **DELETE `/personas/reset`**: elimina todos los registros de la tabla personas e informa cuántos fueron eliminados.
3. **GET `/personas/estadisticas/dominios`**: consulta la cantidad de personas agrupadas por el dominio de su correo electrónico.

### Desarrollo de Jhon Alex Rivera
4. **GET `/personas/estadisticas/edad`**: consulta la edad promedio, mínima y máxima de las personas.
5. **GET `/personas/buscar/{termino}`**: permite buscar personas por nombre, apellido o correo electrónico.
6. **GET `/personas/reporte/activos`**: genera un reporte con las personas que se encuentran activas.

### Desarrollo de Emanuel Alzate
7. **GET `/personas/cumpleanios/mes/{numero_mes}`**: consulta las personas que cumplen años en un mes determinado.
8. **PATCH `/personas/bulk/desactivar`**: permite desactivar varias personas mediante sus identificadores.
9. **GET `/personas/exportar/csv`**: permite exportar los registros de personas a un archivo CSV.

### Dependencias adicionales
Se agregó la librería Faker al archivo `requirements.txt` para permitir la generación automática de datos de prueba.
 

## Pruebas automatizadas

El proyecto incluye pruebas automatizadas para verificar el funcionamiento de los endpoints de analítica G, H e I.

### Tecnologías utilizadas
- **Pytest:** ejecución de pruebas automatizadas.
- **HTTPX:** cliente para realizar solicitudes HTTP.
- **SQLite:** base de datos independiente utilizada durante las pruebas.

### Ejecutar las pruebas

Desde la raíz del proyecto, activa el entorno virtual e instala las dependencias:

```bash
pip install -r requirements.txt
```

Ejecuta todas las pruebas con:

```bash
python -m pytest tests/test_analitica.py -v
```

### Cobertura de pruebas

- **Endpoint G:** consulta de cumpleaños por mes, validación de meses y resultados vacíos.
- **Endpoint H:** desactivación masiva, validación de identificadores, IDs duplicados y verificación del estado de las personas.
- **Endpoint I:** exportación CSV, encabezados, nombre del archivo y límite de 1000 registros.

Las pruebas utilizan una base de datos SQLite independiente para evitar modificar los datos de MySQL.

