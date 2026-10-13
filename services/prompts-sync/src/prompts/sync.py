"""Register the versioned prompt files in the MLflow prompt registry: files are the source of truth."""

import asyncio
import logging
import sys
from pathlib import Path

import mlflow
import yaml
from core.adapters.file_prompt_store import FilePromptStore
from mlflow.entities.model_registry import PromptVersion

from prompts.settings import settings

log = logging.getLogger("prompts-sync")


class SyncError(Exception):
    """The files and the registry disagree in a way the sync must not paper over."""


async def sync_prompt(files: FilePromptStore, name: str) -> None:
    """Register the missing versions of one prompt, then set its aliases.

    Args:
        files: Store reading the prompt files.
        name: Prompt name, i.e. its subfolder.

    Raises:
        SyncError: Versions have a gap, a registered version differs from its file, or the registry has extra ones.
    """
    numbers = _versions(files.root / name)
    for number in numbers:
        prompt = await files.load(name, str(number))
        registered = _registered(name, number)
        if registered is None:
            created = mlflow.genai.register_prompt(name, prompt.text, commit_message=prompt.description,
                                                   tags={"source": f"{name}/v{number}.md"})
            if created.version != number:
                raise SyncError(f"{name}: v{number}.md was registered as version {created.version}")
            log.info("%s v%d registered", name, number)
        elif registered.template != prompt.text:
            raise SyncError(f"{name}: v{number}.md differs from the registered version; add a new file instead")
        else:
            log.info("%s v%d unchanged", name, number)
    if _registered(name, len(numbers) + 1) is not None:
        raise SyncError(f"{name}: the registry has versions beyond v{len(numbers)}.md; it was edited by hand")
    _sync_aliases(files.root / name, name)


def _versions(folder: Path) -> list[int]:
    """List the version numbers of a prompt's files.

    Args:
        folder: The prompt's folder, holding v<n>.md files.

    Returns:
        The version numbers, 1 to N.

    Raises:
        SyncError: The numbers do not run from 1 to N without gaps, as MLflow numbers versions itself.
    """
    numbers = sorted(int(file.stem[1:]) for file in folder.glob("v*.md"))
    if numbers != list(range(1, len(numbers) + 1)):
        raise SyncError(f"{folder.name}: versions must run from v1.md without gaps, found {numbers}")
    return numbers


def _registered(name: str, number: int) -> PromptVersion | None:
    """Fetch one registered version, bypassing MLflow's cache.

    Args:
        name: Prompt name.
        number: Version number.

    Returns:
        The registered version, or None if it does not exist.
    """
    version: PromptVersion | None = mlflow.genai.load_prompt(  # typed Any: mlflow wraps it in a decorator
        f"prompts:/{name}/{number}", allow_missing=True, link_to_model=False, cache_ttl_seconds=0
    )
    return version


def _sync_aliases(folder: Path, name: str) -> None:
    """Point each alias in aliases.yaml at its version; aliases set elsewhere are left alone.

    Args:
        folder: The prompt's folder.
        name: Prompt name.
    """
    aliases_file = folder / "aliases.yaml"
    aliases: dict[str, int] = yaml.safe_load(aliases_file.read_text()) if aliases_file.exists() else {}
    for alias, number in aliases.items():
        mlflow.genai.set_prompt_alias(name, alias, number)
        log.info("%s @%s -> v%d", name, alias, number)


async def sync_all(root: Path) -> None:
    """Sync every prompt folder under the root.

    Args:
        root: Folder holding one subfolder per prompt name.
    """
    files = FilePromptStore(root)
    for folder in sorted(path for path in root.iterdir() if path.is_dir()):
        await sync_prompt(files, folder.name)


def run() -> None:
    """Entry point: sync the prompts, exiting non-zero if the files and the registry disagree."""
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
    logging.getLogger("mlflow").setLevel(logging.WARNING)
    mlflow.set_tracking_uri(settings.mlflow_url)
    try:
        asyncio.run(sync_all(settings.dir))
    except SyncError as error:
        log.error("%s", error)
        sys.exit(1)
