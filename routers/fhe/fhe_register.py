from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from models.database import FaceEmbedding
import uuid

router = APIRouter()

@router.post("/store-encrypted-embedding/")
async def store_fhe_encrypted_embedding(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        encrypted_data = await file.read()
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        if not encrypted_data or len(encrypted_data) < 100:
            raise HTTPException(status_code=400, detail="Encrypted embedding is empty or too small")
        registration_group_id = str(uuid.uuid4())
        embedding = FaceEmbedding(
            user_id=user_id,
            encrypted_embedding=encrypted_data,
            device_id="fhe_microservice",
            model_type="deepface",
            registration_group_id=registration_group_id,
        )

        
        db.add(embedding)
        db.commit()
        db.refresh(embedding)
        return {
            "message": "FHE encrypted embedding stored successfully",
            "embedding_id": embedding.id,
            "registration_group_id": registration_group_id,
            "embedding_type": "fhe_ckks"
        }
    except Exception as e:
        print(f"Error in store_fhe_encrypted_embedding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error storing FHE embedding: {str(e)}"
        )