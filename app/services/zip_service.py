import zipfile
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.logger import get_logger
from app.core.errors import (
    APIException,
    ErrorCode,
    ErrorCategory,
    ErrorSeverity,
)

logger = get_logger(__name__)


class ZipService:
    """Enterprise-grade ZIP artifact extraction service."""

    @staticmethod
    async def extract_and_parse(zip_content: bytes) -> Dict[str, Any]:
        zip_path: Optional[Path] = None

        try:
            # ------------------------------------------------------------------
            # Write ZIP to temp file
            # ------------------------------------------------------------------
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                tmp.write(zip_content)
                zip_path = Path(tmp.name)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                names = zip_ref.namelist()

                # ------------------------------------------------------------------
                # ZIP Slip Protection
                # ------------------------------------------------------------------
                for name in names:
                    if ".." in name or name.startswith("/"):
                        raise APIException(
                            error_code=ErrorCode.INVALID_ZIP,
                            message="ZIP contains unsafe paths",
                            status_code=400,
                            category=ErrorCategory.VALIDATION,
                            severity=ErrorSeverity.ERROR,
                        )

                # ------------------------------------------------------------------
                # Root Folder Detection
                # ------------------------------------------------------------------
                root_prefix = ""
                top_levels = {name.split("/")[0] for name in names if "/" in name}

                if len(top_levels) == 1:
                    candidate = list(top_levels)[0] + "/"
                    if any(n.startswith(candidate) for n in names):
                        root_prefix = candidate

                logger.info("Detected ZIP root", extra={"root_prefix": root_prefix})

                def exists(path: str) -> bool:
                    return f"{root_prefix}{path}" in names

                def read_text(path: str) -> Optional[str]:
                    full_path = f"{root_prefix}{path}"
                    if full_path in names:
                        return zip_ref.read(full_path).decode(errors="ignore").strip()
                    return None

                # ------------------------------------------------------------------
                # Validate Required Files
                # ------------------------------------------------------------------
                status_file = read_text("status.txt")
                if not status_file:
                    raise APIException(
                        error_code=ErrorCode.MISSING_ARTIFACTS,
                        message="Missing or empty status.txt in ZIP",
                        status_code=400,
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.ERROR,
                    )

                artifact_folder = "success" if status_file == "passed" else "failures"

                started_at = read_text("started_at.txt")
                finished_at = read_text("finished_at.txt")
                
                # ------------------------------------------------------------------
                # Extract Final Script (Root Level)
                # ------------------------------------------------------------------
                final_script_path = f"{root_prefix}final_script.py"

                if final_script_path not in names:
                    raise APIException(
                        error_code=ErrorCode.MISSING_ARTIFACTS,
                        message="Missing required final_script.py in ZIP",
                        status_code=400,
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.ERROR,
                        details={"expected_path": final_script_path},
                    )

                try:
                    final_script_data: str = (
                        zip_ref.read(final_script_path)
                        .decode(errors="ignore")
                        .strip()
                    )
                except Exception as exc:
                    raise APIException(
                        error_code=ErrorCode.MISSING_ARTIFACTS,
                        message="Unable to read final_script.py",
                        status_code=400,
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.ERROR,
                        details={"error": str(exc)},
                    )

                if not final_script_data:
                    raise APIException(
                        error_code=ErrorCode.MISSING_ARTIFACTS,
                        message="final_script.py is empty",
                        status_code=400,
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.ERROR,
                    )

                # ------------------------------------------------------------------
                # Extract Execution Video
                # ------------------------------------------------------------------
                video_folder_prefix = f"{root_prefix}{artifact_folder}/video/"
                video_data: Optional[bytes] = None
                video_path_found: Optional[str] = None

                for name in names:
                    if name.startswith(video_folder_prefix) and (
                        name.endswith(".mp4")
                        or name.endswith(".webm")
                        or name.endswith(".mov")
                    ):
                        video_path_found = name
                        break

                if not video_path_found:
                    raise APIException(
                        error_code=ErrorCode.MISSING_ARTIFACTS,
                        message="Missing execution video in ZIP",
                        status_code=400,
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.ERROR,
                        details={"expected_prefix": video_folder_prefix},
                    )

                try:
                    video_data = zip_ref.read(video_path_found)
                except Exception as exc:
                    raise APIException(
                        error_code=ErrorCode.MISSING_ARTIFACTS,
                        message="Unable to read execution video",
                        status_code=400,
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.ERROR,
                        details={"video_path": video_path_found, "error": str(exc)},
                    )

                if not video_data:
                    raise APIException(
                        error_code=ErrorCode.MISSING_ARTIFACTS,
                        message="Execution video is empty",
                        status_code=400,
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.ERROR,
                        details={"video_path": video_path_found},
                    )

                # ------------------------------------------------------------------
                # Extract Repair Report
                # ------------------------------------------------------------------
                repair_report_path = f"{root_prefix}repair_report.json"

                repair_report: Optional[Dict[str, Any]] = None

                if repair_report_path in names:
                    try:
                        raw_report = zip_ref.read(repair_report_path).decode(errors="ignore")
                        repair_report = json.loads(raw_report)

                        # ---------------------------------------------------------------
                        # Normalize Step IDs for HTML Reporter
                        # Example:
                        # 10__step_10_1997a082a4fb -> Step-10
                        # ---------------------------------------------------------------
                        repairs = repair_report.get("repairs", [])

                        for repair in repairs:
                            step_id = repair.get("step_id")

                            if step_id:
                                try:
                                    # Extract leading number before "__"
                                    step_number = step_id.split("__")[0]
                                    repair["step_id"] = f"Step-{step_number}"
                                except Exception:
                                    # fallback safe behavior
                                    repair["step_id"] = step_id

                    except Exception as exc:
                        raise APIException(
                            error_code=ErrorCode.MISSING_ARTIFACTS,
                            message="Invalid JSON in repair_report.json",
                            status_code=400,
                            category=ErrorCategory.VALIDATION,
                            severity=ErrorSeverity.ERROR,
                            details={"error": str(exc)},
                        )
                
                # ------------------------------------------------------------------
                # Extract Step Artifacts (ORDER-INDEPENDENT)
                # ------------------------------------------------------------------
                steps: List[Dict[str, Any]] = []

                for file_name in names:
                    if (
                        file_name.startswith(f"{root_prefix}{artifact_folder}/")
                        and file_name.endswith("step_summary.json")
                    ):
                        raw = zip_ref.read(file_name).decode(errors="ignore")
                        try:
                            step_json = json.loads(raw)
                        except Exception as exc:
                            raise APIException(
                                error_code=ErrorCode.MISSING_ARTIFACTS,
                                message=f"Invalid JSON in {file_name}",
                                status_code=400,
                                category=ErrorCategory.VALIDATION,
                                severity=ErrorSeverity.ERROR,
                                details={"error": str(exc)},
                            )

                        # ------------------------------------------------------------------
                        # HARD REQUIREMENT: step_index
                        # ------------------------------------------------------------------
                        if "step_index" not in step_json:
                            raise APIException(
                                error_code=ErrorCode.MISSING_ARTIFACTS,
                                message=f"Missing step_index in {file_name}",
                                status_code=400,
                                category=ErrorCategory.VALIDATION,
                                severity=ErrorSeverity.ERROR,
                            )

                        step_index = int(step_json["step_index"])

                        # ------------------------------------------------------------------
                        # Duration Calculation
                        # ------------------------------------------------------------------
                        execution_timestamp = step_json.get("duration_sec")

                        if execution_timestamp is None:
                            step_started = step_json.get("started_at")
                            step_ended = step_json.get("ended_at")

                            if step_started and step_ended:
                                try:
                                    start_dt = datetime.fromisoformat(
                                        step_started.replace("Z", "+00:00")
                                    )
                                    end_dt = datetime.fromisoformat(
                                        step_ended.replace("Z", "+00:00")
                                    )
                                    execution_timestamp = (
                                        end_dt - start_dt
                                    ).total_seconds()
                                except Exception:
                                    execution_timestamp = None

                        screenshot_path = file_name.replace(
                            "step_summary.json", "screenshot.png"
                        )

                        screenshot_data = (
                            zip_ref.read(screenshot_path)
                            if screenshot_path in names
                            else None
                        )

                        steps.append(
                            {
                                "step_index": step_index,
                                "summary": step_json,
                                "screenshot": screenshot_data,
                                "execution_timestamp": execution_timestamp,
                            }
                        )

                if not steps:
                    raise APIException(
                        error_code=ErrorCode.MISSING_ARTIFACTS,
                        message=f"No step artifacts found in {artifact_folder}",
                        status_code=400,
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.ERROR,
                    )

                # ------------------------------------------------------------------
                # CANONICAL ORDER FREEZE
                # ------------------------------------------------------------------
                steps.sort(key=lambda s: s["step_index"])

                indices = [s["step_index"] for s in steps]
                if indices != sorted(indices):
                    raise APIException(
                        error_code=ErrorCode.INTERNAL,
                        message="Step order corrupted during ZIP extraction",
                        status_code=500,
                        category=ErrorCategory.INTERNAL,
                        severity=ErrorSeverity.ERROR,
                        details={"indices": indices},
                    )

                logger.info(
                    "Successfully extracted artifacts",
                    extra={"step_count": len(steps), "status": status_file},
                )

                return {
                    "status": status_file,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "steps": steps,
                    "final_script": final_script_data,
                    "execution_video": video_data,
                    "repair_report": repair_report,
                }

        except zipfile.BadZipFile:
            raise APIException(
                error_code=ErrorCode.INVALID_ZIP,
                message="Invalid ZIP file format",
                status_code=400,
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.ERROR,
            )

        except APIException:
            raise

        except Exception as e:
            logger.error(
                "ZIP extraction failed",
                extra={"error_message": str(e)},
                exc_info=True,
            )
            raise APIException(
                error_code=ErrorCode.ZIP_EXTRACTION_FAILED,
                message="Failed to extract ZIP",
                status_code=500,
                category=ErrorCategory.INTERNAL,
                severity=ErrorSeverity.ERROR,
                details={"error": str(e)},
            )

        finally:
            try:
                if zip_path and zip_path.exists():
                    zip_path.unlink()
            except Exception:
                pass
