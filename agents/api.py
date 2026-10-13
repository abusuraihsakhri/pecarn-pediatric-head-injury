"""
FastAPI REST API Server for Pecarn Pediatric Head Injury.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from pecarn_rule import calculate_metrics
from pydantic import BaseModel, ConfigDict, StrictBool, StrictInt
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Pecarn Pediatric Head Injury API",
    description="Age-specific PECARN decision rule and separately labeled legacy demonstration API",
    version="4.0.0",
)


class PECARNRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    age_months: StrictInt
    gcs: StrictInt
    hours_since_injury: float
    exclusion_present: StrictBool
    altered_mental_status: StrictBool
    severe_mechanism: StrictBool
    palpable_skull_fracture: StrictBool | None = None
    nonfrontal_scalp_hematoma: StrictBool | None = None
    loc_at_least_5_seconds: StrictBool | None = None
    not_acting_normally: StrictBool | None = None
    basilar_skull_fracture_signs: StrictBool | None = None
    any_loss_of_consciousness: StrictBool | None = None
    vomiting: StrictBool | None = None
    severe_headache: StrictBool | None = None


class ChatRequest(BaseModel):
    query: str


@app.get("/")
def homepage():
    return FileResponse(Path(__file__).resolve().parent.parent / "web" / "index.html", media_type="text/html")


@app.get("/app.js")
def browser_rule():
    return FileResponse(Path(__file__).resolve().parent.parent / "web" / "app.js", media_type="text/javascript")


@app.post("/api/pecarn")
def api_pecarn(payload: PECARNRequest):
    try:
        return calculate_metrics(**payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "pecarn-pediatric-head-injury", "version": "4.0.0", "clinical_rule_endpoint": "/api/pecarn", "legacy_audit_endpoint": "/api/audit"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "demonstration_only": True
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    from .base import SecurityException
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        raise HTTPException(status_code=422, detail="Input contains a prohibited identifier")
    return {**dossier.to_dict(), "demonstration_only": True, "warning": "Generic component demonstration, NOT PECARN clinical risk stratification"}


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans, "demonstration_only": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
