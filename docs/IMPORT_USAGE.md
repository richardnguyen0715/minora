# Import Command Usage Guide

## Problem Fixed ✅
Previously, the `/import` command only showed a placeholder message without actually saving data. This has been fixed.

## How It Works Now

When you send `/import <url>`:

1. **URL Validation**: System validates the URL format
2. **Platform Detection**: Detects if URL is from Facebook, Twitter, YouTube, Medium, GitHub, etc.
3. **Source Creation**: Creates a unique source node with metadata
4. **2-Layer Storage**: 
   - Saves markdown file in `knowledge/sources/YYYY/MM/`
   - Saves metadata in database
5. **Response**: Returns success message with source ID and location

## Commands

### Import from URL
```
/import <url>
```

### Aliases
- `/imp <url>`
- `/load <url>`

## Examples

### Facebook Link
```
/import https://www.facebook.com/share/p/1DJys3DVKH/
```
Response:
```
[OK] Source imported successfully!
- ID: src_20260501_facebook_001
- Platform: facebook
- File: knowledge/sources/2026/05/src-20260501-facebook-001.md
```

### Twitter Link
```
/import https://twitter.com/user/status/123456789
```

### Generic Web URL
```
/import https://www.example.com/interesting-article
```

### YouTube Video
```
/import https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

## What Gets Stored

### Markdown File
Located in `knowledge/sources/YYYY/MM/[id].md`

Contains:
- Frontmatter with metadata (YAML)
- Source URL
- Platform information
- Import timestamp
- Tags

Example:
```markdown
---
id: src_20260501_facebook_001
type: source
title: Source from facebook.com
slug: src_20260501_facebook_001
status: imported
tags:
- imported
metadata:
  url: https://www.facebook.com/share/p/1DJys3DVKH/
  platform: facebook
  imported_by_user: john_doe
created_at: '2026-05-01T14:18:27Z'
---

# Source from facebook.com

Source URL: https://www.facebook.com/share/p/1DJys3DVKH/

Platform: facebook
```

### Database Record
Metadata stored in SQLite:
- Node ID
- Type (source)
- Title
- Platform
- URL (in metadata JSON)
- Created/Updated timestamps
- Hash for change detection

## Supported Platforms

| Platform | Examples |
|----------|----------|
| facebook | facebook.com, fb.com |
| twitter | twitter.com, x.com |
| youtube | youtube.com, youtu.be |
| reddit | reddit.com |
| medium | medium.com |
| github | github.com |
| arxiv | arxiv.org |
| web | any other URL |

## Error Messages

### No URL provided
```
[ERROR] Please provide a URL: /import <url>
```

### Invalid URL format
```
[WARN] URL is not valid
```

### Already imported
```
[WARN] This source already imported: src_20260501_facebook_001
```

### Server error
```
[ERROR] Import failed: <error details>
```

## Next Steps

After importing a source, you can:

1. **List** - View all imported sources
   ```
   /list
   ```

2. **Find** - Search for sources
   ```
   /find facebook
   /find imported
   ```

3. **Read** - View source details
   ```
   /read src_20260501_facebook_001
   ```

4. **Create concepts** from sources (future feature)

## Testing

To verify import is working:

```bash
# Run tests
pytest tests/unit/test_import_source.py -v

# Output should show all tests PASS:
# - test_import_facebook_url PASSED
# - test_import_web_url PASSED
# - test_import_duplicate_url PASSED
# - test_import_invalid_url PASSED
# - test_import_no_url PASSED
```

## Architecture Notes

The import feature follows the **2-layer storage model**:
- **Layer 1**: Markdown files (human-readable, version-controllable)
- **Layer 2**: Metadata database (queryable, linkable)

This design enables:
- Easy Git backup of markdown files
- Efficient search via database indexes
- Future knowledge graph construction
- AI-friendly metadata extraction
