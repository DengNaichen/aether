from neomodel import StructuredNode, StringProperty, ZeroOrOne, RelationshipTo, \
    One, RelationshipFrom, ArrayProperty, IntegerProperty, StructuredRel, FloatProperty, DateTimeProperty

from app.schemas.questions import QuestionDifficulty


class Course(StructuredNode):
    course_id = StringProperty(required=True, unique_index=True)
    course_name = StringProperty(required=True)

    def __str__(self):
        return f"<Course {self.course_name} ({self.course_id})>)"


class HasMastery(StructuredRel):
    score = FloatProperty(default=0.1)
    last_updated = DateTimeProperty(default_now=True)


class User(StructuredNode):
    user_id = StringProperty(required=True, unique_index=True)
    user_name = StringProperty(required=True, unique_index=True)

    enrolled_course = RelationshipTo(
        Course,
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


class MultipleChoice(Question):
    options = ArrayProperty(StringProperty(), required=True)
    correct_answer = IntegerProperty(required=True)


class FillInBlank(Question):
    expected_answer = ArrayProperty(StringProperty(), required=True)


class Calculation(Question):
    expected_answer = ArrayProperty(StringProperty(), required=True)
    precision = IntegerProperty(default=2)


class KnowledgeNode(StructuredNode):

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
        "HAS_PREREQUISITES"
    )

    is_prerequisite_for = RelationshipFrom(
        "KnowledgeNode",
        "HAS_PREREQUISITES"
    )

    subtopic = RelationshipTo(
        "KnowledgeNode",
        "HAS_SUBTOPIC"
    )

    parent_topic = RelationshipFrom(
        "KnowledgeNode",
        "HAS_SUBTOPIC"
    )

    concept_this_is_example_of = RelationshipTo(
        "KnowledgeNode",
        "IS_EXAMPLE_OF"
    )

    example = RelationshipFrom(
        "KnowledgeNode",
        "IS_EXAMPLE_OF"
    )

    questions = RelationshipFrom(
        "Question",
        "TESTS"
    )

    def __str__(self):
        return f"<KnowledgeNode {self.node_name} ({self.node_id})>"
