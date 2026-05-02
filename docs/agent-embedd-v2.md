Bạn đang đi đúng hướng: bài toán này không phải “call LLM rồi trả kết quả”, mà là một **pipeline ingestion + multi-agent orchestration**. Nếu thiết kế đúng từ đầu, bạn sẽ có một hệ thống gần như RAG-ready + knowledge graph builder.

Tôi sẽ thiết kế theo 4 lớp:

1. **Command Layer (Telegram trigger)**
2. **Orchestrator (Agent Controller)**
3. **Worker Agents (multi-agent, chuyên biệt)**
4. **Storage Layer (DB + Markdown)**

---

# 1. High-level Flow

```text
User: /import <url>

→ Telegram Bot
→ Command Handler
→ Ingestion Orchestrator
    → Fetch Agent
    → Parse Agent
    → Extract Agent (LLM)
    → Concept Agent
    → Insight Agent
    → Storage Agent
    → Report Agent
→ Telegram reply
```

---

# 2. Kiến trúc tổng thể (multi-agent)

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

# 3. Command Layer

Bạn đã có `/import`, cần chuẩn hóa:

```text
/import <url>
/import text:<raw text>
/import file:<file_id>
```

---

# 4. Orchestrator (core của hệ thống)

## Vai trò:

* điều phối agent
* quản lý state
* retry / fail-safe

---

## Pseudo-code

```python
class IngestionOrchestrator:

    async def run(self, input_data):
        source = await FetchAgent.run(input_data)

        parsed = await ParseAgent.run(source)

        extracted = await ExtractAgent.run(parsed)

        concepts = await ConceptAgent.run(extracted)

        insights = await InsightAgent.run(extracted)

        await StorageAgent.run(
            source, parsed, extracted, concepts, insights
        )

        report = await ReportAgent.run(extracted, insights)

        return report
```

---

# 5. Agent Design (multi-agent đúng nghĩa)

## 5.1 Fetch Agent (không dùng LLM)

### Input:

* URL

### Output:

```json
{
  "html": "...",
  "status": 200
}
```

---

## 5.2 Parse Agent

### Nhiệm vụ:

* extract main content
* remove noise

### Tool:

* newspaper3k / readability

---

### Output:

```json
{
  "title": "...",
  "content": "...",
  "author": "...",
  "published_at": "...",
  "language": "en"
}
```

---

## 5.3 Extract Agent (LLM - GEMINI)

### Đây là agent quan trọng nhất

### Prompt design:

```text
You are an expert content analyst.

Extract structured information from the article.

Return JSON with:
- summary (short, 3-5 sentences)
- key_points (5-10 bullet points)
- concepts (technical concepts)
- entities (people, companies, tools)
- topics (high-level tags)
```

---

### Output:

```json
{
  "summary": "...",
  "key_points": [...],
  "concepts": ["llm", "rag"],
  "entities": ["OpenAI"],
  "topics": ["ai", "ml"]
}
```

---

## 5.4 Concept Agent

### Nhiệm vụ:

* map `concepts` → existing concept
* hoặc tạo mới

---

```python
if concept_exists(name):
    link()
else:
    create_concept()
```

---

## 5.5 Insight Agent (LLM)

### Prompt:

```text
You are a strategic thinker.

Given this article, generate insights:
- what is non-obvious?
- what can be applied?
- what is the implication?
```

---

### Output:

```json
{
  "insights": [
    {
      "text": "...",
      "impact": "high"
    }
  ]
}
```

---

## 5.6 Storage Agent

### Ghi:

* Markdown file (source)
* DB:

  * nodes
  * edges
  * embeddings

---

## 5.7 Report Agent

### Output cho Telegram:

```text
[SUMMARY]
...

[KEY POINTS]
- ...
- ...

[INSIGHT]
- ...

[CONCEPTS]
llm, rag, agents
```

---

# 6. GEMINI Integration (pluggable LLM)

## Interface chuẩn

```python
class LLMProvider:

    async def generate(self, prompt: str) -> dict:
        pass
```

---

## Gemini implementation

```python
class GeminiProvider(LLMProvider):
    async def generate(self, prompt):
        # call Gemini API
        return response
```

---

## Swap LLM dễ dàng:

```python
llm = GeminiProvider()
# hoặc
llm = OpenAIProvider()
```

---

# 7. Queue + Worker (production)

Bạn nên thêm:

```text
API → Queue → Worker Agents
```

---

## Queue:

* Redis / Celery

---

## Lợi ích:

* retry
* scale
* async processing

---

# 8. Telegram Response Strategy

### 2-phase response (rất nên làm)

---

## Phase 1 (ngay lập tức)

```text
[INFO] Processing your link...
```

---

## Phase 2 (sau khi xong)

```text
[OK] Summary:
...

Key Points:
...

Insights:
...
```

---

# 9. Error Handling

* Fetch fail → retry
* Parse fail → fallback LLM
* LLM fail → degrade gracefully

---

# 10. Observability

Log theo từng stage:

```text
ingest_started
fetch_done
parse_done
extract_done
storage_done
```

---

# 11. Mở rộng tương lai

Với design này bạn có thể:

* multi-source ingestion
* real-time knowledge graph
* auto-learning system
* agent collaboration

---

# 12. Tóm lại

Pipeline chuẩn của bạn:

* Event-driven
* Multi-agent
* LLM pluggable
* Storage tách biệt
* Graph-ready

---

# Nếu bạn muốn đi tiếp

Tôi có thể:

* Viết full code skeleton (FastAPI + worker + agents)
* Thiết kế prompt chuẩn cho Gemini (JSON strict)
* Hoặc build luôn pipeline async (Redis + Celery + retry + monitoring)

Bạn muốn đi theo hướng **prototype nhanh** hay **production ngay từ đầu**?
