# RSS-ArchiveORG

Extractor de RRSS (redes sociales) de un listado de webs usando [archive.org](https://archive.org).

Given a list of websites, this tool looks up the closest snapshot of each site in the
Internet Archive Wayback Machine, downloads the archived page, and extracts links to
social networks (RRSS) such as Facebook, Twitter/X, Instagram, LinkedIn, YouTube,
TikTok and more. It also extracts corporate email addresses when present.

## Landing web (MVP)

Interfaz para lanzar peticiones desde el navegador con resultados en tiempo real:

```bash
source .venv/bin/activate
python -m rss_archiveorg.web
```

Abre `http://localhost:8000`. Desde ahí puedes:

- Pegar o **subir un listado de URLs** (una por línea, sin tope de 200)
- Ajustar la **espera entre peticiones** (mínimo **3 s** para reducir bloqueos de archive.org)
- Activar **proxys cíclicos**: pegar (copiar/pegar), **subir un `.txt`**, o usar `proxies.txt` del servidor. El ciclo es **IP propia → proxy 1 → proxy 2 → …**
- Ver cada resultado en cuanto termina, con avisos si la web falla o no tiene RRSS/correo
- **Cancelar** un lote en curso
- **Filtrar** resultados (con datos / sin datos / errores)
- **Exportar** a JSON o CSV
- Elegir un **snapshot preferido** (`YYYYMMDD` o `YYYYMMDDhhmmss`)

## Requirements

- Python 3.10+
- Network access to `archive.org` / `web.archive.org`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt      # or requirements-dev.txt to also get pytest
```

In a Cursor Cloud Agent, `./.cursor/install.sh` performs the steps above automatically.

### Proxies (optional)

To reduce archive.org rate limits, copy the example file and add your credentials:

```bash
cp proxies.example.txt proxies.txt
chmod 600 proxies.txt
```

`proxies.txt` is git-ignored. Never commit real proxy credentials.

## Usage

Provide a text file with one website URL per line (see `sites.txt`):

```bash
# JSON output to stdout
python -m rss_archiveorg sites.txt

# With proxy rotation
python -m rss_archiveorg sites.txt --proxies proxies.txt -v

# CSV output to a file, only the first 2 sites
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
| `--max-retries` | Retries for throttled (429) or transient errors (default: 4). |
| `--backoff` | Base seconds for exponential backoff (default: 2). |
| `--backoff-max` | Maximum backoff cap in seconds (default: 60). |
| `--delay` | Seconds to wait between sites. |
| `--proxies` | Path to a proxy list file (`host:port:user:pass` per line). |
| `-v, --verbose` | Print progress to stderr. |

## Output

JSON output is a list of objects, one per site:

```json
[
  {
    "site": "https://www.python.org",
    "snapshot": {
      "url": "http://web.archive.org/web/.../https://www.python.org/",
      "timestamp": "..."
    },
    "social": {
      "facebook": ["https://www.facebook.com/..."],
      "twitter": ["https://twitter.com/..."]
    },
    "corporate_emails": ["info@example.com"],
    "all_emails": ["info@example.com"],
    "error": null
  }
]
```

## Project layout

```
rss_archiveorg/
  cli.py         # Argument parsing and entrypoint
  config.py      # RunConfig dataclass from CLI args
  pipeline.py    # Batch orchestration (sites -> results)
  io.py          # Site list input and JSON/CSV output
  models.py      # SiteResult / SnapshotInfo dataclasses
  wayback.py     # archive.org Wayback Machine client
  proxy.py       # Proxy parsing and rotation
  extractor.py   # HTML -> social network links
  extractors/    # Corporate email extraction
  utils.py       # URL/email helpers
  web/           # FastAPI landing + SSE streaming UI
docs/
  ARCHITECTURE.md
  SECURITY.md
  CODE_STANDARDS.md
tests/
sites.txt
proxies.example.txt
```

See `docs/ARCHITECTURE.md` for module responsibilities and `docs/CODE_STANDARDS.md`
for conventions to follow when adding new code.

## Development

```bash
pip install -r requirements-dev.txt
pytest
```

## Security

See `docs/SECURITY.md` for credential handling, proxy file permissions, and input
validation rules.
