Bạn đang đi đúng hướng khi nghĩ theo **multi-agent ingestion pipeline**. Nhưng nếu không thiết kế rõ **orchestration + contract giữa các agent**, hệ thống sẽ nhanh chóng rối và khó debug.

Tôi sẽ thiết kế cho bạn một pipeline hoàn chỉnh, production-ready, có thể:

* dùng Gemini API
* dễ thay LLM
* mở rộng multi-agent
* tích hợp clean với command system bạn đã build

---

# 1. Tổng thể kiến trúc

```text
Telegram (/import url)
        ↓
Command Handler
        ↓
Ingestion Orchestrator  ← (core)
        ↓
Task Queue (async)
        ↓
Multi-Agent Pipeline
        ↓
Storage (Markdown + DB)
        ↓
Notifier (Telegram reply)
```

## 1.1 High-level Flow

```text
User: /import <url>

→ Telegram Bot
→ Command Handler
→ Ingestion Orchestrator
    → Fetch Agent
    → Parse Agent
    → Extract Agent (LLM)
    → Concept Agent`
    → Insight Agent
    → Storage Agent
    → Report Agent
→ Telegram reply
```

# 1.2 Kiến trúc tổng thể (multi-agent)

```text
                ┌────────────────────┐
                │ Telegram Interface │
                └─────────┬──────────┘
                          ↓
                ┌────────────────────┐
                │ Command Use Case   │
                └─────────┬──────────┘
                          ↓
                ┌────────────────────┐
                │ Orchestrator Agent │
                └──────┬─────┬───────┘
                       ↓     ↓
        ┌──────────────┘     └──────────────┐
        ↓                                   ↓
 Fetch Agent                        Parse Agent
        ↓                                   ↓
        └──────────────┬────────────────────┘
                       ↓
                Extract Agent (LLM)
                       ↓
        ┌──────────────┴──────────────┐
        ↓                             ↓
 Concept Agent                Insight Agent
        ↓                             ↓
        └──────────────┬──────────────┘
                       ↓
                Storage Agent
                       ↓
                Report Agent
                       ↓
                Telegram Reply
```

---


---

# 2. Nguyên tắc thiết kế

### 2.1 Agent = stateless, chuyên biệt

Mỗi agent chỉ làm 1 việc:

* ParserAgent → lấy nội dung
* SummarizerAgent → tóm tắt
* ConceptExtractorAgent → trích xuất concept
* EntityExtractorAgent → trích xuất entity
* InsightAgent → generate insight

---

### 2.2 Orchestrator = brain

* điều phối agent
* quản lý state
* retry / fallback

---

### 2.3 LLM abstraction layer

Không gọi trực tiếp Gemini → phải có adapter

---

# 3. Command flow (/import)

```text
/import https://...
        ↓
HandleCommandUseCase
        ↓
ImportUseCase
        ↓
IngestionOrchestrator.start()
```

---

# 4. Ingestion Orchestrator (core design)

```python
class IngestionOrchestrator:

    def __init__(self, agents, storage, notifier):
        self.agents = agents
        self.storage = storage
        self.notifier = notifier

    async def run(self, url, user_id, chat_id):

        # STEP 1: create source
        source = self.storage.create_source(url, user_id)

        # STEP 2: parse content
        content = await self.agents.parser.run(url)

        # STEP 3: summarize
        summary = await self.agents.summarizer.run(content)

        # STEP 4: extract knowledge
        concepts = await self.agents.concept_extractor.run(content)
        entities = await self.agents.entity_extractor.run(content)

        # STEP 5: insight
        insight = await self.agents.insight.run(summary)

        # STEP 6: save
        self.storage.update_source(
            source.id,
            summary=summary,
            concepts=concepts,
            entities=entities
        )

        # STEP 7: notify user
        await self.notifier.send(chat_id, summary)

        return source
```

---

# 5. Multi-agent design

## 5.1 Base Agent interface

```python
class BaseAgent:
    async def run(self, input_data):
        raise NotImplementedError
```

---

## 5.2 Gemini Adapter (LLM abstraction)

```python
class LLMClient:

    def __init__(self, provider="gemini"):
        self.provider = provider

    async def generate(self, prompt):
        if self.provider == "gemini":
            return await call_gemini(prompt)
        elif self.provider == "openai":
            return await call_openai(prompt)
```

---

## 5.3 Summarizer Agent

```python
class SummarizerAgent(BaseAgent):

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def run(self, content: str):

        prompt = f"""
        Summarize the following content:

        {content}

        Output:
        - concise summary
        - key points (bullet)
        """

        return await self.llm.generate(prompt)
```

---

## 5.4 Concept Extractor Agent

```python
class ConceptExtractorAgent(BaseAgent):

    async def run(self, content):

        prompt = """
        Extract key concepts from the text.

        Output JSON:
        {
          "concepts": ["..."]
        }
        """

        return await self.llm.generate(prompt)
```

---

## 5.5 Insight Agent

```python
class InsightAgent(BaseAgent):

    async def run(self, summary):

        prompt = """
        Generate high-value insights from this summary.

        Focus on:
        - implications
        - non-obvious ideas
        """

        return await self.llm.generate(prompt)
```

---

# 6. Parser Agent (không dùng LLM)

Quan trọng: không dùng LLM để crawl

```python
class ParserAgent:

    async def run(self, url):

        html = await fetch(url)

        text = extract_main_content(html)

        return text
```

---

# 7. Storage layer

## 7.1 Markdown writer

```python
class MarkdownStorage:

    def create_source(self, url, user_id):
        # generate id
        # create file
        pass

    def update_source(self, id, **kwargs):
        # update frontmatter
        pass
```

---

## 7.2 Metadata DB sync

* insert node
* insert edges (concepts, entities)

---

# 8. Telegram response design

Không trả raw summary

→ trả format:

```text
[SUMMARY]

<short summary>

[KEY POINTS]
- ...
- ...

[INSIGHT]
- ...

[LINK]
<url>
```

---

# 9. Async execution (quan trọng)

Không block command

```python
# trong command handler
asyncio.create_task(
    orchestrator.run(url, user_id, chat_id)
)
```

→ trả ngay:

```text
[OK] Processing your link...
```

---

# 10. Scaling architecture

## Khi lớn hơn:

```text
API
 ↓
Queue (Redis / Kafka)
 ↓
Worker pool
 ↓
Agents
```

---

# 11. Error handling

* retry per agent
* fallback model
* mark status = failed

---

# 12. Advanced (nên làm)

## 12.1 Parallel agents

```python
summary, concepts, entities = await asyncio.gather(
    summarizer.run(content),
    concept.run(content),
    entity.run(content)
)
```

---

## 12.2 Caching

* hash(url) → skip reprocess

---

## 12.3 Deduplication

* nếu source tồn tại → update

---

# 13. Kết nối với knowledge system của bạn

Pipeline sẽ:

```text
Source → Concept → Insight → Graph
```

→ đúng với schema bạn đã thiết kế

---

# 14. Kết luận

Pipeline chuẩn cần:

* Orchestrator trung tâm
* Agent chuyên biệt (single responsibility)
* LLM abstraction layer
* Async + queue
* Structured output (JSON)
* Tight integration với knowledge graph

---

# Nếu bạn muốn đi sâu hơn

Tôi có thể tiếp tục:

* Viết full code runnable (FastAPI + worker + Redis)
* Thiết kế prompt chuẩn JSON (không lỗi parse)
* Hoặc build agent framework giống LangGraph nhưng lightweight hơn
