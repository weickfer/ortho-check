from fastapi import FastAPI
from app.controllers.audit_area_controller import router

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(router)
