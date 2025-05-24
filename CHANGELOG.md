# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->

## [v0.4.0](https://github.com/jharemza/workday_scraper/releases/tag/v0.4.0) - 2025-05-24

<small>[Compare with v0.3.0](https://github.com/jharemza/workday_scraper/compare/v0.3.0...v0.4.0)</small>

### General Description

---

### Added in v0.4.0

- YAML-based config system for multi-institution scraping
- `config/institutions.yaml` with support for:
  - `name`, `workday_url`, `locations`, `search_text`
- New runner module `institution_runner.py` to handle per-institution logic
- Separate output files for each institution in `json_output/`
- Institution-aware logging and progress bars
- Internal documentation added under `docs/v0.4.0_architecture.md`
- Public-facing `README.md` with setup, config, and usage instructions

### Fixed in v0.4.0

- Ensured backward compatibility with M&T Bank scraping flow via isolated regression test

### Specific Commits

---

### Features

- Add `InstitutionRunner` with YAML-driven inputs ([100cdf5](https://github.com/jharemza/workday_scraper/commit/100cdf5))

### Code Refactoring

- Extract M&T-specific logic to config ([7ae416e](https://github.com/jharemza/workday_scraper/commit/7ae416e))

### Chores

- Add YAML config structure and parser ([5e98db1](https://github.com/jharemza/workday_scraper/commit/5e98db1))
- Include institution name in logs and progress bars ([411eb7b](https://github.com/jharemza/workday_scraper/commit/411eb7b))
- Ignore JSON output files in `.gitignore` ([77601b6](https://github.com/jharemza/workday_scraper/commit/77601b6))

### Documentation

- Add architecture reference for v0.4.0 abstraction ([9d45ce3](https://github.com/jharemza/workday_scraper/commit/9d45ce3))
- Update README.md ([4d775f3](https://github.com/jharemza/workday_scraper/commit/4d775f3))

### Added

- Add CHANGELOG.md for versions v0.1.0 through v0.3.0 ([55716b8](https://github.com/jharemza/workday_scraper/commit/55716b8d1882cd44859bae2223d0c257ca90be09) by Jeremiah Haremza).

<!-- insertion marker -->

## [v0.3.0](https://github.com/jharemza/workday_scraper/releases/tag/v0.3.0) - 2025-05-20

<small>[Compare with v0.2.0](https://github.com/jharemza/workday_scraper/compare/v0.2.0...v0.3.0)</small>

### Added in v0.3.0

- Add inline formatting support and improve recursive HTML parsing ([b1594be](https://github.com/jharemza/workday_scraper/commit/b1594beceac4120d061059dff85c1b4ce65b8d4b) by Jeremiah Haremza).

### Comments on v0.3.0

- Inline formatting support for **bold**, _italic_, underline, code, and strikethrough
- Recursive HTML parsing of deeply nested tags (e.g., `div > span > p`)
- Preservation of orphaned text nodes as paragraph blocks
- Character chunking for rich text spans to comply with Notion’s 2000-char limit
- Skipping of empty HTML tags like `<h1></h1>` and `<p></p>`
- Missed content inside nested `<div>`/`<span>` wrappers

## [v0.2.0](https://github.com/jharemza/workday_scraper/releases/tag/v0.2.0) - 2025-05-19

<small>[Compare with v0.1.0](https://github.com/jharemza/workday_scraper/compare/v0.1.0...v0.2.0)</small>

### Added in v0.2.0

- Added job description to database page. ([616c886](https://github.com/jharemza/workday_scraper/commit/616c88694c8a86b31a5571b096b40310d337c0b2) by Jeremiah Haremza).

### Comments on v0.2.0

- Modularized project into `scraper.py`, `notion_client.py`, and `job_parser.py`
- Added support for Notion job upload filtering based on Req ID presence
- Chunked Notion API calls to comply with block limits
- Logging support with file rotation and console filtering
- Progress indicators using `tqdm`

## [v0.1.0](https://github.com/jharemza/workday_scraper/releases/tag/v0.1.0) - 2025-05-18

<small>[Compare with first commit](https://github.com/jharemza/workday_scraper/compare/7743493c934f5c70a64ec44e948dc091213033c6...v0.1.0)</small>

### Added in v0.1.0

- Add tqdm-based progress tracking and per-stage summaries ([89a43a6](https://github.com/jharemza/workday_scraper/commit/89a43a6cc949cfff5e178fdddef98adc381ebd8b) by Jeremiah Haremza).
- Added file logging with file output ([ff923aa](https://github.com/jharemza/workday_scraper/commit/ff923aa50e2ddc4db2d486578f376d7c8d530146) by Jeremiah Haremza).
- Add Notion deduplication logic with company filter ([dde98d1](https://github.com/jharemza/workday_scraper/commit/dde98d1f2c3cc12d89a579f08a54b29e9ce14e60) by Jeremiah Haremza).
- Added per job entry to notion database. ([864f72a](https://github.com/jharemza/workday_scraper/commit/864f72aeb9282ea3a873b867ec5b2089e7e685a2) by Jeremiah Haremza).
- Added notion static variables. ([73a5017](https://github.com/jharemza/workday_scraper/commit/73a50178bf4b0bdce92dc96392ab80392059d4eb) by Jeremiah Haremza).
- Added filtering for job info only. ([1fc5667](https://github.com/jharemza/workday_scraper/commit/1fc566795c9406e83a943f1329ae9ba15ee13220) by Jeremiah Haremza).

### Comments on v0.1.0

- Initial working scraper: fetches job listings from Workday and stores them in Notion
- Salary extraction from `jobDescription` via regex
- Search/filter support by location (e.g., "Remote, USA", "Buffalo, NY")
- Default fallback for `Application Deadline`
