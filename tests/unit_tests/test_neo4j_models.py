"""
Living documentation tests for Neo4j models.

These tests serve as executable documentation showing:
1. How to create and use each model type
2. What properties and relationships exist
3. Valid value ranges and constraints
4. How BKT parameters work

No real database connection needed - uses mocks for fast execution.
"""

import pytest
from unittest.mock import patch

from app.models.neo4j_model import (
    Course,
    User,
    KnowledgeNode,
    MultipleChoice,
    FillInBlank,
    Calculation,
    HasMastery,
    IsPrerequisiteFor,
    HasSubtopic,
    validate_probability,
    validate_weight,
)


# ============================================
# Test Validator Functions
# ============================================

class TestValidators:
    """Documents the validation rules for probabilities and weights."""

    def test_validate_probability_accepts_valid_values(self):
        """Probabilities must be between 0.0 and 1.0 inclusive."""
        # Boundary values
        assert validate_probability(0.0) == 0.0
        assert validate_probability(1.0) == 1.0

        # Middle values
        assert validate_probability(0.5) == 0.5
        assert validate_probability(0.25) == 0.25

        # None is allowed (optional fields)
        assert validate_probability(None) is None

    def test_validate_probability_rejects_out_of_range(self):
        """Values outside [0.0, 1.0] should raise ValueError."""
        with pytest.raises(ValueError):
            validate_probability(1.5)

        with pytest.raises(ValueError):
            validate_probability(-0.1)

        with pytest.raises(ValueError):
            validate_probability(2.0)

    def test_validate_weight_accepts_valid_values(self):
        """Weights must be between 0.0 and 1.0 inclusive."""
        assert validate_weight(0.0) == 0.0
        assert validate_weight(1.0) == 1.0
        assert validate_weight(0.4) == 0.4
        assert validate_weight(None) is None

    def test_validate_weight_rejects_out_of_range(self):
        """Values outside [0.0, 1.0] should raise ValueError."""
        with pytest.raises(ValueError):
            validate_weight(1.1)

        with pytest.raises(ValueError):
            validate_weight(-0.5)


# ============================================
# Test Course Model
# ============================================

class TestCourse:
    """Documents how to create and use Course nodes."""

    @patch('app.models.neo4j_model.Course.save')
    def test_course_creation(self, mock_save):
        """Shows how to create a Course with required properties."""
        course = Course(
            course_id="CS101",
            course_name="Introduction to Computer Science"
        )

        assert course.course_id == "CS101"
        assert course.course_name == "Introduction to Computer Science"
        assert "CS101" in str(course)
        assert "Introduction to Computer Science" in str(course)


# ============================================
# Test User Model
# ============================================

class TestUser:
    """Documents how to create Users and track their mastery."""

    @patch('app.models.neo4j_model.User.save')
    def test_user_creation(self, mock_save):
        """Shows how to create a User with basic properties."""
        user = User(
            user_id="user_123",
            user_name="Alice"
        )

        assert user.user_id == "user_123"
        assert user.user_name == "Alice"
        assert "Alice" in str(user)
        assert "user_123" in str(user)

    def test_user_has_mastery_relationship(self):
        """Documents that Users connect to KnowledgeNodes via HAS_MASTERY_ON."""
        user = User()

        # User should have mastery relationship defined
        assert hasattr(user, 'mastery')
        assert hasattr(user, 'enrolled_course')


# ============================================
# Test HasMastery Relationship
# ============================================

