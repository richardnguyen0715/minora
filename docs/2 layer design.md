Ý tưởng tách **metadata DB** và **markdown file storage** là đúng hướng — thực tế nhiều hệ thống knowledge production-grade (Obsidian + indexer, Notion-like backend, hay RAG pipelines) đều làm kiểu này.

Nhưng để hệ thống **consistent + queryable + scalable**, bạn cần thiết kế metadata layer như một **index + graph layer**, không chỉ là “lưu frontmatter”.

Tôi sẽ đi thẳng vào 3 phần:

---

# 1. Nguyên tắc phân tách 2 layer

## Layer 1 — Metadata DB (minira.db)

Không lưu nội dung dài. Chỉ lưu:

* index
* relationship
* query optimization
* state

→ đóng vai trò **source of truth cho hệ thống**

---

## Layer 2 — Markdown Files

* Lưu nội dung human-readable
* Là canonical content
* Có thể sync Git / Obsidian / local

---

# 2. Metadata cần lưu (thiết kế chuẩn)

Bạn nên thiết kế theo dạng **normalized schema + graph-aware**

---

## 2.1 Core Table: `nodes`

```sql
nodes (
    id TEXT PRIMARY KEY,
    type TEXT,              -- source | concept | insight | summary | entity
    title TEXT,
    slug TEXT,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP,

    status TEXT,            -- draft | processed | archived
    confidence REAL,

    file_path TEXT,         -- link tới markdown file

    hash TEXT               -- để detect change
)
```

---

## 2.2 Relationships (quan trọng nhất)

```sql
edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    from_id TEXT,
    to_id TEXT,
    
    type TEXT,  -- related_concept | derived_from | references
    
    weight REAL DEFAULT 1.0,
    
    created_at TIMESTAMP
)
```

→ Đây là backbone để sau này build graph

---

## 2.3 Tags

```sql
tags (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE
)

node_tags (
    node_id TEXT,
    tag_id INTEGER
)
```

---

## 2.4 Embeddings (AI-ready)

```sql
embeddings (
    node_id TEXT,
    chunk_index INTEGER,
    vector BLOB
)
```

---

## 2.5 Full-text search (optional nhưng nên có)

```sql
fts_index (
    node_id TEXT,
    content TEXT
)
```

→ để query nhanh không cần load file

---

## 2.6 Extra metadata theo type

### Source-specific

```sql
sources (
    node_id TEXT PRIMARY KEY,
    url TEXT,
    platform TEXT,
    author TEXT,
    language TEXT
)
```

---

### Concept-specific

```sql
concepts (
    node_id TEXT PRIMARY KEY,
    domain TEXT,
    level TEXT
)
```

---

### Insight-specific

```sql
insights (
    node_id TEXT PRIMARY KEY,
    impact TEXT
)
```

---

# 3. File system design (real-file layer)

Bạn đã đúng direction, nhưng cần chuẩn hóa hơn:

---

## 3.1 Folder structure (refined)

```text
/knowledge
  /sources/
    2026/
      04/
        src_20260430_001.md

  /concepts/
    ai/
      concept_llm.md
      concept_rag.md

  /insights/
    2026/
      04/
        insight_20260430_01.md

  /summaries/
    llm/
      summary_llm_trends_2026.md

  /entities/
    company/
      entity_openai.md

  /tasks/
```

---

## 3.2 Naming rule (rất quan trọng)

* File name = `id.md`
* Không dùng title làm filename

```text
concept_llm.md
src_20260430_001.md
```

---

## 3.3 Frontmatter = single source of truth (partial)

Markdown vẫn giữ:

* id
* type
* lightweight metadata

Nhưng:

* **relationships → DB**
* **embedding → DB**

---

# 4. Sync strategy (cốt lõi để tránh chaos)

Bạn cần 1 sync engine:

---

## 4.1 File → DB

Khi file thay đổi:

* parse frontmatter
* update `nodes`
* update `edges`
* update `tags`

---

## 4.2 DB → File

Khi agent update:

* regenerate frontmatter
* update markdown file

---

## 4.3 Hash-based change detection

```python
file_hash = sha256(content)
```

→ nếu không đổi → skip

---

# 5. Relationship mapping (từ markdown → DB)

Ví dụ:

```md
related_concepts:
  - concept_llm
```

→ convert thành:

```text
concept_A --related--> concept_llm
```

---

Wikilink:

```md
[[concept_llm]]
```

→ parse → insert edge:

```text
current_node --references--> concept_llm
```

---

# 6. Query capability bạn sẽ có

Với schema này, bạn có thể:

---

## 6.1 Graph query

* “mọi insight liên quan LLM”
* “source nào generate insight này”

---

## 6.2 Hybrid search

* vector similarity + metadata filter

---

## 6.3 Timeline

* insight theo thời gian

---

# 7. Những thứ KHÔNG nên lưu trong DB

* full markdown content (trừ FTS)
* raw note dài
* duplicated data từ file

---

# 8. Sai lầm phổ biến

### 1. DB chỉ là mirror của file

→ sai, DB phải là index + graph

---

### 2. Không có edge table

→ mất khả năng query graph

---

### 3. Không có hash

→ reprocess toàn bộ rất tốn

---

### 4. Lưu embedding trong file

→ cực kỳ khó scale

---

# 9. Nâng cấp tương lai

Với design này, bạn có thể:

* migrate sang Neo4j
* build RAG system
* multi-agent knowledge editing
* realtime sync

---

# 10. Tóm lại

### Metadata DB nên chứa:

* Node index
* Relationship graph
* Tags
* Embeddings
* Lightweight metadata

---

### File system nên:

* clean
* deterministic
* human-readable

---

### Triết lý:

> Markdown = content
> Database = intelligence layer