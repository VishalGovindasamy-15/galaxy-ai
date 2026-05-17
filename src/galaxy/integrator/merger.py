"""Code chunk merger — merges worker output chunks into complete files.

Handles import deduplication, symbol placement, and content assembly.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from galaxy.contracts.types import ChunkOperation, ChunkStatus, CodeChunk
from galaxy.integrator import FileState, MergeResult, MergeStrategy

logger = logging.getLogger(__name__)

# Regex to extract import lines
IMPORT_RE = re.compile(r"^(?:from\s+\S+\s+)?import\s+.+$", re.MULTILINE)

# Regex to extract function/class definitions
FUNC_DEF_RE = re.compile(r"^(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)
CLASS_DEF_RE = re.compile(r"^class\s+(\w+)[\s(:]", re.MULTILINE)


class ChunkMerger:
    """Merges code chunks into FileState objects.

    Handles:
    - Import deduplication and sorting
    - Function/class placement
    - Symbol tracking to prevent duplicates
    - Content assembly in logical order
    """

    def merge_chunk(
        self,
        chunk: CodeChunk,
        file_state: FileState | None = None,
    ) -> MergeResult:
        """Merge a single code chunk into a file state.

        Args:
            chunk: The code chunk to merge.
            file_state: Existing file state (None = new file).

        Returns:
            MergeResult with the merged content.
        """
        if file_state is None:
            file_state = FileState(path=chunk.target_file)

        result = MergeResult(file_path=chunk.target_file)

        # Extract imports from chunk content
        chunk_imports = self._extract_imports(chunk.content)
        chunk_body = self._remove_imports(chunk.content)

        # Add dependency imports
        dep_imports = self._generate_dependency_imports(chunk.dependencies)
        all_new_imports = chunk_imports + dep_imports

        # Deduplicate imports
        for imp in all_new_imports:
            imp_stripped = imp.strip()
            if imp_stripped and imp_stripped not in file_state.imports:
                file_state.imports.append(imp_stripped)
                result.imports_added.append(imp_stripped)

        # Extract symbols from chunk
        new_symbols = self._extract_symbols(chunk_body)

        # Merge based on operation
        if chunk.operation == ChunkOperation.CREATE_FILE:
            file_state.content = chunk_body.strip()
            for sym in new_symbols:
                file_state.add_symbol(sym)
                result.symbols_added.append(sym)

        elif chunk.operation in (
            ChunkOperation.CREATE_FUNCTION,
            ChunkOperation.CREATE_CLASS,
            ChunkOperation.CREATE_METHOD,
            ChunkOperation.ADD_CONSTANT,
        ):
            # Append new code with proper spacing
            if file_state.content:
                file_state.content = file_state.content.rstrip() + "\n\n\n" + chunk_body.strip()
            else:
                file_state.content = chunk_body.strip()

            for sym in new_symbols:
                file_state.add_symbol(sym)
                result.symbols_added.append(sym)

        elif chunk.operation in (
            ChunkOperation.MODIFY_FUNCTION,
            ChunkOperation.MODIFY_CLASS,
        ):
            # Replace existing symbol
            if chunk.target_symbol and file_state.has_symbol(chunk.target_symbol):
                file_state.content = self._replace_symbol(
                    file_state.content,
                    chunk.target_symbol,
                    chunk_body.strip(),
                )
            else:
                # Symbol doesn't exist, append instead
                if file_state.content:
                    file_state.content = file_state.content.rstrip() + "\n\n\n" + chunk_body.strip()
                else:
                    file_state.content = chunk_body.strip()
                for sym in new_symbols:
                    file_state.add_symbol(sym)
                    result.symbols_added.append(sym)

        elif chunk.operation == ChunkOperation.ADD_IMPORT:
            # Already handled above
            pass

        elif chunk.operation == ChunkOperation.APPEND_CODE:
            if file_state.content:
                file_state.content = file_state.content.rstrip() + "\n\n" + chunk_body.strip()
            else:
                file_state.content = chunk_body.strip()

        elif chunk.operation == ChunkOperation.ADD_DECORATOR:
            # Add decorator before target symbol
            if chunk.target_symbol:
                file_state.content = self._add_decorator_before(
                    file_state.content,
                    chunk.target_symbol,
                    chunk_body.strip(),
                )

        # Track chunk
        file_state.chunk_ids.append(chunk.id)
        from datetime import datetime, timezone
        file_state.updated_at = datetime.now(timezone.utc)

        # Assemble final content
        result.content = self.assemble_file(file_state)
        result.chunks_merged = 1
        result.success = True

        chunk.status = ChunkStatus.MERGED
        return result

    def merge_chunks(
        self,
        chunks: list[CodeChunk],
        file_state: FileState | None = None,
    ) -> MergeResult:
        """Merge multiple chunks into a single file.

        Args:
            chunks: Chunks to merge (should target the same file).
            file_state: Existing file state.

        Returns:
            Combined MergeResult.
        """
        if not chunks:
            return MergeResult(success=True)

        if file_state is None:
            file_state = FileState(path=chunks[0].target_file)

        combined_result = MergeResult(file_path=file_state.path)

        for chunk in chunks:
            result = self.merge_chunk(chunk, file_state)
            combined_result.symbols_added.extend(result.symbols_added)
            combined_result.imports_added.extend(result.imports_added)
            combined_result.conflicts.extend(result.conflicts)
            combined_result.chunks_merged += 1

        combined_result.content = self.assemble_file(file_state)
        combined_result.success = not combined_result.has_conflicts
        return combined_result

    def assemble_file(self, file_state: FileState) -> str:
        """Assemble a complete file from file state.

        Order: docstring → imports → content
        """
        parts: list[str] = []

        # Sorted imports
        if file_state.imports:
            stdlib_imports = []
            third_party_imports = []
            local_imports = []

            for imp in sorted(set(file_state.imports)):
                if imp.startswith("from .") or imp.startswith("from galaxy"):
                    local_imports.append(imp)
                elif any(imp.startswith(f"import {m}") or imp.startswith(f"from {m}")
                         for m in ("os", "sys", "re", "json", "uuid", "datetime",
                                   "pathlib", "typing", "enum", "dataclasses",
                                   "logging", "asyncio", "collections", "functools",
                                   "hashlib", "hmac", "secrets", "__future__")):
                    stdlib_imports.append(imp)
                else:
                    third_party_imports.append(imp)

            if stdlib_imports:
                parts.append("\n".join(sorted(stdlib_imports)))
            if third_party_imports:
                parts.append("\n".join(sorted(third_party_imports)))
            if local_imports:
                parts.append("\n".join(sorted(local_imports)))

        # Body content
        if file_state.content:
            parts.append(file_state.content)

        return "\n\n".join(parts) + "\n" if parts else ""

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import lines from code content."""
        imports = []
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                imports.append(stripped)
        return imports

    def _remove_imports(self, content: str) -> str:
        """Remove import lines from code content."""
        lines = []
        for line in content.split("\n"):
            stripped = line.strip()
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                lines.append(line)
        # Remove leading blank lines
        result = "\n".join(lines)
        return result.strip()

    def _generate_dependency_imports(self, dependencies: list[str]) -> list[str]:
        """Generate import statements from dependency names."""
        imports = []
        for dep in dependencies:
            if "." in dep:
                # e.g., "os.path" → "from os import path"
                parts = dep.rsplit(".", 1)
                imports.append(f"from {parts[0]} import {parts[1]}")
            else:
                imports.append(f"import {dep}")
        return imports

    def _extract_symbols(self, content: str) -> list[str]:
        """Extract function and class names from code."""
        symbols = []
        for match in FUNC_DEF_RE.finditer(content):
            symbols.append(match.group(1))
        for match in CLASS_DEF_RE.finditer(content):
            symbols.append(match.group(1))
        return symbols

    def _replace_symbol(self, content: str, symbol: str, new_code: str) -> str:
        """Replace a function or class definition in content."""
        # Find the symbol definition
        pattern = rf"(^(?:async\s+)?def\s+{re.escape(symbol)}\s*\(|^class\s+{re.escape(symbol)}[\s(:])"
        match = re.search(pattern, content, re.MULTILINE)
        if not match:
            return content + "\n\n\n" + new_code

        start = match.start()

        # Find the end of the symbol (next top-level def/class or EOF)
        rest = content[match.end():]
        next_match = re.search(r"^\S", rest, re.MULTILINE)
        if next_match:
            end = match.end() + next_match.start()
        else:
            end = len(content)

        return content[:start] + new_code + "\n\n" + content[end:].lstrip("\n")

    def _add_decorator_before(self, content: str, symbol: str, decorator: str) -> str:
        """Add a decorator before a function/class definition."""
        pattern = rf"(^(?:async\s+)?def\s+{re.escape(symbol)}\s*\(|^class\s+{re.escape(symbol)}[\s(:])"
        match = re.search(pattern, content, re.MULTILINE)
        if not match:
            return content
        return content[:match.start()] + decorator + "\n" + content[match.start():]