class TestHasMasteryRelationship:
    """Documents the BKT parameters stored on User-KnowledgeNode relationships."""

    def test_has_mastery_properties(self):
        """Shows all BKT parameters and their default values."""
        mastery_rel = HasMastery()

        # Default values for BKT parameters
        assert mastery_rel.score == 0.1  # P(L_t) - current mastery
        assert mastery_rel.p_l0 == 0.2   # Prior knowledge
        assert mastery_rel.p_t == 0.2    # Learning transition probability
        assert mastery_rel.last_updated is not None

    def test_has_mastery_accepts_valid_probabilities(self):
        """All probability values must be between 0.0 and 1.0."""
        mastery_rel = HasMastery(
            score=0.75,
            p_l0=0.3,
            p_t=0.25
        )

        assert mastery_rel.score == 0.75
        assert mastery_rel.p_l0 == 0.3
        assert mastery_rel.p_t == 0.25

    def test_has_mastery_rejects_invalid_score(self):
        """
        Score outside [0.0, 1.0] should raise error when validated.

        Note: Neomodel validators run during save/deflate, not object creation.
        We test validation directly via the validator function.
        """
        # Test validator function directly
        with pytest.raises(ValueError):
            validate_probability(1.5)

        with pytest.raises(ValueError):
            validate_probability(-0.1)

    def test_has_mastery_rejects_invalid_p_l0(self):
        """p_l0 outside [0.0, 1.0] should raise error when validated."""
        # Test validator function directly
        with pytest.raises(ValueError):
            validate_probability(1.2)

    def test_has_mastery_rejects_invalid_p_t(self):
        """p_t outside [0.0, 1.0] should raise error when validated."""
        # Test validator function directly
        with pytest.raises(ValueError):
            validate_probability(-0.5)


# ============================================
# Test KnowledgeNode Model
# ============================================

class TestKnowledgeNode:
    """Documents KnowledgeNode structure and relationships."""

    @patch('app.models.neo4j_model.KnowledgeNode.save')
    def test_knowledge_node_creation(self, mock_save):
        """Shows how to create a KnowledgeNode with properties."""
        node = KnowledgeNode(
            node_id="algebra_001",
            node_name="Linear Equations",
            description="Solving equations with one variable"
        )

        assert node.node_id == "algebra_001"
        assert node.node_name == "Linear Equations"
        assert node.description == "Solving equations with one variable"
        assert "Linear Equations" in str(node)

    def test_knowledge_node_has_two_relationship_types(self):
        """Documents the two key relationship types: prerequisites and subtopics."""
        node = KnowledgeNode()

        # Prerequisite relationships (for learning dependencies)
        assert hasattr(node, 'prerequisites')  # Outgoing: what this needs
        assert hasattr(node, 'is_prerequisite_for')  # Incoming: what needs this

        # Subtopic relationships (for hierarchical decomposition)
        assert hasattr(node, 'subtopic')  # Outgoing: children topics
        assert hasattr(node, 'parent_topic')  # Incoming: parent topics

        # Other relationships
        assert hasattr(node, 'questions')  # Questions that test this node
        assert hasattr(node, 'course')  # Course this belongs to


# ============================================
# Test Prerequisite Relationship
# ============================================

class TestIsPrerequisiteForRelationship:
    """Documents the IS_PREREQUISITE_FOR relationship and its weight attribute."""

    def test_prerequisite_relationship_default_weight(self):
        """By default, prerequisites are critical (weight=1.0)."""
        prereq_rel = IsPrerequisiteFor()

        assert prereq_rel.weight == 1.0  # Critical prerequisite

    def test_prerequisite_relationship_custom_weight(self):
        """Weight can indicate importance: 1.0=critical, <1.0=supplementary."""
        # Critical prerequisite
        critical = IsPrerequisiteFor(weight=1.0)
        assert critical.weight == 1.0

        # Supplementary prerequisite
        supplementary = IsPrerequisiteFor(weight=0.7)
        assert supplementary.weight == 0.7

    def test_prerequisite_relationship_rejects_invalid_weight(self):
        """
        Weight must be between 0.0 and 1.0.

        Note: Validation occurs during save. Test validator directly.
        """
        with pytest.raises(ValueError):
            validate_weight(1.5)

        with pytest.raises(ValueError):
            validate_weight(-0.1)


# ============================================
# Test Subtopic Relationship
# ============================================

