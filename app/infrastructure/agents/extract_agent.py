"""Extract agent: uses LLM to extract structured information from content."""

from loguru import logger

from app.domain.entities.pipeline import ExtractResult, PipelineContext
from app.infrastructure.agents.base_agent import BaseAgent
from app.infrastructure.llm.provider import LLMProvider


class ExtractAgent(BaseAgent):
    """
    LLM-powered content extraction.

    Sends parsed content to the LLM and extracts:
    - Summary (3-5 sentences)
    - Key points (bullet points)
    - Concepts (technical concepts/terms)
    - Entities (people, companies, tools)
    - Topics (high-level tags)
    """

    name = "extract"

    def __init__(
        self,
        llm: LLMProvider,
        max_key_points: int = 10,
        max_concepts: int = 15,
        max_entities: int = 10,
    ) -> None:
        """
        Initialize extract agent.

        Args:
            llm (LLMProvider): LLM provider for content analysis.
            max_key_points (int): Maximum key points to extract.
            max_concepts (int): Maximum concepts to extract.
            max_entities (int): Maximum entities to extract.
        """
        self.llm = llm
        self.max_key_points = max_key_points
        self.max_concepts = max_concepts
        self.max_entities = max_entities

    async def _execute(self, context: PipelineContext) -> PipelineContext:
        """
        Extract structured information using LLM.

        Args:
            context (PipelineContext): Pipeline context with parse_result.

        Returns:
            PipelineContext: Updated with extract_result and status=extracted.
        """
        if not context.parse_result:
            raise ValueError("No parse result available for extraction")

        content = context.parse_result.content
        title = context.parse_result.title

        # Truncate content for LLM prompt to stay within token limits
        max_prompt_content = 30000
        if len(content) > max_prompt_content:
            content = content[:max_prompt_content]

        prompt = self._build_prompt(title, content)
        result = await self.llm.generate(prompt)

        context.extract_result = ExtractResult(
            summary=str(result.get("summary", "")),
            key_points=self._safe_list(result.get("key_points", []), self.max_key_points),
            concepts=self._safe_list(result.get("concepts", []), self.max_concepts),
            entities=self._safe_list(result.get("entities", []), self.max_entities),
            topics=self._safe_list(result.get("topics", [])),
        )
        context.status = "extracted"

        logger.info(
            "extract_complete",
            extra={
                "source_id": context.source_id,
                "concepts_count": len(context.extract_result.concepts),
                "entities_count": len(context.extract_result.entities),
                "key_points_count": len(context.extract_result.key_points),
            },
        )

        return context

    def _build_prompt(self, title: str, content: str) -> str:
        """
        Build the extraction prompt for the LLM.

        Args:
            title (str): Article title.
            content (str): Article content.

        Returns:
            str: Formatted prompt.
        """
        return f"""You are an expert content analyst. Analyze the following article and extract structured information.

Title: {title}

Content:
{content}

Return a JSON object with exactly these fields:
{{
  "summary": "A concise summary in 3-5 sentences",
  "key_points": ["up to {self.max_key_points} key points as bullet strings"],
  "concepts": ["up to {self.max_concepts} technical concepts/terms mentioned (lowercase, normalized)"],
  "entities": ["up to {self.max_entities} named entities: people, companies, tools, products"],
  "topics": ["3-7 high-level topic tags (lowercase)"]
}}

Rules:
- summary must be informative and standalone
- key_points should capture the most important takeaways
- concepts should be normalized (e.g., "large language model" not "LLMs")
- entities should be proper names only
- topics should be broad categories
- All values must be strings
- Return ONLY the JSON object, no additional text"""

    @staticmethod
    def _safe_list(value, max_items: int = 20) -> list[str]:
        """
        Safely convert LLM output to a list of strings.

        Args:
            value: Raw value from LLM response.
            max_items (int): Maximum items to keep.

        Returns:
            list[str]: Cleaned list of strings.
        """
        if not isinstance(value, list):
            return []
        result = [str(item).strip() for item in value if item and str(item).strip()]
        return result[:max_items]
