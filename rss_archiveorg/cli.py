from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer

from rss_archiveorg.processor import process_url

app = typer.Typer(
    help="Extrae RRSS y correos corporativos de webs archivadas en archive.org"
)


def _read_urls(input_path: Path) -> list[str]:
    urls: list[str] = []
    for line in input_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def _write_json(results: list[dict], output_path: Path) -> None:
    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _write_csv(results: list[dict], output_path: Path) -> None:
    fieldnames = [
        "original_url",
        "archive_url",
        "snapshot_timestamp",
        "corporate_emails",
        "all_emails",
        "social_links",
        "errors",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    "original_url": row["original_url"],
                    "archive_url": row.get("archive_url") or "",
                    "snapshot_timestamp": row.get("snapshot_timestamp") or "",
                    "corporate_emails": ";".join(row.get("corporate_emails", [])),
                    "all_emails": ";".join(row.get("all_emails", [])),
                    "social_links": json.dumps(
                        row.get("social_links", {}), ensure_ascii=False
                    ),
                    "errors": ";".join(row.get("errors", [])),
                }
            )


@app.command()
def extract(
    input_file: Annotated[
        Path,
        typer.Argument(help="Archivo de texto con una URL por línea"),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Archivo de salida (.json o .csv)"),
    ] = Path("results.json"),
) -> None:
    urls = _read_urls(input_file)
    if not urls:
        typer.echo("No se encontraron URLs en el archivo de entrada.")
        raise typer.Exit(code=1)

    results = [asdict(process_url(url)) for url in urls]

    if output.suffix.lower() == ".csv":
        _write_csv(results, output)
    else:
        _write_json(results, output)

    typer.echo(f"Procesadas {len(results)} URLs. Resultados en {output}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