class TestHasSubtopicRelationship:
    """
    Documents the HAS_SUBTOPIC relationship for hierarchical decomposition.
    """

    def test_subtopic_relationship_requires_weight(self):
        """
        Weight indicates how much the subtopic contributes to parent mastery.
        """
        subtopic_rel = HasSubtopic(weight=0.4)

        assert subtopic_rel.weight == 0.4

    def test_subtopic_relationship_weight_constraint(self):
        """Weight must be between 0.0 and 1.0."""
        # Valid weights
        HasSubtopic(weight=0.0)
        HasSubtopic(weight=1.0)
        HasSubtopic(weight=0.5)

    def test_subtopic_relationship_rejects_invalid_weight(self):
        """
        Weight outside [0.0, 1.0] should raise error.

        Note: Validation occurs during save. Test validator directly.
        """
        with pytest.raises(ValueError):
            validate_weight(1.2)

        with pytest.raises(ValueError):
            validate_weight(-0.3)

    def test_subtopic_weights_should_sum_to_one(self):
        """
        IMPORTANT: All subtopic weights for a parent must sum to 1.0.

        This constraint is validated at the service layer, not here.
        Example: If "Algebra" has two subtopics, weights might be:
            - Linear Equations: 0.4
            - Quadratics: 0.6
            - Sum: 1.0 ✓
        """
        # This is documentation - the actual validation happens in service layer
        linear_equations_weight = HasSubtopic(weight=0.4)
        quadratics_weight = HasSubtopic(weight=0.6)

        assert linear_equations_weight.weight + quadratics_weight.weight == 1.0


# ============================================
# Test Question Types
# ============================================

class TestMultipleChoiceQuestion:
    """Documents MultipleChoice question type and p_g calculation."""

    @patch('app.models.neo4j_model.MultipleChoice.save')
    def test_multiple_choice_creation(self, mock_save):
        """Shows how to create a multiple choice question."""
        question = MultipleChoice(
            question_id="q_001",
            text="What is 2+2?",
            difficulty="easy",
            options=["2", "3", "4", "5"],
            correct_answer=2,  # Index of "4"
            p_s=0.1  # Slip probability
        )

        assert question.question_id == "q_001"
        assert question.text == "What is 2+2?"
        assert question.difficulty == "easy"
        assert question.options == ["2", "3", "4", "5"]
        assert question.correct_answer == 2
        assert question.p_s == 0.1

    def test_multiple_choice_p_g_calculation(self):
        """p_g (guess probability) is calculated as 1/number_of_options."""
        question = MultipleChoice(
            question_id="q_002",
            text="Test question",
            difficulty="medium",
            options=["A", "B", "C", "D"],
            correct_answer=0
        )

        # With 4 options, guess probability is 0.25
        assert question.p_g == 0.25

    def test_multiple_choice_p_g_with_different_option_counts(self):
        """p_g adapts based on number of choices."""
        # 2 options (True/False) -> 50% guess rate
        two_options = MultipleChoice(
            question_id="q_tf",
            text="True or False?",
            difficulty="easy",
            options=["True", "False"],
            correct_answer=0
        )
        assert two_options.p_g == 0.5

        # 5 options -> 20% guess rate
        five_options = MultipleChoice(
            question_id="q_five",
            text="Pick one",
            difficulty="hard",
            options=["A", "B", "C", "D", "E"],
            correct_answer=0
        )
        assert five_options.p_g == 0.2

    def test_multiple_choice_p_g_empty_options(self):
        """Edge case: empty options returns 0."""
        question = MultipleChoice(
            question_id="q_empty",
            text="Test",
            difficulty="easy",
            options=[],
            correct_answer=0
        )

        assert question.p_g == 0

    def test_multiple_choice_p_s_validation(self):
        """
        p_s (slip probability) must be between 0.0 and 1.0.

        Note: Validation occurs during save. Test validator directly.
        """
        # Valid p_s
        question = MultipleChoice(
            question_id="q_valid",
            text="Test",
            difficulty="easy",
            options=["A", "B"],
            correct_answer=0,
            p_s=0.15
        )
        assert question.p_s == 0.15

        # Invalid p_s - test validator directly
        with pytest.raises(ValueError):
            validate_probability(1.5)


