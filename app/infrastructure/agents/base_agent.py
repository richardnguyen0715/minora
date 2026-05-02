"""Base agent abstraction for the ingestion pipeline."""

from abc import ABC, abstractmethod

from loguru import logger

from app.domain.entities.pipeline import PipelineContext


class BaseAgent(ABC):
    """
    Base class for all pipeline agents.

    Provides:
    - Structured logging (start/success/failure)
    - Error handling with context update
    - Consistent interface for orchestrator
    """

    name: str = "base"

    async def run(self, context: PipelineContext) -> PipelineContext:
        """
        Execute the agent with logging and error handling.

        Args:
            context (PipelineContext): Current pipeline context.

        Returns:
            PipelineContext: Updated pipeline context.
        """
        logger.info(
            f"agent_{self.name}_started",
            extra={
                "agent": self.name,
                "source_id": context.source_id,
                "status": context.status,
            },
        )

        try:
            context = await self._execute(context)
            logger.info(
                f"agent_{self.name}_completed",
                extra={
                    "agent": self.name,
                    "source_id": context.source_id,
                    "status": context.status,
                },
            )
        except Exception as exc:
            context.error = str(exc)
            context.error_stage = self.name
            context.status = "failed"
            logger.error(
                f"agent_{self.name}_failed",
                extra={
                    "agent": self.name,
                    "source_id": context.source_id,
                    "error": str(exc),
                },
            )

        return context

    @abstractmethod
    async def _execute(self, context: PipelineContext) -> PipelineContext:
        """
        Agent-specific execution logic.

        Args:
            context (PipelineContext): Current pipeline context.

        Returns:
            PipelineContext: Updated pipeline context.
        """
        pass
