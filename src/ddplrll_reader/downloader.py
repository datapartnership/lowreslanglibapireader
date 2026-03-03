"""Download PDFs referenced in the Croissant JSON-LD and rewrite contentUrl."""

from __future__ import annotations

import asyncio
import copy
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


async def _download_one(
    client: httpx.AsyncClient,
    url: str,
    dest: Path,
    semaphore: asyncio.Semaphore,
) -> Path:
    """Download a single file, returning the local path."""
    async with semaphore:
        logger.info("Downloading %s → %s", url, dest)
        async with client.stream("GET", url) as resp:
            resp.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("wb") as fh:
                async for chunk in resp.aiter_bytes(chunk_size=64 * 1024):
                    fh.write(chunk)
    logger.info("  ✓ %s (%s bytes)", dest.name, dest.stat().st_size)
    return dest


def _collect_file_nodes(data: dict) -> list[dict]:
    """Walk the graph → distribution lists and return every FileObject dict."""
    nodes: list[dict] = []
    for dataset in data.get("graph", []):
        for fo in dataset.get("distribution", []):
            if fo.get("scContentUrl"):
                nodes.append(fo)
    return nodes


async def download_files_and_rewrite(
    data: dict,
    *,
    files_dir: Path,
    api_key: str = "",
    max_concurrent: int = 5,
    timeout: float = 120.0,
    verify_ssl: bool = True,
) -> dict:
    """Download every PDF in *data* and return a **copy** with rewritten URLs.

    Parameters
    ----------
    data
        The raw JSON dict from the API response.
    files_dir
        Directory where files will be saved.  Sub-directories per dataset-id
        are created automatically.
    api_key
        Passed as ``X-Api-Key`` header on each download request.
    max_concurrent
        Max simultaneous downloads.
    timeout
        Per-request timeout in seconds.

    Returns
    -------
    dict
        A deep copy of *data* with every ``scContentUrl`` replaced by the
        local file path.
    """
    result = copy.deepcopy(data)
    file_nodes = _collect_file_nodes(result)

    if not file_nodes:
        logger.warning("No file nodes with scContentUrl found – nothing to download.")
        return result

    files_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(max_concurrent)
    headers = {"X-Api-Key": api_key} if api_key else {}

    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True, verify=verify_ssl) as client:
        tasks: list[asyncio.Task] = []
        node_map: list[tuple[dict, Path]] = []

        for node in file_nodes:
            url: str = node["scContentUrl"]
            file_id: str = node.get("id", "unknown")
            # Use the file id as the filename, preserving a .pdf extension
            filename = file_id if file_id.endswith(".pdf") else f"{file_id}.pdf"
            dest = files_dir / filename

            node_map.append((node, dest))
            tasks.append(
                asyncio.create_task(_download_one(client, url, dest, semaphore))
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Rewrite URLs for successful downloads
    succeeded = 0
    failed = 0
    for (node, dest), res in zip(node_map, results):
        if isinstance(res, BaseException):
            logger.error("Failed to download %s: %s", node["scContentUrl"], res)
            failed += 1
        else:
            node["scContentUrl"] = str(dest)
            succeeded += 1

    logger.info(
        "Downloads complete: %d succeeded, %d failed out of %d total.",
        succeeded,
        failed,
        len(file_nodes),
    )
    return result
