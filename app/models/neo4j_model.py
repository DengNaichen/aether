"""
Neo4j graph database models for the adaptive learning system.

This module defines the knowledge graph structure including:
- KnowledgeNode: Concepts and topics in the curriculum
- Question types: MultipleChoice, FillInBlank, Calculation
- User: Students with mastery tracking
- Course: Top-level curriculum containers

The graph supports two key relationship types:
1. IS_PREREQUISITE_FOR: Defines prerequisite dependencies between concepts
2. HAS_SUBTOPIC: Defines hierarchical topic decomposition

Mastery tracking uses Bayesian Knowledge Tracing (BKT) with parameters:
- p_l0: Prior knowledge probability
- p_t: Learning transition probability
- p_g: Guess probability (question-specific)
- p_s: Slip probability (question-specific)
"""

from neomodel import StructuredNode, StringProperty, ZeroOrOne, RelationshipTo, \
    One, RelationshipFrom, ArrayProperty, IntegerProperty, StructuredRel, FloatProperty, DateTimeProperty

from app.schemas.questions import QuestionDifficulty


def validate_probability(value):
    """Validator for probability values - must be between 0.0 and 1.0."""
    if value is None:
        return value
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Probability must be between 0.0 and 1.0, got {value}")
    return value


def validate_weight(value):
    """Validator for weight values - must be between 0.0 and 1.0."""
    if value is None:
        return value
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Weight must be between 0.0 and 1.0, got {value}")
    return value


class Course(StructuredNode):
    """
    Represents a course or curriculum container.

    A course groups related knowledge nodes and provides a top-level
    organizational structure for the knowledge graph.

    Attributes:
        course_id: Unique identifier for the course
        course_name: Human-readable name of the course
    """
    course_id = StringProperty(required=True, unique_index=True)
    course_name = StringProperty(required=True)

    def __str__(self):
        return f"<Course {self.course_name} ({self.course_id})>)"


class HasMastery(StructuredRel):
    """
    Relationship between User and KnowledgeNode tracking mastery level.

    This relationship stores the current mastery state and BKT parameters
    for a specific user on a specific knowledge node.

    Attributes:
        score: Current mastery probability (0.0 to 1.0), representing P(L_t)
        p_l0: Prior knowledge probability (0.0 to 1.0) - initial mastery before any practice
        p_t: Transition probability (0.0 to 1.0) - chance of learning from practice
        last_updated: Timestamp of last mastery update (for forgetting curve)

    Constraints:
        - All probability values must be between 0.0 and 1.0

    Note:
        - p_g (guess) and p_s (slip) are stored on Question, not here
        - p_l0 should be dynamically calculated from prerequisites
        - score decays over time using forgetting curve: P_new = P_old * e^(-0.099 * days)
    """
    score = FloatProperty(default=0.1, validator=validate_probability)

    p_l0 = FloatProperty(default=0.2, validator=validate_probability)
    p_t = FloatProperty(default=0.2, validator=validate_probability)

    last_updated = DateTimeProperty(default_now=True)


class User(StructuredNode):
    """
    Represents a student in the adaptive learning system.

    Users enroll in courses and build mastery relationships with knowledge nodes
    as they practice and answer questions.

    Attributes:
        user_id: Unique identifier for the user
        user_name: Display name for the user

    Relationships:
        enrolled_course: The course this user is currently studying (0 or 1)
        mastery: Knowledge nodes the user has practiced, with mastery scores
    """
    user_id = StringProperty(required=True, unique_index=True)
    user_name = StringProperty(required=True, unique_index=True)

    enrolled_course = RelationshipTo(
        "Course",
        "ENROLLED_IN",
        cardinality=ZeroOrOne
    )

    mastery = RelationshipTo(
        "KnowledgeNode",
        "HAS_MASTERY_ON",
        model=HasMastery,
    )

    def __str__(self):
        return f"<User {self.user_name} ({self.user_id})>"


class Question(StructuredNode):
    """
    Abstract base class for all question types.

    Questions are linked to leaf knowledge nodes and used to assess mastery.
    Each question type implements its own p_g (guess probability) based on
    its format characteristics.

    Attributes:
        question_id: Unique identifier for the question
        text: The question prompt text
        difficulty: Question difficulty level (easy, medium, hard)
        p_s: Slip probability (0.0 to 1.0) - chance of careless error despite knowing the material

    Relationships:
        knowledge_node: The leaf knowledge node this question tests

    Properties:
        p_g: Guess probability (0.0 to 1.0) - must be implemented by subclasses

    Constraints:
        - p_s must be between 0.0 and 1.0
        - p_g (from subclasses) must return value between 0.0 and 1.0

    Note:
        Questions should only link to LEAF nodes (nodes with no subtopics)
    """
    __abstract_node__ = True

    question_id = StringProperty(required=True, unique_index=True)
    text = StringProperty(required=True)
    difficulty = StringProperty(
        required=True,
        choices={d.value: d.name for d in QuestionDifficulty}
    )

    knowledge_node = RelationshipTo(
        "KnowledgeNode",
        "TESTS",
        cardinality=One
    )

    p_s = FloatProperty(default=0.1, validator=validate_probability)

    @property
    def p_g(self):
        raise NotImplementedError


