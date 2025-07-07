from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    error_code: Optional[str] = Field(None, description="Application-specific error code")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Rate limit exceeded",
                "status_code": 429,
                "error_code": "RATE_LIMIT_EXCEEDED",
            }
        }
    }


class ValidationErrorDetail(BaseModel):
    """Details about a validation error."""

    loc: List[str] = Field(..., description="Location of the error")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ValidationErrorResponse(BaseModel):
    """Validation error response."""

    detail: List[ValidationErrorDetail] = Field(..., description="List of validation errors")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": [
                    {
                        "loc": ["body", "prompt"],
                        "msg": "String should have at least 10 characters",
                        "type": "string_too_short",
                    }
                ]
            }
        }
    }


class SuccessResponse(BaseModel):
    """Generic success response."""

    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Operation completed successfully",
                "data": {"affected_items": 5},
            }
        }
    }


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    

class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "per_page": 20,
                "pages": 5,
            }
        }
    }