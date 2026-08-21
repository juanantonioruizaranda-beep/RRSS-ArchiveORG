# RSS-ArchiveORG

Extractor de RRSS (redes sociales) de un listado de webs usando archive.org.

Given a list of websites, this tool looks up the closest snapshot of each site in
the [Internet Archive Wayback Machine](https://archive.org), downloads the archived
page, and extracts links to social networks (RRSS) such as Facebook, Twitter/X,
Instagram, LinkedIn, YouTube, TikTok and more.

## Requirements

- Python 3.10+
- Network access to `archive.org` / `web.archive.org`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt      # or requirements-dev.txt to also get pytest
```

In a Cursor Cloud Agent, `./.cursor/install.sh` performs the steps above
automatically and creates the `.venv` virtualenv.

## Usage

Provide a text file with one website URL per line (see `sites.txt`):

```bash
# JSON output to stdout
python -m rss_archiveorg sites.txt

# CSV output to a file, only the first 2 sites, verbose progress
python -m rss_archiveorg sites.txt --format csv --limit 2 --output results.csv --verbose

# Prefer a snapshot near a given date (YYYYMMDD[hhmmss])
python -m rss_archiveorg sites.txt --timestamp 20200101
```

### Options

| Flag | Description |
| --- | --- |
| `-o, --output` | Write results to a file instead of stdout. |
| `-f, --format` | Output format: `json` (default) or `csv`. |
| `-t, --timestamp` | Preferred snapshot date `YYYYMMDD[hhmmss]` (default: most recent). |
| `--limit` | Only process the first N sites. |
| `--timeout` | Per-request timeout in seconds (default: 30). |
| `-v, --verbose` | Print progress to stderr. |

## Output

JSON output is a list of objects, one per site:

```json
[
  {
    "site": "https://www.python.org",
    "snapshot": { "url": "http://web.archive.org/web/.../https://www.python.org/", "timestamp": "..." },
    "social": {
      "facebook": ["https://www.facebook.com/..."],
      "twitter": ["https://twitter.com/..."]
    },
    "error": null
  }
]
```

## Development

```bash
pip install -r requirements-dev.txt
pytest
```

## Project layout

```
rss_archiveorg/
  extractor.py   # HTML -> social network links
  wayback.py     # archive.org Wayback Machine client
  cli.py         # command-line interface
tests/           # unit tests
sites.txt        # sample input
```
