"""CLI interface powered by Typer."""

from __future__ import annotations

import logging
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from ddplrll_reader.client import DdplrllDatasetClient
from ddplrll_reader.config import Settings

app = typer.Typer(
    name="ddplrll-reader",
    help="Query the Nation Newspaper Dataset API and download PDFs.",
    add_completion=False,
)
console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@app.command()
def run(
    api_url: Annotated[
        str,
        typer.Option("--api-url", "-u", envvar="DDPLRLL_API_BASE_URL", help="Base URL of the API."),
    ] = "http://localhost:5000",
    api_key: Annotated[
        str,
        typer.Option("--api-key", "-k", envvar="DDPLRLL_API_KEY", help="API key for authentication."),
    ] = "",
    keyword: Annotated[
        Optional[str],
        typer.Option("--keyword", "-K", help="Filter by keyword."),
    ] = None,
    theme: Annotated[
        Optional[str],
        typer.Option("--theme", "-t", help="Filter by theme."),
    ] = None,
    author: Annotated[
        Optional[str],
        typer.Option("--author", "-a", help="Filter by author."),
    ] = None,
    year: Annotated[
        Optional[str],
        typer.Option("--year", "-y", help="Filter by year."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Max files returned (1-100)."),
    ] = 30,
    output_dir: Annotated[
        str,
        typer.Option("--output", "-o", help="Directory for JSON-LD and PDFs."),
    ] = "./output",
    no_download: Annotated[
        bool,
        typer.Option("--no-download", help="Skip downloading PDF files."),
    ] = False,
    max_concurrent: Annotated[
        int,
        typer.Option("--concurrency", "-c", help="Max parallel downloads."),
    ] = 5,
    no_verify_ssl: Annotated[
        bool,
        typer.Option("--no-verify-ssl", help="Skip SSL certificate verification."),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable debug logging."),
    ] = False,
) -> None:
    """Query the API, download files, and save a local JSON-LD document."""
    _setup_logging(verbose)

    settings = Settings(
        api_base_url=api_url,
        api_key=api_key,
        keyword=keyword,
        theme=theme,
        author=author,
        year=year,
        limit=limit,
        output_dir=output_dir,
        download_files=not no_download,
        max_concurrent_downloads=max_concurrent,
        verify_ssl=not no_verify_ssl,
    )

    client = DdplrllDatasetClient(settings)
    jsonld_path = client.run(output_dir=output_dir, download=not no_download)

    console.print(f"\n[bold green]✓[/] JSON-LD saved to [cyan]{jsonld_path}[/]")


@app.command()
def health(
    api_url: Annotated[
        str,
        typer.Option("--api-url", "-u", envvar="DDPLRLL_API_BASE_URL", help="Base URL of the API."),
    ] = "http://localhost:5000",
    api_key: Annotated[
        str,
        typer.Option("--api-key", "-k", envvar="DDPLRLL_API_KEY", help="API key for authentication."),
    ] = "",
) -> None:
    """Check the API health endpoint."""
    import httpx

    url = f"{api_url.rstrip('/')}/api/Datasets/health"
    headers = {"X-Api-Key": api_key} if api_key else {}
    resp = httpx.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    console.print_json(data=resp.json())


if __name__ == "__main__":
    app()
