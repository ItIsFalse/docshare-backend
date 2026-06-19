from typing import Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class BaseResponse(BaseModel):
    success: bool = True
    message: str = "OK"

class DataResponse(BaseResponse, Generic[T]):
    data: Optional[T] = None

class ErrorResponse(BaseModel):
    error: dict = {
        "code": "ERROR",
        "message": "Something went wrong"
    }