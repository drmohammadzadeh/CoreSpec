#!/usr/bin/env python3
"""
Apache Fineract Documentation Crawler
=====================================
Recursively crawls the official Apache Fineract documentation from
https://fineract.apache.org/docs/stable up to depth 3, cleans HTML,
converts to structured GitHub-Flavored Markdown, extracts modular
sections, and generates sitemap.json and SUMMARY.md.
"""

import os
import re
import sys
import time
import json
import logging
from collections import deque
from datetime import datetime, timezone
import urllib.parse
import requests
import bs4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("docs_crawler")

# Constants
SEED_URL = "https://fineract.apache.org/docs/stable"
BASE_DOMAIN = "fineract.apache.org"
DOCS_PATH_PREFIX = "/docs/"
MAX_DEPTH = 3
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0
OUTPUT_DIR = os.path.abspath("docs/crawled")
PAGES_DIR = os.path.join(OUTPUT_DIR, "pages")
SITEMAP_FILE = os.path.join(OUTPUT_DIR, "sitemap.json")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "SUMMARY.md")

USER_AGENT = "FineractDocsCrawler/1.0 (+https://fineract.apache.org; pair-programming-ears)"


def get_http_session() -> requests.Session:
    """Create a resilient requests Session ignoring broken system proxies."""
    session = requests.Session()
    # Explicitly avoid loading broken proxy configurations (e.g. Windows registry http://(null):(null))
    session.trust_env = False
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return session


def normalize_url(url: str) -> str:
    """Strip anchor fragments and normalize URL for deduplication."""
    defragged, _ = urllib.parse.urldefrag(url)
    parsed = urllib.parse.urlparse(defragged)
    # Normalize path (remove duplicate slashes and strip trailing slash for consistency)
    path = re.sub(r"/+", "/", parsed.path)
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    normalized = urllib.parse.urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        parsed.params,
        parsed.query,
        ""
    ))
    return normalized


