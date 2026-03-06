import asyncio
import random
from typing import Optional, Dict

from google import genai
from google.genai import types

from app.core.logger import get_logger
from app.core.errors import (
    APIException,
    ErrorCode,
    ErrorCategory,
    ErrorSeverity,
)
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class AIService:
    """Enterprise-grade AI Service using Gemini SDK (order-safe)."""

    def __init__(self):
        try:
            self.client = genai.Client(
                api_key=settings.GEMINI_API_KEY.get_secret_value()
            )
            self.model_name = settings.GEMINI_MODEL
            self.max_retries = 3
            self.timeout_seconds = 30
            self.max_concurrency = 5  # HARD LIMIT
            logger.info(
                "Gemini client initialized",
                extra={"model": self.model_name},
            )
        except Exception as e:
            logger.critical(
                "Failed to initialize Gemini client",
                extra={"error": str(e)},
            )
            raise APIException(
                error_code=ErrorCode.GEMINI_API_ERROR,
                message="Failed to initialize Gemini client",
                status_code=500,
                category=ErrorCategory.DEPENDENCY,
                severity=ErrorSeverity.CRITICAL,
                details={"error": str(e)},
            )

    # ------------------------------------------------------------------
    # INTERNAL: Gemini generation with retries + timeout
    # ------------------------------------------------------------------
    async def _generate(self, prompt: str) -> str:
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.models.generate_content,
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.4,
                            max_output_tokens=120,
                            top_p=0.9,
                            top_k=40,
                        ),
                    ),
                    timeout=self.timeout_seconds,
                )

                if not response or not response.text:
                    raise ValueError("Empty response from Gemini")

                return response.text.strip()

            except asyncio.TimeoutError as exc:
                last_error = exc
                logger.warning(
                    "Gemini request timed out",
                    extra={
                        "attempt": attempt,
                        "timeout_sec": self.timeout_seconds,
                    },
                )

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Gemini generation attempt failed",
                    extra={
                        "attempt": attempt,
                        "error": str(exc),
                    },
                )

            # Exponential backoff + jitter
            await asyncio.sleep((2 ** attempt) + random.random())

        logger.error(
            "Gemini generation failed after retries",
            extra={"error": str(last_error)},
        )

        raise APIException(
            error_code=ErrorCode.GEMINI_API_ERROR,
            message="Gemini generation failed after multiple attempts",
            status_code=502,
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.ERROR,
            retryable=True,
            details={"error": str(last_error)},
        )

    # ------------------------------------------------------------------
    # SINGLE STEP SUMMARY (unchanged behavior)
    # ------------------------------------------------------------------
    async def generate_step_summary(
        self,
        step_intent: str,
        step_status: str,
        duration: float,
    ) -> str:
        prompt = f"""
You are an automation reporting assistant.

Write a crisp 1–2 sentence summary (30–40 words max) describing this step:

Intent: {step_intent}
Status: {step_status}
Execution Time: {duration:.2f} seconds

Rules:
- Be factual
- No filler words
- No emojis
- No markdown
- No headings
- No commentary

Return only the summary text.
"""

        logger.debug(
            "Generating step summary",
            extra={"status": step_status, "duration": duration},
        )

        return await self._generate(prompt)

    # ------------------------------------------------------------------
    # ORDER-SAFE BATCH ENRICHMENT (THIS FIXES EVERYTHING)
    # ------------------------------------------------------------------
    async def enrich_steps_with_summaries(
        self,
        steps: list,
    ) -> Dict[int, str]:
        """
        Enrich steps concurrently WITHOUT breaking order.

        Returns:
            Dict[int, str]  -> { step_index: ai_summary }
        """

        semaphore = asyncio.Semaphore(self.max_concurrency)
        results: Dict[int, str] = {}

        async def enrich(step: dict):
            async with semaphore:
                summary = step.get("summary", {})
                step_index = summary.get("step_index")

                if step_index is None:
                    logger.error("Missing step_index during AI enrichment")
                    return

                ai_text = await self.generate_step_summary(
                    step_intent=summary.get("intent", ""),
                    step_status=summary.get("status", ""),
                    duration=summary.get("duration_sec") or 0.0,
                )

                results[int(step_index)] = ai_text

                logger.info(
                    "AI step summary generated",
                    extra={"step_index": step_index},
                )

        tasks = [enrich(step) for step in steps]
        await asyncio.gather(*tasks)

        return results

    # ------------------------------------------------------------------
    # OVERALL EXECUTION SUMMARY (safe, standalone)
    # ------------------------------------------------------------------
    async def generate_overall_description(
        self,
        total_steps: int,
        passed_steps: int,
        failed_steps: int,
        duration_sec: float,
    ) -> str:
        prompt = f"""
You are an expert test automation reporter.

Write a professional narrative (40–50 words) summarizing the execution flow.

Data:
- Total steps: {total_steps}
- Passed: {passed_steps}
- Failed: {failed_steps}
- Total duration: {duration_sec:.2f} seconds

Rules:
- Narrative tone
- No bullet points
- No emojis
- No markdown
- No headings
- No extra commentary

Return only the narrative.
"""

        logger.debug(
            "Generating overall execution description",
            extra={
                "total_steps": total_steps,
                "passed": passed_steps,
                "failed": failed_steps,
                "duration": duration_sec,
            },
        )

        return await self._generate(prompt)
