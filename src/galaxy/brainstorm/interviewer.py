"""Brainstorm interviewer — Master asks clarifying questions.

During brainstorming, the interviewer generates intelligent questions
to help the user refine their ideas and uncover missing requirements.
Uses the LLM to analyze current ideas and identify gaps.
"""

from __future__ import annotations

import logging
from typing import Any

from galaxy.brainstorm.types import BrainstormMode, Idea, IdeaCategory

logger = logging.getLogger(__name__)

# ─── Prompt Templates ────────────────────────────────────────────────────────

INTERVIEW_SYSTEM_PROMPT = """\
You are a senior software architect conducting a brainstorming interview.
Your goal is to help the user refine their project idea by asking smart,
targeted questions that uncover missing requirements, constraints, and
architectural decisions.

Rules:
- Ask ONE clear question at a time
- Focus on what's missing or ambiguous
- Suggest concrete options when possible
- Be concise and direct
"""

QUESTION_GENERATION_PROMPT = """\
The user wants to build: {prompt}

Current approved ideas:
{ideas_summary}

Current gaps/concerns:
{gaps}

Generate {count} targeted questions to help refine this project.
Focus on: architecture decisions, missing features, constraints,
security concerns, and scalability requirements.

Return ONLY the questions, one per line, numbered.
"""


# ─── Predefined Question Templates ──────────────────────────────────────────

STRUCTURED_QUESTIONS: dict[str, list[str]] = {
    "architecture": [
        "What's the primary backend framework? (FastAPI, Django, Flask, Express, etc.)",
        "What database do you want to use? (PostgreSQL, MySQL, SQLite, MongoDB, etc.)",
        "Do you need a frontend? If so, what framework? (React, Vue, Next.js, etc.)",
        "Should this be a monolith or microservices architecture?",
        "Do you need real-time features? (WebSocket, Server-Sent Events)",
    ],
    "auth": [
        "What authentication method? (JWT, OAuth2, Session-based, API keys)",
        "Do you need role-based access control (RBAC)?",
        "Do you need social login? (Google, GitHub, etc.)",
    ],
    "data": [
        "What are the main data entities/models?",
        "Do you need file uploads or media storage?",
        "Do you need caching? (Redis, Memcached)",
        "What's the expected data volume? (small/medium/large)",
    ],
    "deployment": [
        "Where will this be deployed? (AWS, GCP, self-hosted, Docker)",
        "Do you need CI/CD? (GitHub Actions, GitLab CI)",
        "Do you need containerization? (Docker, Kubernetes)",
    ],
    "security": [
        "What's the security requirement level? (basic/standard/high)",
        "Do you need rate limiting?",
        "Do you need input validation/sanitization?",
        "Do you need audit logging?",
    ],
    "testing": [
        "What test coverage do you need? (unit/integration/e2e)",
        "Do you need API documentation? (OpenAPI/Swagger)",
    ],
}


