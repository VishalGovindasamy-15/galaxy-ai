"""Prompt Expander — transforms vague prompts into structured specs.

Stage 1 of the cognitive pipeline. Takes a raw user prompt and
produces an ExpandedSpec with project type, tech stack, features,
constraints, and domain suggestions.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from galaxy.cognitive.types import ExpandedSpec, PipelineStage, StageResult, StageStatus

logger = logging.getLogger(__name__)

EXPANDER_SYSTEM_PROMPT = """\
You are a senior software architect. Given a vague project description,
produce a structured engineering specification.

Output a JSON object with these fields:
- project_type: string (e.g. "REST API", "CLI tool", "web app")
- tech_stack: list of strings
- features: list of feature descriptions
- constraints: list of constraints
- non_functional: list of non-functional requirements
- domains: list of domain names for the agent hierarchy
- ambiguities: list of things that need clarification

Output ONLY valid JSON. No explanations.
"""

# ─── Keyword-based expansion (no LLM needed) ────────────────────────────────

TECH_KEYWORDS: dict[str, list[str]] = {
    "api": ["FastAPI", "Python", "Pydantic"],
    "rest": ["FastAPI", "Python", "Pydantic"],
    "web": ["React", "TypeScript", "Vite"],
    "frontend": ["React", "TypeScript", "CSS"],
    "backend": ["FastAPI", "Python", "SQLAlchemy"],
    "cli": ["Python", "Click", "Rich"],
    "database": ["PostgreSQL", "SQLAlchemy"],
    "auth": ["JWT", "bcrypt"],
    "docker": ["Docker", "Docker Compose"],
    "test": ["pytest", "coverage"],
    "graphql": ["Strawberry", "GraphQL"],
    "websocket": ["WebSocket", "asyncio"],
    "microservice": ["FastAPI", "Docker", "Redis"],
}

DOMAIN_KEYWORDS: dict[str, str] = {
    "auth": "auth",
    "login": "auth",
    "jwt": "auth",
    "user": "auth",
    "database": "database",
    "postgres": "database",
    "sql": "database",
    "model": "database",
    "api": "backend",
    "endpoint": "backend",
    "route": "backend",
    "crud": "backend",
    "react": "frontend",
    "ui": "frontend",
    "component": "frontend",
    "page": "frontend",
    "test": "testing",
    "pytest": "testing",
    "docker": "devops",
    "deploy": "devops",
    "ci": "devops",
}


class PromptExpander:
    """Expands vague prompts into structured engineering specs.

    Can operate in two modes:
    - Keyword-based: Fast, no LLM needed, uses pattern matching
    - LLM-powered: Uses the model for deep analysis (future)
    """

    def expand(self, prompt: str, context: str = "") -> ExpandedSpec:
        """Expand a prompt into a structured spec using keyword analysis.

        Args:
            prompt: Raw user prompt.
            context: Additional context (e.g., from brainstorm spec).

        Returns:
            ExpandedSpec with structured project information.
        """
        prompt_lower = prompt.lower()
        full_text = f"{prompt} {context}".lower()

        spec = ExpandedSpec(original_prompt=prompt)

        # Detect project type
        spec.project_type = self._detect_project_type(prompt_lower)

        # Detect tech stack
        spec.tech_stack = self._detect_tech_stack(full_text)

        # Extract features
        spec.features = self._extract_features(prompt)

        # Detect constraints
        spec.constraints = self._detect_constraints(full_text)

        # Detect non-functional requirements
        spec.non_functional = self._detect_non_functional(full_text)

        # Suggest domains
        spec.domains = self._suggest_domains(full_text)

        # Identify ambiguities
        spec.ambiguities = self._find_ambiguities(spec)

        return spec

    def expand_to_stage_result(self, prompt: str, context: str = "") -> StageResult:
        """Expand and wrap in a StageResult."""
        import time
        start = time.monotonic()

        spec = self.expand(prompt, context)

        duration = (time.monotonic() - start) * 1000
        result = StageResult(
            stage=PipelineStage.EXPAND,
            input_data=prompt,
            output_data=spec.to_prompt(),
            metadata=spec.to_dict(),
        )
        result.complete(spec.to_prompt(), duration)
        return result

    def _detect_project_type(self, prompt: str) -> str:
        type_keywords = {
            "REST API": ["rest api", "api", "endpoint", "crud"],
            "Web Application": ["web app", "website", "frontend", "full-stack", "fullstack"],
            "CLI Tool": ["cli", "command line", "terminal tool"],
            "Microservice": ["microservice", "micro-service"],
            "Library": ["library", "package", "module", "sdk"],
            "Bot": ["bot", "chatbot", "discord", "telegram"],
        }
        for proj_type, keywords in type_keywords.items():
            if any(kw in prompt for kw in keywords):
                return proj_type
        return "Application"

    def _detect_tech_stack(self, text: str) -> list[str]:
        stack: set[str] = set()
        for keyword, techs in TECH_KEYWORDS.items():
            if keyword in text:
                stack.update(techs)
        return sorted(stack) if stack else ["Python"]

    def _extract_features(self, prompt: str) -> list[str]:
        features = []
        # Look for comma-separated or "and"-separated items
        # e.g., "user auth, CRUD endpoints, and tests"
        parts = re.split(r",\s*(?:and\s+)?|\s+and\s+", prompt)
        for part in parts:
            part = part.strip()
            # Strip leading verb prefixes
            cleaned = re.sub(
                r"^(?:build|create|make|implement|add|set up|develop)\s+",
                "",
                part,
                flags=re.IGNORECASE,
            ).strip()
            if len(cleaned) > 3:
                features.append(cleaned)

        if not features:
            features.append(prompt.strip())

        return features

    def _detect_constraints(self, text: str) -> list[str]:
        constraints = []
        constraint_patterns = {
            "must use": "Must use: ",
            "require": "Requirement: ",
            "only": "Constraint: ",
            "no ": "Exclusion: ",
            "without": "Exclusion: ",
        }
        for keyword, prefix in constraint_patterns.items():
            if keyword in text:
                # Find the sentence containing the keyword
                for sentence in text.split("."):
                    if keyword in sentence:
                        constraints.append(sentence.strip())
                        break
        return constraints

    def _detect_non_functional(self, text: str) -> list[str]:
        nfr = []
        nfr_keywords = {
            "security": "Security requirements detected",
            "performance": "Performance requirements detected",
            "scalab": "Scalability requirements detected",
            "production": "Production-grade quality required",
            "enterprise": "Enterprise-grade requirements",
            "real-time": "Real-time capabilities required",
        }
        for keyword, desc in nfr_keywords.items():
            if keyword in text:
                nfr.append(desc)
        return nfr

    def _suggest_domains(self, text: str) -> list[str]:
        domains: set[str] = set()
        for keyword, domain in DOMAIN_KEYWORDS.items():
            if keyword in text:
                domains.add(domain)
        if not domains:
            domains.add("backend")
        return sorted(domains)

    def _find_ambiguities(self, spec: ExpandedSpec) -> list[str]:
        ambiguities = []
        if not spec.tech_stack or spec.tech_stack == ["Python"]:
            ambiguities.append("Tech stack not fully specified")
        if len(spec.features) <= 1:
            ambiguities.append("Feature list is vague — needs decomposition")
        if not spec.constraints:
            ambiguities.append("No explicit constraints mentioned")
        if spec.project_type == "Application":
            ambiguities.append("Project type is ambiguous")
        return ambiguities
