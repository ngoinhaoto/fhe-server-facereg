from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from database.db import get_db
from models.database import FaceEmbedding, User, Attendance, ClassSession, AttendanceStatus
from utils.tenseal_context import load_public_context
import tenseal as ts
import base64
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class FHECheckInRequest(BaseModel):
    session_id: int
    user_id: int
    verification_method: str = "fhe"

@router.post("/verify-with-embedding/")
async def verify_with_embedding(
    file: UploadFile = File(...),
    session_id: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        enc_bytes = await file.read()
        context = load_public_context()
        query = db.query(FaceEmbedding, User).join(
            User, FaceEmbedding.user_id == User.id
        ).filter(
            FaceEmbedding.embedding_type == "fhe_ckks"
        )
        if session_id:
            # Optionally filter by session/class
            pass  # Add your session filtering logic here

        stored_embeddings = query.all()
        if not stored_embeddings:
            return {
                "verified": False,
                "message": "No registered faces found",
                "results": [],
                "session_id": session_id,
                "embedding_count": 0
            }

        # Load the uploaded encrypted embedding
        enc_vec = ts.lazy_ckks_vector_from(enc_bytes)
        enc_vec.link_context(context)

        results = []
        for embedding_obj, user in stored_embeddings:
            try:
                stored_vec = ts.lazy_ckks_vector_from(embedding_obj.encrypted_embedding)
                stored_vec.link_context(context)

                enc_similarity =  enc_vec.dot(stored_vec)  

                serialized = base64.b64encode(enc_similarity.serialize()).decode("utf-8")
                results.append({
                    "user_id": user.id,
                    "username": user.username,
                    "full_name": getattr(user, "full_name", None),
                    "role": getattr(user, "role", None),
                    "encrypted_similarity": serialized,
                    "embedding_id": embedding_obj.id
                })
            except Exception as e:
                results.append({
                    "user_id": user.id,
                    "error": f"Error computing similarity: {str(e)}"
                })

        return {
            "results": results,
            "session_id": session_id,
            "embedding_count": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying with embedding: {str(e)}"
        )

@router.post("/fhe-check-in")
async def fhe_check_in(
    data: FHECheckInRequest,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),

):
    """Record attendance based on FHE verification from microservice"""
    session_id = data.session_id
    user_id = data.user_id
    verification_method = data.verification_method

    # Validate session
    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class session not found"
        )

    # Validate user
    student_user = db.query(User).filter(User.id == user_id).first()
    if not student_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in database."
        )

    # Check if the student has access to this class
    student_has_access = any(c.id == session.class_id for c in student_user.classes)
    if not student_has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student is not enrolled in this class."
        )

    # Check if attendance record already exists
    existing_attendance = db.query(Attendance).filter(
        Attendance.student_id == user_id,
        Attendance.session_id == session_id
    ).first()

    now = datetime.now(timezone.utc)
    late_minutes = 0
    attendance_status = AttendanceStatus.PRESENT.value
    if now > session.start_time:
        time_diff = now - session.start_time
        late_minutes = int(time_diff.total_seconds() / 60)
        if late_minutes > 0:
            attendance_status = AttendanceStatus.LATE.value

    try:
        if existing_attendance:
            existing_attendance.status = attendance_status
            existing_attendance.check_in_time = now
            existing_attendance.late_minutes = late_minutes
            existing_attendance.verification_method = verification_method
        else:
            attendance = Attendance(
                student_id=user_id,
                session_id=session_id,
                status=attendance_status,
                check_in_time=now,
                late_minutes=late_minutes,
                verification_method=verification_method
            )
            db.add(attendance)

        db.commit()

        class_info = session.class_obj

        return {
            "message": "Attendance recorded successfully via FHE",
            "status": attendance_status,
            "late_minutes": late_minutes if attendance_status == AttendanceStatus.LATE.value else 0,
            "user": {
                "id": student_user.id,
                "name": student_user.full_name,
                "username": student_user.username,
                "role": student_user.role
            },
            "session": {
                "id": session.id,
                "date": session.session_date,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "class": {
                    "id": class_info.id,
                    "name": class_info.name,
                    "code": class_info.class_code
                }
            },
            "check_in_time": now,
            "verification_method": verification_method
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error recording FHE attendance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording attendance: {str(e)}"
        )