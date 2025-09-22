from __future__ import annotations
from pathlib import Path


class PromptManager:
    """
    Manages prompt templates and provides formatted prompts for conversations.

    This class loads prompt templates from text files and provides methods
    to generate formatted prompts for different conversation scenarios.
    """

    def __init__(
        self, prompts_dir: str | Path = "prompts", company_name: str = "Pharmesol"
    ):
        self.prompts_dir = Path(prompts_dir)
        self._cache: dict[str, str] = {}
        self.company_name = company_name

        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")

    def __getitem__(self, file_name: str) -> str:
        if not file_name.endswith(".txt"):
            file_name = f"{file_name}.txt"

        if file_name in self._cache:
            return self._cache[file_name]

        file_path = self.prompts_dir / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            self._cache[file_name] = content
            return content

        except Exception as e:
            raise RuntimeError(
                f"Failed to read prompt file {file_path}: {str(e)}"
            ) from e

    def reload_prompts(self) -> None:
        self._cache.clear()
