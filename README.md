SS-ArchiveORG
Bulk social media and corporate contact extractor powered by the Internet Archive Wayback Machine.

RSS-ArchiveORG is a Python tool that takes a list of website URLs and automatically discovers each site’s social media presence and corporate email addresses by reading archived snapshots from archive.org (the Wayback Machine), instead of scraping live websites directly.

What problem does it solve?
When you need to research many organizations at once — for lead generation, OSINT, competitive analysis, or data enrichment — manually visiting each website to find Facebook pages, LinkedIn profiles, Twitter/X accounts, and contact emails is slow and unreliable. Sites change, go offline, or block automated access.

RSS-ArchiveORG solves this by:

Querying the Wayback Machine for the most recent (or date-specific) archived snapshot of each URL.
Downloading the archived HTML from web.archive.org.
Parsing the page to extract structured contact and social data.
This approach is useful because archived pages are stable, publicly accessible, and often preserve contact information that has since been removed from the live site.

What it extracts
Social media links (RRSS)
Detects and normalizes links to major platforms, including:

Facebook
Twitter / X
Instagram
LinkedIn
YouTube
TikTok
Pinterest
Telegram
WhatsApp
Vimeo
Flickr
Spotify
GitHub
Links are cleaned to remove Wayback Machine URL rewriting, deduplicated, and grouped by platform.

Corporate email addresses
Scans archived HTML for email addresses found in:

mailto: links
Visible page text
HTML metadata
Common obfuscated formats (e.g. user [at] domain [dot] com)
Only emails matching the site’s own domain are kept as corporate contacts. Free providers (Gmail, Outlook, Yahoo, etc.) are filtered out.

How it works
Input URL list  →  Wayback Machine API  →  Download archived HTML  →  Parse & extract  →  JSON / CSV output
For each URL in your list, the tool:

Calls the archive.org availability API to find the closest snapshot (most recent by default, or near a date you specify).
Fetches the archived page content.
Runs HTML parsers to extract social links and emails.
Returns a structured result per site, including the archive URL used, snapshot timestamp, extracted data, and any errors.
Features
Feature	Description
Batch processing	Process hundreds of URLs from a plain text file (one URL per line).
CLI & Web UI	Command-line tool for automation; optional FastAPI web interface with real-time streaming results.
JSON & CSV export	Structured output for pipelines, spreadsheets, or databases.
Snapshot date selection	Target a specific historical snapshot (YYYYMMDD or YYYYMMDDhhmmss).
Rate-limit handling	Configurable delays, exponential backoff, and retries for archive.org throttling (HTTP 429).
Proxy rotation	Optional proxy support to reduce IP-based rate limits during large batches.
Error resilience	Per-URL error reporting; one failed site does not stop the entire batch.
Example output
{
  "site": "https://www.example.com",
  "snapshot": {
    "url": "http://web.archive.org/web/20230115.../https://www.example.com/",
    "timestamp": "20230115120000"
  },
  "social": {
    "facebook": ["https://www.facebook.com/example"],
    "linkedin": ["https://www.linkedin.com/company/example"],
    "twitter": ["https://twitter.com/example"]
  },
  "corporate_emails": ["info@example.com", "contact@example.com"],
  "all_emails": ["info@example.com", "contact@example.com"],
  "error": null
}
Use cases
Lead generation & sales prospecting — enrich a list of company websites with social profiles and contact emails.
OSINT & research — recover historical contact information from archived pages.
Data enrichment pipelines — feed URL lists and get structured JSON/CSV for CRM or database import.
Competitive intelligence — map the social presence of multiple competitors in one run.
Digital archaeology — find social links and emails that existed on a site before redesigns or shutdowns.
Tech stack
Python 3.10+
BeautifulSoup for HTML parsing
FastAPI for the optional web UI (Server-Sent Events for live results)
Internet Archive Wayback Machine API as the data source
Quick start

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# CLI: extract from a URL list
python -m rss_archiveorg sites.txt --format json --output results.json
# Web UI
python -m rss_archiveorg.web
# Open http://localhost:8000
Note on the name
RSS here refers to RRSS (Redes Sociales — Spanish for social networks), not RSS feeds. The project name reflects its origin: extracting social network links from archived web pages.

If you want, I can also turn this into an updated README.md on main or help you pick which feature branch to merge first.
