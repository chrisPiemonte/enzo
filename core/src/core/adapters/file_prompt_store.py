"""Prompts read from versioned Markdown files with YAML frontmatter."""

from pathlib import Path

import yaml
from core.models.prompts import Prompt


class FilePromptStore:
    """Reads <root>/<name>/v<version>.md, resolving aliases from <root>/<name>/aliases.yaml."""

    def __init__(self, root: Path) -> None:
        """Create the store.

        Args:
            root: Folder holding one subfolder per prompt name.
        """
        self.root = root

    async def load(self, name: str, ref: str) -> Prompt:
        """Load one prompt version from its file.

        Args:
            name: Prompt name, i.e. the subfolder.
            ref: A version number, or an alias listed in aliases.yaml.

        Returns:
            The prompt text and its frontmatter metadata.
        """
        version = ref if ref.isdigit() else yaml.safe_load((self.root / name / "aliases.yaml").read_text())[ref]
        _, frontmatter, text = (self.root / name / f"v{version}.md").read_text().split("---\n", 2)
        meta = yaml.safe_load(frontmatter)
        return Prompt(name=name, version=meta["version"], description=meta["description"], text=text.strip())
