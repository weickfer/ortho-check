from fastapi import FastAPI
from app.controllers.audit_area_controller import router

app = FastAPI()
app.include_router(router)