class IsPrerequisiteFor(StructuredRel):
    """
    Relationship indicating one knowledge node is prerequisite for another.

    Structure: (NodeA) -[:IS_PREREQUISITE_FOR]-> (NodeB)
    Meaning: NodeA must be learned before NodeB

    Attributes:
        weight: Importance of the prerequisite (0.0 to 1.0)
                1.0 = critical prerequisite (must master)
                < 1.0 = supplementary prerequisite (helpful but not required)
                Default 1.0 treats all prerequisites as critical

    Constraints:
        - weight must be between 0.0 and 1.0

    Used for:
        - Backward propagation: When NodeB is answered correctly, boost NodeA mastery
        - Forward propagation: Calculate p_l0 for NodeB based on NodeA mastery
        - Recommendation: When NodeB fails, flag NodeA for testing
    """
    weight = FloatProperty(default=1.0, validator=validate_weight)


class HasSubtopic(StructuredRel):
    """
    Relationship indicating hierarchical topic decomposition.

    Structure: (ParentTopic) -[:HAS_SUBTOPIC]-> (Subtopic)
    Meaning: Subtopic is a component of ParentTopic

    Attributes:
        weight: Contribution of subtopic to parent (0.0 to 1.0)
                All subtopic weights for a parent should sum to 1.0
                Used to calculate parent mastery as weighted sum

    Constraints:
        - weight must be between 0.0 and 1.0
        - Sum of all subtopic weights for a parent MUST equal 1.0
          (validated at service layer, not database level)

    Example:
        If "Algebra" has subtopics "Linear Equations" (0.4) and "Quadratics" (0.6),
        then Mastery(Algebra) = 0.4 * Mastery(Linear) + 0.6 * Mastery(Quadratics)
    """
    weight = FloatProperty(required=True, validator=validate_weight)


class MultipleChoice(Question):
    """
    Multiple choice question with one correct answer.

    Attributes:
        options: List of answer choices
        correct_answer: Index of the correct option (0-based)

    Properties:
        p_g: Calculated as 1/n_options (e.g., 0.25 for 4 choices)
    """
    options = ArrayProperty(StringProperty(), required=True)
    correct_answer = IntegerProperty(required=True)

    @property
    def p_g(self):
        if not self.options:
            return 0
        return 1.0/len(self.options)


class FillInBlank(Question):
    """
    Fill-in-the-blank question requiring text input.

    Attributes:
        expected_answer: List of acceptable answers (for flexibility)
        _p_g: Guess probability (0.0 to 1.0, very low since guessing text is hard)

    Properties:
        p_g: Defaults to 0.01 (1% chance of guessing correctly)

    Constraints:
        - _p_g must be between 0.0 and 1.0
    """
    expected_answer = ArrayProperty(StringProperty(), required=True)
    _p_g = FloatProperty(default=0.01, validator=validate_probability)

    @property
    def p_g(self):
        return self._p_g


class Calculation(Question):
    """
    Numerical calculation question requiring mathematical computation.

    Attributes:
        expected_answer: List of acceptable numerical answers (as strings)
        precision: Number of decimal places for answer matching
        _p_g: Guess probability (0.0 to 1.0, very low for calculation problems)

    Properties:
        p_g: Defaults to 0.01 (1% chance of guessing correctly)

    Constraints:
        - _p_g must be between 0.0 and 1.0
    """
    expected_answer = ArrayProperty(StringProperty(), required=True)
    precision = IntegerProperty(default=2)

    _p_g = FloatProperty(default=0.01, validator=validate_probability)

    @property
    def p_g(self):
        return self._p_g


class KnowledgeNode(StructuredNode):
    """
    Represents a concept or topic in the knowledge graph.

    Knowledge nodes form two types of hierarchies:
    1. Prerequisite dependencies (IS_PREREQUISITE_FOR)
    2. Topic decomposition (HAS_SUBTOPIC)

    Leaf nodes (no subtopics) are linked to questions for assessment.
    Parent nodes have mastery calculated as weighted sum of subtopics.

    Attributes:
        node_id: Unique identifier for the node
        node_name: Human-readable name of the concept
        description: Detailed explanation (useful for LLM-based features)

    Relationships:
        course: The course this node belongs to
        prerequisites: Concepts that must be learned before this one
        is_prerequisite_for: Concepts that require this one as prerequisite
        subtopic: Child concepts that compose this topic
        parent_topic: Parent topics that this node is part of
        questions: Assessment questions for this node (leaf nodes only)

    Propagation Rules:
        - Correct answer: Boosts this node and its prerequisites
        - Incorrect answer: Updates this node, flags prerequisites for testing
        - Mastery change: Triggers parent recalculation and forward p_l0 updates
    """
    node_id = StringProperty(required=True, unique_index=True)
    node_name = StringProperty(required=True)

    description = StringProperty()

    course = RelationshipTo(
        "Course",
        "BELONGS_TO",
        cardinality=One
    )

    prerequisites = RelationshipTo(
        "KnowledgeNode",
        "IS_PREREQUISITE_FOR",
        model=IsPrerequisiteFor,
    )

    is_prerequisite_for = RelationshipFrom(
        "KnowledgeNode",
        "IS_PREREQUISITE_FOR",
        model=IsPrerequisiteFor,
    )

    subtopic = RelationshipTo(
        "KnowledgeNode",
        "HAS_SUBTOPIC",
        model=HasSubtopic,
    )

    parent_topic = RelationshipFrom(
        "KnowledgeNode",
        "HAS_SUBTOPIC",
        model=HasSubtopic,
    )

    questions = RelationshipFrom(
        "Question",
        "TESTS"
    )

    def __str__(self):
        return f"<KnowledgeNode {self.node_name} ({self.node_id})>"
