from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from security.auth import oauth2_scheme  # Import the OAuth2 scheme
from sqlalchemy.orm import Session
from database.db import get_db
import uvicorn
from routers import auth, users, classes, attendance, fhe
from routers.admin import dashboard  
from utils.tenseal_context import load_public_context
import os

CONTEXT_DIR = os.getenv("CONTEXT_DIR", "context")
PUBLIC_PATH = os.path.join(CONTEXT_DIR, "public.txt")

app = FastAPI(
    title="Face Recognition System",
    description="API for face recognition attendance system",
    version="0.1.0",
    openapi_tags=[
        {"name": "Authentication", "description": "Authentication operations"},
        {"name": "Users", "description": "User management operations"},
        {"name": "Classes", "description": "Class management operations"},
        {"name": "Attendance", "description": "Attendance tracking operations"},
        {"name": "Admin", "description": "Admin dashboard operations"},
    ],
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(classes.router)
app.include_router(attendance.router)
app.include_router(fhe.router)
app.include_router(
    dashboard.router,
    prefix="/admin",
    tags=["Admin"]
)

public_context = None
if os.path.exists(PUBLIC_PATH):
    public_context = load_public_context()
    print(f"[INFO] TenSEAL public context loaded from {PUBLIC_PATH}")
else:
    print(f"[WARNING] TenSEAL public context not found at {PUBLIC_PATH}. Encrypted operations will fail.")

@app.get("/")
def read_root():
    return {"message": "Face Recognition API running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)