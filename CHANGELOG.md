# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v0.3.0] - 2025-05-19

### Added in v0.3.0

- Inline formatting support for **bold**, _italic_, underline, code, and strikethrough
- Recursive HTML parsing of deeply nested tags (e.g., `div > span > p`)
- Preservation of orphaned text nodes as paragraph blocks
- Character chunking for rich text spans to comply with Notion’s 2000-char limit

### Fixed in v0.3.0

- Skipping of empty HTML tags like `<h1></h1>` and `<p></p>`
- Missed content inside nested `<div>`/`<span>` wrappers

---

## [v0.2.0] - 2025-05-18

### Added in v0.2.0

- Modularized project into `scraper.py`, `notion_client.py`, and `job_parser.py`
- Added support for Notion job upload filtering based on Req ID presence
- Chunked Notion API calls to comply with block limits
- Logging support with file rotation and console filtering
- Progress indicators using `tqdm`

---

## [v0.1.0] - 2025-05-17

### Added in v0.1.0

- Initial working scraper: fetches job listings from Workday and stores them in Notion
- Salary extraction from `jobDescription` via regex
- Search/filter support by location (e.g., "Remote, USA", "Buffalo, NY")
- Default fallback for `Application Deadline`
