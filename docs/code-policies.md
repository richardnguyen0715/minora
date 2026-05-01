# 1. Ngôn ngữ & Naming conventions

### Nguyên tắc bắt buộc

* Sử dụng **tiếng Anh 100%** trong:

  * tên biến
  * tên hàm
  * tên class
  * commit message
  * comment
* Không sử dụng emoji trong code, log, commit

---

### Naming chuẩn

| Thành phần | Convention | Ví dụ                     |
| ---------- | ---------- | ------------------------- |
| Variable   | snake_case | `user_id`, `message_text` |
| Function   | snake_case | `process_message()`       |
| Class      | PascalCase | `MessageProcessor`        |
| Constant   | UPPER_CASE | `MAX_RETRY`               |
| File       | snake_case | `message_service.py`      |

---

### Quy tắc đặt tên

* Tránh viết tắt khó hiểu:

  * ❌ `msg`, `usr`
  * ✔ `message`, `user`
* Tên phải mô tả **ý nghĩa, không phải kiểu dữ liệu**

  * ❌ `data`, `obj`
  * ✔ `telegram_message_payload`

---

# 2. Cấu trúc thư mục

### Nguyên tắc

Cấu trúc theo **domain + responsibility**, không theo framework

---

### Ví dụ chuẩn (backend service)

```bash
app/
├── domain/          # business logic thuần
├── application/     # use cases
├── infrastructure/  # external systems
├── interface/       # API / controllers
├── tests/
└── main.py
```

---

### Quy tắc quan trọng

* Mỗi folder có **1 trách nhiệm rõ ràng**
* Không import ngược chiều (outer → inner only)

---

# 3. Docstring (chuẩn cực kỳ quan trọng)

### Chuẩn phổ biến

* PEP 257
* Google Python Style Guide

---

### Ví dụ chuẩn

```python
def process_message(message: Message) -> str:
    """
    Process an incoming message and generate a response.

    Args:
        message (Message): Normalized message object.

    Returns:
        str: Response text to send back to user.
    """
```

---

### Quy tắc

* Mọi function public phải có docstring
* Mô tả:

  * input
  * output
  * side effects (nếu có)
* Không viết lại obvious code

---

# 4. Commenting

### Nguyên tắc vàng

> Comment **WHY**, không phải **WHAT**

---

### Ví dụ

```python
# ❌ Bad
# increment i by 1
i += 1

# ✔ Good
# retry mechanism to handle transient network failures
retry_count += 1
```

---

### Khi nào cần comment

* Business logic phức tạp
* Workaround hack
* Performance optimization
* Integration external system

---

# 5. Clean Code principles

### Theo Clean Code

---

### Các rule quan trọng

#### 1. Function nhỏ

* < 20–30 dòng
* Single responsibility

#### 2. Không nested quá sâu

* Tối đa 2–3 levels

#### 3. Early return

```python
if not user:
    return None
```

---

#### 4. Không magic number

```python
# ❌
timeout = 3000

# ✔
DEFAULT_TIMEOUT_MS = 3000
```

---

# 6. Error handling

### Nguyên tắc

* Không swallow exception
* Log đầy đủ context
* Phân loại error

---

### Ví dụ

```python
try:
    send_message()
except NetworkError as e:
    logger.error("Failed to send message", extra={"chat_id": chat_id})
    raise
```

---

# 7. Logging

### Chuẩn

* Log dạng structured (JSON nếu production)
* Không dùng print

* tools: sử dụng loguru

---

### Ví dụ

```python
logger.info(
    "message_received",
    extra={"chat_id": chat_id, "user_id": user_id}
)
```

---

# 8. Code formatting

### Tool chuẩn

* Black
* Prettier

---

### Quy tắc

* Không tranh luận style → dùng formatter
* Line length: ~88–120 chars

---

# 9. Linting & static analysis

### Tool

* Flake8
* ESLint
* mypy

---

### Mục tiêu

* Bắt bug sớm
* Enforce convention

---

# 10. Testing

### Quy tắc

* Viết test cho:

  * business logic
  * edge cases
* Không test framework

---

### Structure

```bash
tests/
├── unit/
├── integration/
```

---

### Nguyên tắc

* Test phải:

  * deterministic
  * fast
  * isolated

---

# 11. Git & version control

### Commit message chuẩn

Theo Conventional Commits

---

### Ví dụ

```bash
feat: add telegram auto responder
fix: handle empty message case
refactor: extract message service
```

---

# 12. Configuration management

### Nguyên tắc

* Không hardcode config
* Dùng env variables
* Dùng yaml configs file trong các thư mục configs/

---

### Ví dụ

```python
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
```

---

# 13. Dependency management

### Quy tắc

* Pin version

```txt
fastapi==0.110.0
```

* Không import unused lib

* tools: sử dụng poetry

---

# 14. Security cơ bản

* Không commit secret
* Validate input từ bên ngoài
* Rate limit API

---

# 15. Performance mindset

* Không optimize sớm
* Nhưng:

  * tránh N+1 query
  * tránh blocking I/O

---

# 16. Consistency (quan trọng nhất)

> Codebase tốt không phải code “hay nhất”, mà là code **consistent nhất**

---

### Cách đảm bảo

* Coding guideline document
* Pre-commit hooks
* CI check

---

# 17. Documentation hệ thống

Không chỉ docstring, cần thêm:

* README
* Architecture diagram
* API contract

---

# Tổng kết

Một codebase đạt chuẩn quốc tế cần:

* Naming rõ ràng
* Structure theo domain
* Docstring đầy đủ
* Comment đúng mục đích
* Clean code principles
* Logging + error handling chuẩn
* Tooling (lint, format, test)
* Consistency toàn hệ thống