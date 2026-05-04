import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from app.controllers.audit_area_controller import router
from app.core.database import Base, engine
from app.entities.audit_area import AuditArea

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite requisições de qualquer origem (no modo dev)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)


# Tenta conectar ao banco com retentativas, pois o Postgres pode demorar a subir
max_retries = 10
for i in range(max_retries):
    try:
        Base.metadata.create_all(bind=engine)
        print("Banco de dados conectado e tabelas verificadas.")
        break
    except OperationalError:
        print(f"Banco de dados ainda não está pronto. Tentando novamente em 3 segundos... ({i+1}/{max_retries})")
        time.sleep(3)


app.include_router(router)
