"""Request models for OmniDimension webhook payloads.

OmniDimension webhook payloads may include many fields. These models define the
fields Signo cares about while still allowing extra webhook fields to pass
through without breaking validation.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class FlexibleBaseModel(BaseModel):
    """Base model that accepts extra webhook fields safely."""

    class Config:
        extra = "allow"


class Interaction(FlexibleBaseModel):
    """One message or event from the call conversation."""

    role: Optional[str] = None
    message: Optional[str] = None
    content: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class ExtractedVariables(FlexibleBaseModel):
    """Important fields OmniDimension extracted during the call."""

    driver_mobile_number: Optional[str] = None
    category_selected: Optional[str] = None
    conversation_summary: Optional[str] = None
    language: Optional[str] = None
    driver_id: Optional[str] = None
    query_description: Optional[str] = None


class CallReport(FlexibleBaseModel):
    """Call report section from the OmniDimension webhook."""

    summary: Optional[str] = None
    extracted_variables: Optional[ExtractedVariables] = None
    interactions: Optional[list[Interaction]] = Field(default_factory=list)


class OmniDimensionWebhookPayload(FlexibleBaseModel):
    """Full OmniDimension webhook payload accepted by POST /memory/save."""

    call_id: Optional[int] = None
    bot_id: Optional[int] = None
    call_request_id: Optional[int] = None
    bot_name: Optional[str] = None
    call_status: Optional[str] = None
    call_duration: Optional[int] = None
    call_report: Optional[CallReport] = None
    extracted_variables: Optional[ExtractedVariables] = None
    interactions: Optional[list[Interaction]] = Field(default_factory=list)