class BrainstormInterviewer:
    """Generates clarifying questions during brainstorming.

    Can operate in two modes:
    - Template-based: Uses predefined question sets (no LLM needed)
    - LLM-powered: Uses the model to generate context-aware questions

    Usage:
        interviewer = BrainstormInterviewer()
        questions = interviewer.get_questions(
            prompt="Build a REST API",
            existing_ideas=[...],
            mode=BrainstormMode.STRUCTURED,
        )
    """

    def __init__(self) -> None:
        self._asked_questions: set[str] = set()

    def get_questions(
        self,
        prompt: str = "",
        existing_ideas: list[Idea] | None = None,
        mode: BrainstormMode = BrainstormMode.STRUCTURED,
        count: int = 3,
        categories: list[str] | None = None,
    ) -> list[str]:
        """Get clarifying questions based on current state.

        Args:
            prompt: The user's project prompt.
            existing_ideas: Ideas already in the session.
            mode: Brainstorming mode.
            count: Number of questions to generate.
            categories: Specific question categories to focus on.

        Returns:
            List of question strings.
        """
        ideas = existing_ideas or []

        if mode == BrainstormMode.FREE_FORM:
            return self._get_open_questions(prompt, count)

        # Determine which categories have gaps
        covered = self._detect_covered_categories(ideas)
        gaps = self._get_gap_categories(covered, categories)

        questions = []
        for gap_category in gaps:
            category_qs = STRUCTURED_QUESTIONS.get(gap_category, [])
            for q in category_qs:
                if q not in self._asked_questions and len(questions) < count:
                    questions.append(q)
                    self._asked_questions.add(q)

        return questions[:count]

    def get_follow_up(self, idea: Idea) -> list[str]:
        """Get follow-up questions for a specific idea.

        Args:
            idea: The idea to ask follow-ups about.

        Returns:
            List of follow-up questions.
        """
        questions = []

        if not idea.description:
            questions.append(f"Can you describe '{idea.title}' in more detail?")

        if idea.priority == 0:
            questions.append(f"How important is '{idea.title}'? (1=critical, 5=nice-to-have)")

        if not idea.tags:
            questions.append(f"Any specific tags or keywords for '{idea.title}'?")

        if idea.category == IdeaCategory.FEATURE and not idea.dependencies:
            questions.append(f"Does '{idea.title}' depend on any other features?")

        return questions

    def generate_gap_analysis(
        self,
        prompt: str,
        existing_ideas: list[Idea],
    ) -> dict[str, Any]:
        """Analyze what's missing from the current idea set.

        Args:
            prompt: Original user prompt.
            existing_ideas: Current ideas.

        Returns:
            Dictionary with covered/missing categories and suggestions.
        """
        covered = self._detect_covered_categories(existing_ideas)
        all_categories = set(STRUCTURED_QUESTIONS.keys())
        missing = all_categories - covered

        return {
            "covered_categories": sorted(covered),
            "missing_categories": sorted(missing),
            "total_ideas": len(existing_ideas),
            "categories_detail": {
                cat: len([i for i in existing_ideas if self._idea_matches_category(i, cat)])
                for cat in all_categories
            },
            "suggestions": [
                f"Consider adding {cat} specifications"
                for cat in sorted(missing)
            ],
        }

    def reset(self) -> None:
        """Reset the interviewer state (clear asked questions)."""
        self._asked_questions.clear()

    def _detect_covered_categories(self, ideas: list[Idea]) -> set[str]:
        """Detect which question categories are already covered by ideas."""
        covered: set[str] = set()

        category_map = {
            IdeaCategory.ARCHITECTURE: "architecture",
            IdeaCategory.SECURITY: "security",
            IdeaCategory.TESTING: "testing",
            IdeaCategory.DEVOPS: "deployment",
            IdeaCategory.DEPENDENCY: "data",
        }

        for idea in ideas:
            if idea.category in category_map:
                covered.add(category_map[idea.category])

            # Also check tags and title for keyword matching
            text = f"{idea.title} {idea.description}".lower()
            if any(kw in text for kw in ["auth", "login", "jwt", "oauth"]):
                covered.add("auth")
            if any(kw in text for kw in ["database", "postgres", "mysql", "mongo"]):
                covered.add("data")
            if any(kw in text for kw in ["docker", "deploy", "ci/cd", "kubernetes"]):
                covered.add("deployment")
            if any(kw in text for kw in ["test", "coverage", "pytest"]):
                covered.add("testing")

        return covered

    def _get_gap_categories(
        self,
        covered: set[str],
        focus: list[str] | None = None,
    ) -> list[str]:
        """Get categories that need more questions."""
        all_cats = list(STRUCTURED_QUESTIONS.keys())

        if focus:
            return [c for c in focus if c in all_cats]

        # Prioritize uncovered categories
        uncovered = [c for c in all_cats if c not in covered]
        return uncovered if uncovered else all_cats

    def _get_open_questions(self, prompt: str, count: int) -> list[str]:
        """Generate open-ended questions for free-form mode."""
        return [
            f"What's the most important feature of this project?",
            f"Who is the target user?",
            f"What's the expected scale? (users, requests/sec)",
            f"What constraints do you have? (budget, timeline, tech stack)",
            f"Any specific non-functional requirements? (security, performance, accessibility)",
        ][:count]

    def _idea_matches_category(self, idea: Idea, category: str) -> bool:
        """Check if an idea is related to a question category."""
        text = f"{idea.title} {idea.description}".lower()
        keywords: dict[str, list[str]] = {
            "architecture": ["architecture", "framework", "monolith", "microservice"],
            "auth": ["auth", "login", "jwt", "oauth", "session"],
            "data": ["database", "postgres", "mysql", "mongo", "redis", "cache"],
            "deployment": ["docker", "deploy", "ci/cd", "kubernetes", "aws"],
            "security": ["security", "encrypt", "vulnerability", "rate limit"],
            "testing": ["test", "coverage", "pytest", "jest", "e2e"],
        }
        return any(kw in text for kw in keywords.get(category, []))
