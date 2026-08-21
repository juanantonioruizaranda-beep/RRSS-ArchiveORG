# Security

This document describes security-sensitive behavior and expectations for RSS-ArchiveORG.

## Threat model

The tool is a local CLI that:

- Reads a user-provided list of public website URLs.
- Fetches data from archive.org (and optionally via user-provided HTTP proxies).
- Writes extraction results to stdout or a user-chosen file.

It does **not** expose a network service, store credentials in a database, or execute
user HTML/JavaScript.

## Credentials and secrets

### Proxy files

- **Never commit** `proxies.txt` or any file containing live proxy credentials.
- Use `proxies.example.txt` as a template only.
- Restrict permissions on the real file: `chmod 600 proxies.txt`.
- The loader warns if the proxy file is group- or world-readable.
- Logs print only `host:port` via `Proxy.display_host()`; passwords are never logged.
- `Proxy.__repr__` masks passwords as `***`.
- If credentials were ever committed, rotate them and treat the old ones as compromised
  (git history may retain them even after deletion).

### Environment variables

`WaybackClient` sets `session.trust_env = False` so `HTTP_PROXY` / `HTTPS_PROXY` from
the environment are **not** applied unless you pass an explicit `--proxies` file.
This avoids accidental traffic routing or credential leakage through shared shells.

## Input validation

### Site URLs (`io.normalize_site_url`)

Only `http://` and `https://` URLs with a host are accepted. Other schemes (`file://`,
`ftp://`, etc.) are rejected at parse time with a line-numbered error.

### Proxy lines (`proxy.Proxy.parse`)

- Host must be a valid IP or hostname.
- Port must be in `1..65535`.
- Passwords may contain `:` (parsed with `rsplit` semantics via join of remainder).

## Network behavior

- All outbound requests use an explicit User-Agent: `RSS-ArchiveORG/0.1`.
- Retries with exponential backoff apply to 429 and selected 5xx responses.
- Proxy rotation occurs on retryable failures and between sites when a pool is configured.

## Dependency hygiene

- Pin major versions in `requirements.txt` (`requests`, `beautifulsoup4`, `lxml`).
- HTML parsing uses BeautifulSoup with the `lxml` parser; archived HTML is treated as
  untrusted input (links are extracted, not executed).

## Reporting issues

If you discover a security issue, avoid opening a public issue with exploit details.
Contact the repository owner privately.
