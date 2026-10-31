# Task 2 Brief: Implement and Execute Documentation Crawler Subagent

## Role in Project
Build and execute a Python-based crawler that systematically crawls the official Apache Fineract documentation at `https://fineract.apache.org/docs/stable` up to depth 3, cleans the HTML, converts to structured Markdown, and outputs a complete crawl corpus in `docs/crawled/` along with a machine-readable `sitemap.json` and a hierarchical `SUMMARY.md`.

## Deliverables
1. Python crawler script: `scripts/crawl_docs.py`
2. Crawled markdown files under `docs/crawled/pages/**/*.md`
3. Sitemap manifest: `docs/crawled/sitemap.json` (URL, local_path, title, depth, status, timestamp)
4. Hierarchical Table of Contents: `docs/crawled/SUMMARY.md`

## Technical Constraints & Requirements
1. **Target & Depth:**
   - Seed URL: `https://fineract.apache.org/docs/stable`
   - Maximum recursion depth: 3
   - Stay within domain: `fineract.apache.org/docs/` (do not crawl outside domains or other apache projects)
2. **Resilience & Sanitization:**
   - Use standard Python libraries (`urllib.request` or `urllib.error` or `requests`/`beautifulsoup4`). If third-party libraries (`beautifulsoup4`, `markdownify`) are installed, use them; if not, you can install them via pip or write robust fallback parsing.
   - Clean HTML: Remove redundant navigation headers, sidebars, and footers; extract the core `<article>` or `<main>` or document container.
   - Normalize links: Strip anchor hashes (`#...`) for crawl queue deduplication.
   - Track visited URLs to prevent infinite loops.
   - Inject frontmatter at the top of each `.md` file:
     ```yaml
     ---
     source_url: <url>
     title: <page title>
     depth: <depth>
     crawled_at: <iso8601>
     ---
     ```
3. **Report Contract:**
   - Implement the crawler, execute it, verify that `docs/crawled/sitemap.json` exists with crawled pages, and verify `docs/crawled/SUMMARY.md` is populated.
   - Commit files with `git add scripts/crawl_docs.py docs/crawled/` and `git commit -m "feat(crawler): crawl Fineract stable documentation up to depth 3"`.
   - Write full report to `docs/sdd/task-2-report.md`.
   - Return status `DONE`, commit hash, and summary of pages crawled.
