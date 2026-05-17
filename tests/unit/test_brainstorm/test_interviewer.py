"""Tests for galaxy.brainstorm.interviewer."""

from galaxy.brainstorm.interviewer import BrainstormInterviewer
from galaxy.brainstorm.types import BrainstormMode, Idea, IdeaCategory


class TestInterviewerQuestions:
    """Test question generation."""

    def test_get_questions_default(self) -> None:
        interviewer = BrainstormInterviewer()
        questions = interviewer.get_questions(prompt="Build an API", count=3)
        assert len(questions) == 3
        assert all(isinstance(q, str) for q in questions)

    def test_get_questions_respects_count(self) -> None:
        interviewer = BrainstormInterviewer()
        questions = interviewer.get_questions(count=2)
        assert len(questions) == 2

    def test_no_duplicate_questions(self) -> None:
        interviewer = BrainstormInterviewer()
        q1 = interviewer.get_questions(count=3)
        q2 = interviewer.get_questions(count=3)
        # Second call should return different questions (already asked)
        overlap = set(q1) & set(q2)
        assert len(overlap) == 0

    def test_free_form_mode(self) -> None:
        interviewer = BrainstormInterviewer()
        questions = interviewer.get_questions(
            prompt="Build something",
            mode=BrainstormMode.FREE_FORM,
            count=3,
        )
        assert len(questions) == 3

    def test_focus_on_specific_categories(self) -> None:
        interviewer = BrainstormInterviewer()
        questions = interviewer.get_questions(categories=["security"], count=3)
        assert len(questions) > 0

    def test_detects_covered_categories(self) -> None:
        interviewer = BrainstormInterviewer()
        ideas = [
            Idea(title="JWT Authentication", category=IdeaCategory.SECURITY),
            Idea(title="PostgreSQL database", category=IdeaCategory.DEPENDENCY),
        ]
        questions = interviewer.get_questions(existing_ideas=ideas, count=5)
        # Should NOT ask auth or data questions since those are covered
        for q in questions:
            assert "authentication" not in q.lower() or "database" not in q.lower()

    def test_reset(self) -> None:
        interviewer = BrainstormInterviewer()
        q1 = interviewer.get_questions(count=3)
        interviewer.reset()
        q2 = interviewer.get_questions(count=3)
        # After reset, should get same questions again
        assert q1 == q2


class TestInterviewerFollowUp:
    """Test follow-up question generation."""

    def test_follow_up_missing_description(self) -> None:
        interviewer = BrainstormInterviewer()
        idea = Idea(title="JWT Auth", description="")
        questions = interviewer.get_follow_up(idea)
        assert any("describe" in q.lower() or "detail" in q.lower() for q in questions)

    def test_follow_up_missing_priority(self) -> None:
        interviewer = BrainstormInterviewer()
        idea = Idea(title="Feature X", priority=0)
        questions = interviewer.get_follow_up(idea)
        assert any("important" in q.lower() for q in questions)

    def test_follow_up_complete_idea(self) -> None:
        interviewer = BrainstormInterviewer()
        idea = Idea(
            title="JWT Auth",
            description="Full JWT implementation",
            priority=1,
            tags=["auth"],
            dependencies=["user_model"],
        )
        questions = interviewer.get_follow_up(idea)
        # Should have fewer questions for a complete idea
        assert len(questions) == 0


class TestInterviewerGapAnalysis:
    """Test gap analysis functionality."""

    def test_gap_analysis_empty(self) -> None:
        interviewer = BrainstormInterviewer()
        analysis = interviewer.generate_gap_analysis("Build an API", [])
        assert len(analysis["missing_categories"]) > 0
        assert analysis["total_ideas"] == 0

    def test_gap_analysis_with_ideas(self) -> None:
        interviewer = BrainstormInterviewer()
        ideas = [
            Idea(title="JWT Auth", category=IdeaCategory.SECURITY),
            Idea(title="FastAPI backend", category=IdeaCategory.ARCHITECTURE),
        ]
        analysis = interviewer.generate_gap_analysis("Build an API", ideas)
        assert "security" in analysis["covered_categories"]
        assert "architecture" in analysis["covered_categories"]
        assert analysis["total_ideas"] == 2

    def test_gap_analysis_keyword_detection(self) -> None:
        interviewer = BrainstormInterviewer()
        ideas = [
            Idea(title="Docker deployment", description="Deploy with Docker Compose"),
        ]
        analysis = interviewer.generate_gap_analysis("API", ideas)
        assert "deployment" in analysis["covered_categories"]

    def test_gap_analysis_suggestions(self) -> None:
        interviewer = BrainstormInterviewer()
        analysis = interviewer.generate_gap_analysis("Build an API", [])
        assert len(analysis["suggestions"]) > 0
        assert all("Consider" in s for s in analysis["suggestions"])
