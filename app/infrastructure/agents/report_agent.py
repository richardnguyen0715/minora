"""Report agent: formats pipeline results into a Telegram-friendly message."""

from app.domain.entities.pipeline import PipelineContext
from app.infrastructure.agents.base_agent import BaseAgent


class ReportAgent(BaseAgent):
    """Format pipeline results into a human-readable Telegram report."""

    name = "report"

    def __init__(self, max_summary_length: int = 500) -> None:
        self.max_summary_length = max_summary_length

    async def _execute(self, context: PipelineContext) -> PipelineContext:
        # Report is generated via format_report, no context mutation needed
        return context

    def format_report(self, context: PipelineContext) -> str:
        """
        Format pipeline context into Telegram message.

        Args:
            context (PipelineContext): Completed pipeline context.

        Returns:
            str: Formatted report string.
        """
        if context.status == "failed":
            return (
                f"IMPORT FAILED at stage: {context.error_stage}\n"
                f"Error: {context.error}\n"
                f"Source: {context.url}"
            )

        lines = []
        extract = context.extract_result
        parse = context.parse_result

        # Title
        title = (parse.title if parse else None) or "Untitled"
        lines.append(f"IMPORT COMPLETE: {title}")
        lines.append(f"ID: {context.source_id}")
        lines.append("")

        # Summary
        if extract and extract.summary:
            summary = extract.summary
            if len(summary) > self.max_summary_length:
                summary = summary[: self.max_summary_length] + "..."
            lines.append("-- Summary --")
            lines.append(summary)
            lines.append("")

        # Key points
        if extract and extract.key_points:
            lines.append("-- Key Points --")
            for point in extract.key_points[:7]:
                lines.append(f"- {point}")
            lines.append("")

        # Insights
        if context.insight_result and context.insight_result.insights:
            lines.append("-- Insights --")
            for insight in context.insight_result.insights[:3]:
                lines.append(f"- ({insight.impact}) {insight.text}")
            lines.append("")

        # Concepts
        if extract and extract.concepts:
            lines.append(f"-- Concepts: {', '.join(extract.concepts[:10])}")
            lines.append("")

        # Stats
        concept_result = context.concept_result
        if concept_result:
            lines.append(f"Concepts: {len(concept_result.created)} new, {len(concept_result.linked)} linked")

        lines.append(f"Link: {context.url}")

        return "\n".join(lines)