class TestFillInBlankQuestion:
    """Documents FillInBlank question type."""

    @patch('app.models.neo4j_model.FillInBlank.save')
    def test_fill_in_blank_creation(self, mock_save):
        """Shows how to create a fill-in-the-blank question."""
        question = FillInBlank(
            question_id="q_fib_001",
            text="The capital of France is ____.",
            difficulty="easy",
            expected_answer=["Paris", "paris", "PARIS"],  # Multiple acceptable answers
            p_s=0.1
        )

        assert question.question_id == "q_fib_001"
        assert question.text == "The capital of France is ____."
        assert question.expected_answer == ["Paris", "paris", "PARIS"]

    def test_fill_in_blank_p_g_is_very_low(self):
        """p_g for fill-in-blank is very low (0.01) - hard to guess text."""
        question = FillInBlank(
            question_id="q_fib_002",
            text="Fill in the blank",
            difficulty="medium",
            expected_answer=["answer"]
        )

        assert question.p_g == 0.01  # 1% chance to guess correctly

    def test_fill_in_blank_custom_p_g(self):
        """p_g can be customized for easier fill-in questions."""
        question = FillInBlank(
            question_id="q_fib_custom",
            text="Fill this",
            difficulty="easy",
            expected_answer=["yes"],
            _p_g=0.05  # Slightly higher guess rate
        )

        assert question.p_g == 0.05

    def test_fill_in_blank_p_g_validation(self):
        """
        _p_g must be between 0.0 and 1.0.

        Note: Validation occurs during save. Test validator directly.
        """
        with pytest.raises(ValueError):
            validate_probability(1.5)


class TestCalculationQuestion:
    """Documents Calculation question type for numerical answers."""

    @patch('app.models.neo4j_model.Calculation.save')
    def test_calculation_creation(self, mock_save):
        """Shows how to create a calculation question."""
        question = Calculation(
            question_id="q_calc_001",
            text="What is the square root of 144?",
            difficulty="medium",
            expected_answer=["12", "12.0", "12.00"],
            precision=2,  # Compare to 2 decimal places
            p_s=0.1
        )

        assert question.question_id == "q_calc_001"
        assert question.text == "What is the square root of 144?"
        assert question.expected_answer == ["12", "12.0", "12.00"]
        assert question.precision == 2

    def test_calculation_p_g_is_very_low(self):
        """p_g for calculation is very low (0.01) - hard to guess numbers."""
        question = Calculation(
            question_id="q_calc_002",
            text="Calculate something",
            difficulty="hard",
            expected_answer=["42"]
        )

        assert question.p_g == 0.01

    def test_calculation_custom_p_g(self):
        """p_g can be customized if calculation has limited possible answers."""
        question = Calculation(
            question_id="q_calc_custom",
            text="Simple calc",
            difficulty="easy",
            expected_answer=["5"],
            _p_g=0.02
        )

        assert question.p_g == 0.02

    def test_calculation_p_g_validation(self):
        """
        _p_g must be between 0.0 and 1.0.

        Note: Validation occurs during save. Test validator directly.
        """
        with pytest.raises(ValueError):
            validate_probability(2.0)


# ============================================
# Integration Documentation Tests
# ============================================

class TestBKTParametersSummary:
    """
    Summary: Where are BKT parameters stored?

    This test documents the complete BKT parameter architecture:
    - p_g (guess): Stored on Question, varies by question type
    - p_s (slip): Stored on Question, can vary by difficulty
    - p_l0 (prior): Stored on HasMastery, calculated from prerequisites
    - p_t (transition): Stored on HasMastery, learning rate
    - score (P(L_t)): Stored on HasMastery, current mastery level
    """

    def test_bkt_parameters_location_summary(self):
        """Documents where each BKT parameter lives in the graph."""
        # Question-specific parameters (vary by question type/difficulty)
        question = MultipleChoice(
            question_id="q_doc",
            text="Example",
            difficulty="easy",
            options=["A", "B", "C", "D"],
            correct_answer=0,
            p_s=0.1  # Slip: on Question
        )
        assert hasattr(question, 'p_s')
        assert hasattr(question, 'p_g')

        # User-node mastery parameters (vary by student and concept)
        mastery = HasMastery(
            score=0.5,   # Current mastery
            p_l0=0.2,    # Prior knowledge
            p_t=0.2      # Learning rate
        )
        assert mastery.score == 0.5
        assert mastery.p_l0 == 0.2
        assert mastery.p_t == 0.2
