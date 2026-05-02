Hiện trạng của bạn đang đúng về mặt “ingestion”, nhưng **chưa đạt chuẩn cho pipeline tự động (AI extraction + graph building)**.

Vấn đề chính:

* Metadata còn quá “raw ingestion”
* Thiếu phân tầng trạng thái xử lý
* Không chuẩn hóa field phục vụ downstream (parser, extractor, embedding)
* `metadata` đang bị nhồi chung → khó query

---

# 1. Nguyên tắc refactor Source Note

Source không chỉ là “lưu link”, mà là:

> **Entry point cho toàn bộ pipeline: extract → concept → insight → graph**

Vì vậy schema cần:

1. Phân tách rõ:

   * ingestion
   * processing
   * extraction
2. Chuẩn hóa field để:

   * query DB
   * trigger automation
3. Không nhồi nested metadata tùy tiện

---

# 2. Schema Source mới (production-ready)

## Refactor đề xuất

```md
---
id: src_20260502_medium_9307d879
type: source

title: (auto-fill sau khi crawl)
slug: src_20260502_medium_9307d879

# ===== CORE METADATA =====
url: https://www.medium.com/share/p/1DJysksha/
platform: medium
author: null
language: en

# ===== INGESTION =====
ingested_at: 2026-05-02T02:19:17Z
ingested_by: user_7283872301
source_type: article  # article | video | tweet | thread

# ===== PROCESSING STATE =====
status: pending  # pending | parsed | extracted | completed | failed

# ===== CONTENT METADATA =====
title_extracted: null
summary: null

# ===== EXTRACTION OUTPUT =====
key_points: []
entities: []
concept_candidates: []

# ===== LINKING =====
related_concepts: []
related_sources: []

# ===== SYSTEM =====
confidence: 1.0
hash: 37fa85...
file_path: knowledge/sources/2026/05/src_20260502_medium_9307d879.md

tags: [medium, imported]
---
```

---

# 3. Những thay đổi QUAN TRỌNG

## 3.1 Bỏ `metadata` nested

```yaml
metadata:
  url: ...
```

→ sai hướng

---

### Thay bằng flat fields:

```yaml
url:
platform:
author:
```

→ dễ query trong DB

---

## 3.2 Thêm processing pipeline state

```yaml
status: pending
```

### Lifecycle:

```text
pending → parsed → extracted → completed
```

→ cực kỳ quan trọng để automation chạy đúng bước

---

## 3.3 Tách ingestion vs extraction

| Layer      | Field                |
| ---------- | -------------------- |
| ingestion  | url, platform        |
| parsing    | title_extracted      |
| extraction | key_points, concepts |

---

## 3.4 Thêm `concept_candidates`

```yaml
concept_candidates:
  - llm
  - rag
```

→ để agent xử lý:

* match existing concept
* hoặc tạo concept mới

---

## 3.5 Thêm `entities`

```yaml
entities:
  - entity_openai
  - entity_google
```

→ giúp build graph mạnh hơn

---

# 4. Nội dung markdown body (refactor)

Hiện tại bạn đang có:

```md
# Source from medium.com

Source URL: ...
```

→ quá nghèo thông tin

---

## Refactor body:

```md
# {{title_extracted or title}}

## Summary
(auto-filled by parser)

## Key Points
- ...

## Extracted Concepts
- [[concept_llm]]
- [[concept_rag]]

## Entities
- [[entity_openai]]

## Raw Content
(optional / truncated)
```

---

# 5. Automation pipeline (quan trọng nhất)

Khi ingest link:

---

## STEP 1 — ingest

Tạo file:

```yaml
status: pending
```

---

## STEP 2 — parser job

* crawl content
* extract:

  * title
  * text
  * language

→ update:

```yaml
status: parsed
title_extracted: ...
```

---

## STEP 3 — extraction job (AI)

* summary
* key_points
* concept_candidates
* entities

→ update:

```yaml
status: extracted
```

---

## STEP 4 — linking

* map concept_candidates → concept
* tạo edges

→ update:

```yaml
status: completed
```

---

# 6. Mapping sang metadata DB

Từ file này, bạn sẽ insert:

### nodes

```text
id = src_20260502_medium_9307d879
type = source
```

---

### edges

```text
source → concept
source → entity
```

---

### tags

```text
medium
imported
```

---

# 7. Những field bạn NÊN thêm (advanced)

## 7.1 content_hash vs file_hash

```yaml
content_hash: ...
```

→ detect content change, không phải file change

---

## 7.2 priority

```yaml
priority: high
```

→ queue xử lý

---

## 7.3 quality_score

```yaml
quality_score: 0.82
```

→ ranking source

---

# 8. Version tối giản (nếu bạn muốn lean)

Nếu chưa cần full pipeline:

```yaml
url:
platform:
status:
summary:
concept_candidates:
```

---

# 9. Sai lầm hiện tại của bạn

### 1. Treat source như static note

→ sai, nó là pipeline entry

---

### 2. Không có processing state

→ không automation được

---

### 3. metadata nested

→ query rất khó

---

### 4. Không chuẩn bị cho extraction

→ phải refactor sau (rất đau)

---

# 10. Kết luận

Schema đúng cho Source phải:

* Flat, queryable
* Có lifecycle state
* Chuẩn bị cho AI extraction
* Tách ingestion vs processing vs knowledge