def is_valid_doc_url(url: str) -> bool:
    """Verify if URL belongs to fineract.apache.org/docs/."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if parsed.netloc.lower() != BASE_DOMAIN:
            return False
        if not (parsed.path == "/docs" or parsed.path.startswith(DOCS_PATH_PREFIX)):
            return False
        # Skip query sorting links from Apache Directory Index (e.g. ?C=N;O=D)
        if parsed.query and ("C=" in parsed.query or "O=" in parsed.query):
            return False
        return True
    except Exception:
        return False


def url_to_rel_path(url: str, is_section: bool = False, section_name: str = "") -> str:
    """Map URL to relative markdown path under docs/crawled/pages/."""
    parsed = urllib.parse.urlparse(url)
    subpath = parsed.path.strip("/")
    if subpath.startswith("docs"):
        subpath = subpath[len("docs"):].strip("/")
    if not subpath:
        subpath = "index"
    
    # Sanitize characters for filesystem
    subpath = re.sub(r'[\:*?"<>|]', '_', subpath)
    
    if is_section:
        sec_slug = re.sub(r'[^a-zA-Z0-9_\-]', '-', section_name).lower().strip('-')
        sec_slug = re.sub(r'-+', '-', sec_slug)
        return f"pages/{subpath}/sections/{sec_slug}.md"
    
    if subpath.endswith(".html") or subpath.endswith(".htm"):
        clean_name = re.sub(r'\.html?$', '.md', subpath)
        return f"pages/{clean_name}"
    elif subpath.endswith(".json"):
        return f"pages/{subpath}.md"
    else:
        return f"pages/{subpath}/index.md"


def clean_html_soup(soup: bs4.BeautifulSoup):
    """Strip scripts, styles, trackers, navigation headers, footers, and anchor tags."""
    for tag in soup.find_all(['script', 'style', 'noscript', 'meta', 'link', 'iframe', 'svg']):
        tag.decompose()
    for a in soup.find_all('a', class_='anchor'):
        a.decompose()
    # Remove #footer if present
    footer = soup.find(id='footer')
    if footer:
        footer.decompose()


def element_to_markdown(el, base_url: str = "") -> str:
    """Convert BeautifulSoup element hierarchy to GitHub Flavored Markdown."""
    if el is None:
        return ""
    if isinstance(el, bs4.NavigableString):
        return str(el)

    tag_name = el.name.lower() if el.name else ""

    # Admonition blocks (Asciidoctor notes, tips, warnings, important, caution)
    if tag_name == 'div' and 'admonitionblock' in el.get('class', []):
        classes = el.get('class', [])
        adm_type = "NOTE"
        for c in classes:
            if c != 'admonitionblock' and c.lower() in ('note', 'tip', 'warning', 'important', 'caution'):
                adm_type = c.upper()
                break
        content_el = el.find(class_='content') or el
        inner = ''.join(element_to_markdown(child, base_url) for child in content_el.children).strip()
        lines = inner.split('\n')
        quoted = '\n'.join(f'> {line}' for line in lines if line.strip())
        return f"\n\n> [!{adm_type}]\n{quoted}\n\n"

    # Preformatted code blocks
    if tag_name == 'pre' or (tag_name == 'div' and 'listingblock' in el.get('class', [])):
        code_tag = el.find('code') if tag_name != 'code' else el
        lang = ""
        if code_tag:
            lang = code_tag.get('data-lang', '') or ""
            if not lang:
                for cls in code_tag.get('class', []):
                    if cls.startswith('language-'):
                        lang = cls[len('language-'):]
            raw_code = code_tag.get_text()
        else:
            raw_code = el.get_text()
        raw_code = raw_code.rstrip('\n')
        return f"\n\n```{lang}\n{raw_code}\n```\n\n"

    # Headings
    if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        level = int(tag_name[1])
        prefix = '#' * level
        heading_text = el.get_text(strip=True)
        # Strip internal bracket links if present
        heading_text = re.sub(r'\[([^\]]+)\]\(#[^\)]+\)', r'\1', heading_text)
        return f"\n\n{prefix} {heading_text}\n\n"

    # Paragraphs
    if tag_name == 'p':
        inner = ''.join(element_to_markdown(c, base_url) for c in el.children).strip()
        return f"\n\n{inner}\n\n"

    # Inline code
    if tag_name == 'code':
        return f"`{el.get_text()}`"

    # Bold and strong
    if tag_name in ['strong', 'b']:
        inner = ''.join(element_to_markdown(c, base_url) for c in el.children).strip()
        return f"**{inner}**" if inner else ""

    # Italic and emphasis
    if tag_name in ['em', 'i']:
        inner = ''.join(element_to_markdown(c, base_url) for c in el.children).strip()
        return f"*{inner}*" if inner else ""

    # Strikethrough
    if tag_name in ['del', 's', 'strike']:
        inner = ''.join(element_to_markdown(c, base_url) for c in el.children).strip()
        return f"~~{inner}~~" if inner else ""

    # Hyperlinks
    if tag_name == 'a':
        href = el.get('href', '')
        inner = ''.join(element_to_markdown(c, base_url) for c in el.children).strip()
        if not inner:
            inner = href
        if not href or href.startswith('#'):
            return inner
        # Absolutize URL if needed
        if base_url and not href.startswith(('http://', 'https://', 'mailto:')):
            href = urllib.parse.urljoin(base_url, href)
        return f"[{inner}]({href})"

    # Images
    if tag_name == 'img':
        alt = el.get('alt', 'Image')
        src = el.get('src', '')
        if base_url and not src.startswith(('http://', 'https://')):
            src = urllib.parse.urljoin(base_url, src)
        return f"![{alt}]({src})"

    # Tables
    if tag_name == 'table':
        rows = []
        for tr in el.find_all('tr'):
            cells = []
            for cell in tr.find_all(['th', 'td']):
                c_text = ''.join(element_to_markdown(c, base_url) for c in cell.children).strip()
                # sanitize cell text: replace newlines with space, escape pipe
                c_text = c_text.replace('\n', ' ').replace('|', '\\|')
                cells.append(c_text)
            if cells:
                rows.append(cells)
        if not rows:
            return ""
        max_cols = max(len(r) for r in rows)
        norm_rows = [r + [''] * (max_cols - len(r)) for r in rows]
        header = norm_rows[0]
        md_table = "\n\n| " + " | ".join(header) + " |\n"
        md_table += "| " + " | ".join(["---"] * max_cols) + " |\n"
        for row in norm_rows[1:]:
            md_table += "| " + " | ".join(row) + " |\n"
        return md_table + "\n\n"

    # Lists
    if tag_name in ['ul', 'ol']:
        items = []
        for idx, li in enumerate(el.find_all('li', recursive=False)):
            marker = f"{idx+1}. " if tag_name == 'ol' else "* "
            inner = ''.join(element_to_markdown(c, base_url) for c in li.children).strip()
            lines = inner.split('\n')
            formatted = lines[0]
            if len(lines) > 1:
                formatted += '\n' + '\n'.join('  ' + l for l in lines[1:])
            items.append(f"{marker}{formatted}")
        return "\n\n" + '\n'.join(items) + "\n\n"

    # Blockquotes
    if tag_name == 'blockquote':
        inner = ''.join(element_to_markdown(c, base_url) for c in el.children).strip()
        lines = inner.split('\n')
        return "\n\n" + '\n'.join(f"> {l}" for l in lines) + "\n\n"

    # Horizontal rule
    if tag_name == 'hr':
        return "\n\n---\n\n"

    # Default fallback: concatenate children
    return ''.join(element_to_markdown(c, base_url) for c in el.children)


def render_markdown(element, base_url: str = "") -> str:
    """Render an HTML element into clean markdown with collapsed whitespace."""
    raw_md = element_to_markdown(element, base_url)
    cleaned = re.sub(r'\n{3,}', '\n\n', raw_md).strip()
    return cleaned


def create_frontmatter(source_url: str, title: str, depth: int, crawled_at: str, parent_url: str = None) -> str:
    """Build YAML frontmatter string."""
    fm = [
        "---",
        f"source_url: {source_url}",
        f"title: \"{title}\"",
        f"depth: {depth}",
        f"crawled_at: {crawled_at}"
    ]
    if parent_url:
        fm.append(f"parent_url: {parent_url}")
    fm.append("---\n\n")
    return "\n".join(fm)


def fetch_url_with_retries(session: requests.Session, url: str):
    """Fetch URL with retries and exponential backoff."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            return resp
        except requests.RequestException as e:
            logger.warning("Attempt %d/%d failed for %s: %s", attempt, MAX_RETRIES, url, e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF * attempt)
            else:
                logger.error("All retries exhausted for %s", url)
                return None


