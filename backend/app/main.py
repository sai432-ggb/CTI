from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import analysis #, history (add when ready)
from .config import settings

# Create DB Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",    # This is your current React frontend
        "http://127.0.0.1:8080",    # Adding this just to be safe
        "http://localhost:3000",    # Backup port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router)

@app.get("/")
def health_check():
    return {"status": "CTI Backend is running natively."}