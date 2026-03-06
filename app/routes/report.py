import asyncio
from time import perf_counter
from fastapi import APIRouter, UploadFile, File, status
from fastapi.responses import Response
import re

from app.core.logger import get_logger
from app.core.config import get_settings
from app.core.errors import (
    APIException,
    ErrorCode,
    ErrorCategory,
    ErrorSeverity,
)
from app.services.zip_service import ZipService
from app.services.ai_service import AIService
from app.services.report_service import ReportService

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix=settings.API_PREFIX, tags=["Reports"])


@router.post("/generate-report", status_code=status.HTTP_200_OK)
async def generate_report(file: UploadFile = File(...)):
    request_start = perf_counter()

    logger.info(
        "Report generation started",
        extra={"uploaded_filename": file.filename, "content_type": file.content_type},
    )

    # ------------------------------------------------------------------
    # Validate input
    # ------------------------------------------------------------------
    if not file.filename.lower().endswith(".zip"):
        raise APIException(
            error_code=ErrorCode.INVALID_ZIP,
            message="File must be a ZIP archive",
            status_code=400,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
        )

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > settings.MAX_ZIP_SIZE_MB:
        raise APIException(
            error_code=ErrorCode.INVALID_ZIP,
            message=f"ZIP file exceeds maximum size of {settings.MAX_ZIP_SIZE_MB}MB",
            status_code=413,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
        )

    # ------------------------------------------------------------------
    # Extract ZIP (ORDER FROZEN HERE)
    # ------------------------------------------------------------------
    zip_start = perf_counter()
    artifact_data = await ZipService.extract_and_parse(content)
    zip_time_ms = round((perf_counter() - zip_start) * 1000, 2)

    steps = artifact_data["steps"]
    
    # ------------------------------------------------------------------
    # Mandatory artifacts validation (already validated in ZipService,
    # but we double-assert at boundary layer for safety)
    # ------------------------------------------------------------------
    final_script = artifact_data.get("final_script")
    # ------------------------------------------------------------------
    # Extract test_case_id from final_script (MANDATORY)
    # ------------------------------------------------------------------
    match = re.search(
        r"test_case_id\s*=\s*['\"]([^'\"]+)['\"]",
        final_script,
    )

    if not match:
        raise APIException(
            error_code=ErrorCode.MISSING_ARTIFACTS,
            message="Unable to extract test_case_id from final_script.py",
            status_code=500,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.CRITICAL,
        )

    testcase_name = match.group(1)
    execution_video = artifact_data.get("execution_video")
    repair_report = artifact_data.get("repair_report")

    if not final_script:
        raise APIException(
            error_code=ErrorCode.MISSING_ARTIFACTS,
            message="final_script missing after ZIP extraction",
            status_code=500,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.CRITICAL,
        )

    if not execution_video:
        raise APIException(
            error_code=ErrorCode.MISSING_ARTIFACTS,
            message="execution_video missing after ZIP extraction",
            status_code=500,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.CRITICAL,
        )

    # HARD ASSERT — NEVER REMOVE
    indices = [s["summary"]["step_index"] for s in steps]
    if indices != sorted(indices):
        raise APIException(
            error_code=ErrorCode.INTERNAL,
            message="Step order corrupted after ZIP extraction",
            status_code=500,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.CRITICAL,
            details={"indices": indices},
        )

    # ------------------------------------------------------------------
    # AI STEP SUMMARIES (ORDER-SAFE)
    # ------------------------------------------------------------------
    ai_start = perf_counter()
    ai_service = AIService()

    ai_results = await ai_service.enrich_steps_with_summaries(steps)

    for step in steps:
        idx = step["summary"]["step_index"]
        step["ai_summary"] = ai_results.get(idx, "")

    ai_time_ms = round((perf_counter() - ai_start) * 1000, 2)

    # ------------------------------------------------------------------
    # Overall execution description
    # ------------------------------------------------------------------
    passed_steps = sum(1 for s in steps if s["summary"]["status"] == "passed")
    failed_steps = len(steps) - passed_steps
    total_duration = sum(s["summary"].get("duration_sec") or 0 for s in steps)

    overall_description = await ai_service.generate_overall_description(
        total_steps=len(steps),
        passed_steps=passed_steps,
        failed_steps=failed_steps,
        duration_sec=total_duration,
    )

    # ------------------------------------------------------------------
    # Generate HTML (ORDER PRESERVED)
    # ------------------------------------------------------------------
    html_start = perf_counter()

    html_content = ReportService.generate_html(
        steps=steps,
        overall_description=overall_description,
        started_at=artifact_data["started_at"],
        finished_at=artifact_data["finished_at"],
        final_script=final_script,
        execution_video=execution_video,
        testcase_name=testcase_name,
        repair_report=repair_report,
    )

    html_time_ms = round((perf_counter() - html_start) * 1000, 2)
    total_time_ms = round((perf_counter() - request_start) * 1000, 2)

    logger.info(
        "Report generated successfully",
        extra={
            "steps": len(steps),
            "zip_time_ms": zip_time_ms,
            "ai_time_ms": ai_time_ms,
            "html_time_ms": html_time_ms,
            "total_time_ms": total_time_ms,
        },
    )

    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=report.html"},
    )
