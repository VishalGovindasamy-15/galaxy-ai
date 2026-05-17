"""Integrator engine — orchestrates chunk merging into complete files.

Manages file states, coordinates the merger and conflict resolver,
and produces the final assembled project files.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from galaxy.contracts.types import CodeChunk, ChunkStatus
from galaxy.integrator import ConflictResolution, FileState, MergeResult
from galaxy.integrator.conflict import ConflictDetector, ConflictResolver
from galaxy.integrator.merger import ChunkMerger

logger = logging.getLogger(__name__)


class IntegratorEngine:
    """Orchestrates the chunk → file integration pipeline.

    Manages file states across the project, coordinates merging,
    detects and resolves conflicts, and writes final output.

    Usage:
        engine = IntegratorEngine()
        engine.integrate(chunk1)
        engine.integrate(chunk2)
        files = engine.get_all_files()
        engine.write_all(output_dir)
    """

    def __init__(self) -> None:
        self._file_states: dict[str, FileState] = {}
        self._merger = ChunkMerger()
        self._detector = ConflictDetector()
        self._resolver = ConflictResolver()
        self._results: list[MergeResult] = []

    @property
    def file_count(self) -> int:
        """Number of files being tracked."""
        return len(self._file_states)

    @property
    def total_chunks_merged(self) -> int:
        """Total chunks merged across all files."""
        return sum(len(fs.chunk_ids) for fs in self._file_states.values())

    def get_file_state(self, path: str) -> FileState | None:
        """Get the current state of a file."""
        return self._file_states.get(path)

    def get_all_files(self) -> dict[str, str]:
        """Get all assembled file contents.

        Returns:
            Dict mapping file path → assembled content.
        """
        result = {}
        for path, state in self._file_states.items():
            result[path] = self._merger.assemble_file(state)
        return result

    def integrate(self, chunk: CodeChunk) -> MergeResult:
        """Integrate a single code chunk.

        Detects conflicts, auto-resolves them, and merges the chunk.

        Args:
            chunk: The code chunk to integrate.

        Returns:
            MergeResult with merge details.
        """
        file_state = self._file_states.get(chunk.target_file)
        if file_state is None:
            file_state = FileState(path=chunk.target_file)
            self._file_states[chunk.target_file] = file_state

        # Detect conflicts
        conflicts = self._detector.detect(chunk, file_state)

        # Auto-resolve conflicts
        for conflict in conflicts:
            self._resolver.auto_resolve(conflict)
            logger.info(
                "Auto-resolved %s conflict in %s for symbol '%s'",
                conflict.conflict_type.value,
                conflict.file_path,
                conflict.symbol_name,
            )

        # Merge chunk
        result = self._merger.merge_chunk(chunk, file_state)
        result.conflicts = conflicts
        self._results.append(result)

        logger.debug(
            "Integrated chunk %s → %s (%d symbols, %d imports)",
            chunk.id,
            chunk.target_file,
            len(result.symbols_added),
            len(result.imports_added),
        )

        return result

    def integrate_batch(self, chunks: list[CodeChunk]) -> list[MergeResult]:
        """Integrate multiple chunks, grouped by target file.

        Args:
            chunks: List of code chunks to integrate.

        Returns:
            List of MergeResults (one per file).
        """
        # Group by target file
        by_file: dict[str, list[CodeChunk]] = {}
        for chunk in chunks:
            by_file.setdefault(chunk.target_file, []).append(chunk)

        results = []
        for file_path, file_chunks in by_file.items():
            file_state = self._file_states.get(file_path)
            if file_state is None:
                file_state = FileState(path=file_path)
                self._file_states[file_path] = file_state

            # Detect batch conflicts
            conflicts = self._detector.detect_batch(file_chunks, file_state)
            for conflict in conflicts:
                self._resolver.auto_resolve(conflict)

            # Merge all chunks for this file
            result = self._merger.merge_chunks(file_chunks, file_state)
            result.conflicts = conflicts
            results.append(result)
            self._results.append(result)

        return results

    def write_all(self, output_dir: Path) -> list[Path]:
        """Write all assembled files to disk.

        Args:
            output_dir: Base directory for output.

        Returns:
            List of written file paths.
        """
        written: list[Path] = []
        files = self.get_all_files()

        for rel_path, content in files.items():
            full_path = output_dir / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            written.append(full_path)
            logger.debug("Wrote: %s", full_path)

        logger.info("Wrote %d files to %s", len(written), output_dir)
        return written

    def get_summary(self) -> dict[str, Any]:
        """Get integration summary statistics."""
        total_conflicts = sum(len(r.conflicts) for r in self._results)
        resolved = sum(
            1 for r in self._results
            for c in r.conflicts
            if c.is_resolved
        )
        return {
            "files": self.file_count,
            "chunks_merged": self.total_chunks_merged,
            "total_conflicts": total_conflicts,
            "resolved_conflicts": resolved,
            "symbols": {
                path: state.symbols
                for path, state in self._file_states.items()
            },
        }

    def reset(self) -> None:
        """Reset all state."""
        self._file_states.clear()
        self._results.clear()
