# 1. Nguyên tắc thiết kế

### 1. Structured > Free text

- Mọi note đều có **frontmatter chuẩn hóa**
    
- Nội dung chính vẫn là markdown (để đọc dễ)
    

---

### 2. Atomic + Composable

- Không nhồi mọi thứ vào 1 note
    
- Tách:
    
    - Source
        
    - Concept
        
    - Insight
        

---

### 3. Graph-first mindset

- Luôn dùng:
    
    - `[[wikilink]]`
        
    - `tags`
        
    - `id`
        

---

### 4. AI-friendly

- Dễ parse bằng script
    
- Dễ embedding / retrieval
    

---

# 2. Folder Structure (Production-ready)

```text
/knowledge
  /sources        # raw ingestion từ link
  /concepts       # khái niệm
  /insights       # insight rút ra
  /summaries      # summary tổng hợp nhiều nguồn
  /entities       # người, công ty, tool
  /tasks          # action items
```

---

# 3. Core Schema (quan trọng nhất)

## 3.1 Source Note (điểm vào hệ thống)

```md
---
id: src_20260430_001
type: source
title: ...
url: ...
platform: tiktok | facebook | web | youtube
author: ...
created_at: 2026-04-30
language: en
tags: [ai, marketing]

status: processed
confidence: 0.85

related_concepts: []
related_sources: []
---

## Summary
...

## Key Points
- ...

## Extracted Links
- ...

## Raw Notes
...
```

### Vai trò:

- lưu dữ liệu ingest
    
- trace nguồn
    

---

## 3.2 Concept Note (cực kỳ quan trọng)

```md
---
id: concept_llm_finetuning
type: concept
name: LLM Finetuning
aliases: [fine-tuning, model adaptation]

domain: ai
level: intermediate

related_concepts: []
related_sources: []
---

## Definition
...

## Explanation
...

## Examples
...

## Related
- [[concept_prompt_engineering]]
```

### Vai trò:

- node chính trong knowledge graph
    

---

## 3.3 Insight Note

```md
---
id: insight_20260430_01
type: insight
source: [[src_20260430_001]]

confidence: 0.7
impact: high

tags: [growth, ai]
---

## Insight
...

## Why it matters
...

## Applicability
...
```

### Vai trò:

- nơi “giá trị thực” nằm
    
- không phải copy content, mà là hiểu
    

---

## 3.4 Summary Note (multi-source)

```md
---
id: summary_llm_trends_2026
type: summary

sources:
  - [[src_20260430_001]]
  - [[src_20260429_002]]

topics: [llm, ai trends]
---

## Overview
...

## Key Themes
- ...

## Contradictions
- ...

## Takeaways
...
```

---

## 3.5 Entity Note (optional nhưng nên có)

```md
---
id: entity_openai
type: entity
name: OpenAI

category: company
---

## Description
...

## Related
- [[concept_llm]]
```

---

# 4. Linking Strategy (cốt lõi để build graph)

## 4.1 Wikilinks

Luôn dùng:

```md
[[concept_llm]]
[[entity_openai]]
```

---

## 4.2 Typed Relationships

Trong frontmatter:

```yaml
related_concepts:
  - concept_llm
  - concept_rag

related_sources:
  - src_20260430_001
```

---

## 4.3 Bi-directional linking (quan trọng)

Agent nên tự động:

- update cả 2 phía
    

---

# 5. Tagging Strategy

Không lạm dụng tag.

### Chỉ dùng cho:

- domain: ai, marketing, finance
    
- content-type: tutorial, news, opinion
    
- priority
    

Ví dụ:

```yaml
tags: [ai, tutorial]
```

---

# 6. Chuẩn hóa ID (rất quan trọng)

### Format:

```text
src_YYYYMMDD_xxx
concept_<slug>
insight_YYYYMMDD_xx
summary_<topic>
```

### Lý do:

- dễ query
    
- tránh duplicate
    
- dễ sync
    

---

# 7. AI Interaction Layer (thiết kế cho tương lai)

Schema trên giúp bạn:

## 7.1 Embedding dễ dàng

- embed:
    
    - Summary
        
    - Concept Definition
        
    - Insight
        

---

## 7.2 Retrieval

Query kiểu:

- “tất cả insight về marketing”
    
- “concept liên quan LLM”
    

---

## 7.3 Agent có thể:

- update note
    
- merge concept
    
- detect duplicate
    

---

# 8. Automation Rules (nên implement)

## Rule 1: Khi ingest source

- tạo Source note
    
- extract concept → tạo/append Concept
    

---

## Rule 2: Khi summary xong

- tạo Insight
    
- link tới Source
    

---

## Rule 3: Deduplication

- nếu concept tồn tại:
    
    - không tạo mới
        
    - chỉ append
        

---

# 9. Mở rộng: Knowledge Graph

Với schema này, bạn có thể:

- build graph DB (Neo4j sau này)
    
- hoặc dùng Obsidian graph view
    

Nodes:

- concept
    
- source
    
- insight
    

Edges:

- references
    
- derived_from
    
- related_to
    

---

# 10. Ví dụ flow thực tế

```text
User gửi link

→ tạo src_20260430_001

→ extract:
   - [[concept_llm]]
   - [[concept_rag]]

→ tạo insight_20260430_01

→ link:
   insight → source
   source → concept
```

---

# 11. Sai lầm cần tránh

1. Không có schema → sau 1 tháng là rác
    
2. Nhồi tất cả vào 1 note
    
3. Không dùng wikilink
    
4. Không có ID
    
5. Không tách concept / insight
    

---

# 12. Tóm lại

Schema tốt cần đạt:

- đọc được (human-friendly)
    
- parse được (machine-friendly)
    
- link được (graph-ready)
    
- mở rộng được (future-proof)