def extract_links(soup: bs4.BeautifulSoup, current_url: str) -> list[str]:
    """Extract all valid internal documentation links from soup."""
    found_urls = set()
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if not href or href.startswith(('mailto:', 'javascript:', 'tel:')):
            continue
        # Strip fragment
        defragged, _ = urllib.parse.urldefrag(href)
        if not defragged:
            continue
        full_url = urllib.parse.urljoin(current_url, defragged)
        norm_url = normalize_url(full_url)
        if is_valid_doc_url(norm_url):
            found_urls.add(norm_url)
    return sorted(list(found_urls))


def crawl_documentation():
    """Main crawler execution loop."""
    logger.info("Initializing Fineract Documentation Crawler...")
    logger.info("Seed URL: %s", SEED_URL)
    logger.info("Max Depth: %d", MAX_DEPTH)
    logger.info("Output Directory: %s", OUTPUT_DIR)

    os.makedirs(PAGES_DIR, exist_ok=True)

    session = get_http_session()
    timestamp_now = datetime.now(timezone.utc).isoformat()

    # Queue contains tuples of (url, depth)
    queue = deque([(normalize_url(SEED_URL), 0)])
    visited_urls = set()
    sitemap_entries = []
    summary_sections = []

    while queue:
        current_url, depth = queue.popleft()
        if current_url in visited_urls:
            continue
        visited_urls.add(current_url)

        logger.info("Crawling [Depth %d]: %s", depth, current_url)

        resp = fetch_url_with_retries(session, current_url)
        if resp is None:
            sitemap_entries.append({
                "url": current_url,
                "final_url": current_url,
                "local_path": None,
                "title": "Network Error",
                "depth": depth,
                "status": 0,
                "timestamp": timestamp_now,
                "size_bytes": 0
            })
            continue

        final_url = normalize_url(resp.url)
        visited_urls.add(final_url)

        if resp.status_code != 200:
            logger.info("Non-200 status [%d] for %s", resp.status_code, current_url)
            sitemap_entries.append({
                "url": current_url,
                "final_url": final_url,
                "local_path": None,
                "title": f"HTTP {resp.status_code}",
                "depth": depth,
                "status": resp.status_code,
                "timestamp": timestamp_now,
                "size_bytes": len(resp.content)
            })
            continue

        content_type = resp.headers.get("Content-Type", "")
        if "html" not in content_type:
            logger.info("Skipping non-HTML resource (%s): %s", content_type, current_url)
            # If it's json or text, we can still record it
            rel_path = url_to_rel_path(current_url)
            full_path = os.path.join(OUTPUT_DIR, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(create_frontmatter(current_url, os.path.basename(current_url), depth, timestamp_now))
                f.write(f"```\n{resp.text}\n```\n")
            sitemap_entries.append({
                "url": current_url,
                "final_url": final_url,
                "local_path": rel_path.replace("\\", "/"),
                "title": os.path.basename(current_url),
                "depth": depth,
                "status": resp.status_code,
                "timestamp": timestamp_now,
                "size_bytes": len(resp.content)
            })
            continue

        # Parse HTML using lxml for speed, fallback to html.parser
        try:
            soup = bs4.BeautifulSoup(resp.text, 'lxml')
        except Exception:
            soup = bs4.BeautifulSoup(resp.text, 'html.parser')

        # Extract title before decomposing headers
        page_title = "Apache Fineract Documentation"
        if soup.title and soup.title.string:
            page_title = soup.title.string.strip()
        elif soup.find('h1'):
            page_title = soup.find('h1').get_text(strip=True)

        # Extract links before cleaning soup
        new_links = extract_links(soup, final_url)
        if depth < MAX_DEPTH:
            for link in new_links:
                if link not in visited_urls:
                    queue.append((link, depth + 1))

        # Clean soup
        clean_html_soup(soup)

        # Extract core content container
        content_container = soup.find(id='content') or soup.find('main') or soup.find('article') or soup.body

        # Check if this is the primary monolithic documentation (contains multiple sect1 sections)
        sect1_divs = content_container.find_all('div', class_='sect1') if content_container else []
        is_monolithic = len(sect1_divs) >= 3

        # 1. Render and save the complete page
        page_rel_path = url_to_rel_path(current_url)
        page_full_path = os.path.join(OUTPUT_DIR, page_rel_path)
        os.makedirs(os.path.dirname(page_full_path), exist_ok=True)

        full_markdown = render_markdown(content_container, base_url=final_url)
        page_content = create_frontmatter(current_url, page_title, depth, timestamp_now) + f"# {page_title}\n\n" + full_markdown

        with open(page_full_path, "w", encoding="utf-8") as f:
            f.write(page_content)

        file_size = os.path.getsize(page_full_path)
        logger.info("Saved: %s (%d bytes)", page_rel_path, file_size)

        sitemap_entries.append({
            "url": current_url,
            "final_url": final_url,
            "local_path": page_rel_path.replace("\\", "/"),
            "title": page_title,
            "depth": depth,
            "status": resp.status_code,
            "timestamp": timestamp_now,
            "size_bytes": file_size,
            "sections_count": len(sect1_divs) if is_monolithic else 0
        })

        summary_page_item = {
            "title": page_title,
            "path": page_rel_path.replace("\\", "/"),
            "depth": depth,
            "sections": []
        }

        # 2. If monolithic, extract modular sections for downstream subagents
        if is_monolithic:
            logger.info("Extracting %d modular sections for %s...", len(sect1_divs), current_url)
            for idx, s1 in enumerate(sect1_divs, start=1):
                h2 = s1.find('h2')
                sec_id = h2.get('id', '') if h2 else f"section_{idx}"
                sec_title = h2.get_text(strip=True) if h2 else f"Section {idx}"
                sec_title = re.sub(r'\[([^\]]+)\]\(#[^\)]+\)', r'\1', sec_title)
                sec_slug = f"{idx:02d}-{re.sub(r'[^a-zA-Z0-9]', '-', sec_title).lower()}"
                sec_slug = re.sub(r'-+', '-', sec_slug).strip('-')

                sec_rel_path = url_to_rel_path(current_url, is_section=True, section_name=sec_slug)
                sec_full_path = os.path.join(OUTPUT_DIR, sec_rel_path)
                os.makedirs(os.path.dirname(sec_full_path), exist_ok=True)

                sec_md = render_markdown(s1, base_url=final_url)
                sec_source_url = f"{final_url}#{sec_id}" if sec_id else current_url
                sec_content = create_frontmatter(
                    source_url=sec_source_url,
                    title=sec_title,
                    depth=depth + 1,
                    crawled_at=timestamp_now,
                    parent_url=current_url
                ) + sec_md

                with open(sec_full_path, "w", encoding="utf-8") as f:
                    f.write(sec_content)

                sec_size = os.path.getsize(sec_full_path)
                sitemap_entries.append({
                    "url": sec_source_url,
                    "final_url": sec_source_url,
                    "local_path": sec_rel_path.replace("\\", "/"),
                    "title": sec_title,
                    "depth": depth + 1,
                    "status": 200,
                    "timestamp": timestamp_now,
                    "size_bytes": sec_size,
                    "is_section": True,
                    "parent_url": current_url
                })

                summary_page_item["sections"].append({
                    "title": sec_title,
                    "path": sec_rel_path.replace("\\", "/")
                })

        summary_sections.append(summary_page_item)

    # Write sitemap.json
    logger.info("Writing sitemap manifest to %s...", SITEMAP_FILE)
    with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
        json.dump(sitemap_entries, f, indent=2, ensure_ascii=False)

    # Write SUMMARY.md
    logger.info("Writing SUMMARY.md Table of Contents to %s...", SUMMARY_FILE)
    write_summary_md(summary_sections, sitemap_entries, timestamp_now)

    logger.info("Crawl completed successfully!")
    logger.info("Total visited URLs / entries: %d", len(sitemap_entries))


def write_summary_md(summary_sections: list[dict], sitemap_entries: list[dict], timestamp: str):
    """Generate hierarchical SUMMARY.md in GitBook / mdBook standard."""
    lines = [
        "# Apache Fineract Documentation Summary",
        "",
        f"> **Generated:** {timestamp}",
        f"> **Seed URL:** `{SEED_URL}`",
        f"> **Max Depth:** {MAX_DEPTH}",
        f"> **Total Catalogued Entries:** {len(sitemap_entries)}",
        "",
        "---",
        "",
        "## Table of Contents",
        ""
    ]

    for item in summary_sections:
        lines.append(f"* [{item['title']}]({item['path']})")
        if item.get("sections"):
            for sec in item["sections"]:
                lines.append(f"  * [{sec['title']}]({sec['path']})")

    lines.append("")
    lines.append("## Crawl Manifest Summary")
    lines.append("")
    lines.append("| Status | Depth | URL | Local Path | Size (Bytes) |")
    lines.append("| :---: | :---: | :--- | :--- | :---: |")
    for entry in sitemap_entries:
        status_badge = "OK (200)" if entry["status"] == 200 else f"ERR ({entry['status']})"
        loc = f"[`{entry['local_path']}`]({entry['local_path']})" if entry["local_path"] else "N/A"
        lines.append(f"| {status_badge} | {entry['depth']} | {entry['url']} | {loc} | {entry['size_bytes']} |")

    lines.append("")

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    crawl_documentation()
