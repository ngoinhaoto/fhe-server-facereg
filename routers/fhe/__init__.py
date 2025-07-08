from fastapi import APIRouter

from .fhe_register import router as fhe_register_router
from .fhe_verification import router as fhe_verification_router

router = APIRouter(prefix="/fhe", tags=["FHE"])

router.include_router(fhe_register_router)
router.include_router(fhe_verification_router)

