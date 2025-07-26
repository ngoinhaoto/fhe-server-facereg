import logging # Still import logging for info/warning levels

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from models.database import FaceEmbedding # No need to import User if we're not querying it directly by its public user_id
import uuid

# Configure logging at the module level
logger = logging.getLogger(__name__)
# Set level to INFO to keep info/warning messages, but errors will not explicitly log if you remove the calls
logger.setLevel(logging.INFO) 

router = APIRouter()
MAX_EMBEDDING_PER_STUDENT = 5


@router.post("/store-encrypted-embedding/")
async def store_fhe_encrypted_embedding(
    user_id: int = Form(...),  # Expecting an integer ID directly now
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    logger.info(f"Received request to store embedding for user_id (integer): {user_id}")
    try:
        encrypted_data = await file.read()

        if not user_id: 
            logger.warning("User ID is missing from the form data (should be integer).")
            raise HTTPException(status_code=400, detail="User ID is required")
        if not encrypted_data or len(encrypted_data) < 100:
            logger.warning(f"Encrypted embedding is empty or too small for user_id: {user_id}")
            raise HTTPException(status_code=400, detail="Encrypted embedding is empty or too small")

        # 1. Count existing face embeddings for this user using the directly provided integer ID
        logger.info(f"Counting existing embeddings for user_id (integer PK): {user_id}")
        existing_embeddings_count = db.query(FaceEmbedding).filter(
            FaceEmbedding.user_id == user_id  # Use the integer ID directly!
        ).count()
        logger.info(f"Found {existing_embeddings_count} existing embeddings for user_id: {user_id}")

        # 2. Enforce the limit
        if existing_embeddings_count >= MAX_EMBEDDING_PER_STUDENT:
            logger.warning(f"Maximum embedding limit reached for user_id: {user_id}. (Current: {existing_embeddings_count})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum of 5 face embeddings already stored for this user. Please delete an existing embedding before adding a new one."
            )
        else:
            logger.info(f"User {user_id} has {existing_embeddings_count} embeddings. Proceeding to store new embedding.")
        
        registration_group_id = str(uuid.uuid4())
        embedding = FaceEmbedding(
            user_id=user_id,  # Use the integer ID directly
            encrypted_embedding=encrypted_data,
            device_id="fhe_microservice",
            model_type="deepface",
            registration_group_id=registration_group_id,
            embedding_type="fhe_ckks"
        )
        logger.info(f"Prepared new FaceEmbedding object for user_id: {user_id}")

        db.add(embedding)
        db.commit()
        db.refresh(embedding)
        logger.info(f"Successfully stored new embedding (ID: {embedding.id}) for user_id: {user_id}")

        return {
            "message": "FHE encrypted embedding stored successfully",
            "embedding_id": embedding.id,
            "registration_group_id": registration_group_id,
            "embedding_type": "fhe_ckks"
        }
    except HTTPException as e:
        # Keep this, as it re-raises the HTTPException that FastAPI then handles
        # and logs by default (e.g., 400 Bad Request)
        raise e
    except Exception as e:
        # This catch-all for unexpected errors still raises a 500
        # but the specific traceback logging is removed as requested
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {str(e)}"
        )