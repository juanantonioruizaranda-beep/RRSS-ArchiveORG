# RSS-ArchiveORG

Extractor de RRSS y correos corporativos de un listado de webs en [archive.org](https://archive.org).

## Qué hace

Para cada URL del listado:

1. Busca el snapshot más reciente archivado en Wayback Machine.
2. Descarga el HTML de esa página.
3. Extrae enlaces a redes sociales (Twitter/X, Facebook, LinkedIn, Instagram, YouTube, TikTok, Pinterest, GitHub).
4. Extrae correos electrónicos y filtra los **corporativos** (dominio del sitio, excluyendo proveedores gratuitos como Gmail o Outlook).

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python -m rss_archiveorg.cli extract examples/urls.txt -o results.json
```

Salida CSV:

```bash
python -m rss_archiveorg.cli extract examples/urls.txt -o results.csv
```

### Formato de salida

Cada entrada incluye:

- `original_url`: URL solicitada
- `archive_url`: snapshot usado en archive.org
- `snapshot_timestamp`: fecha del snapshot
- `social_links`: enlaces RRSS por plataforma
- `corporate_emails`: correos del dominio del sitio
- `all_emails`: todos los correos detectados (incluye no corporativos)
- `errors`: errores por URL, si los hubo

## Tests

```bash
python -m unittest discover -s tests -v
```

## Detección de correos corporativos

Se buscan correos en:

- Enlaces `mailto:`
- Texto visible de la página
- Metadatos HTML
- Formatos ofuscados habituales (`usuario [at] dominio [dot] com`)

Solo se conservan como corporativos los que pertenecen al dominio del sitio (incluidos subdominios), excluyendo dominios de correo gratuito.
