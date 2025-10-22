from neomodel import StructuredNode, StringProperty, ZeroOrOne, RelationshipTo, One, RelationshipFrom


class Course(StructuredNode):
    course_id = StringProperty(required=True, unique_index=True)
    course_name = StringProperty(required=True)

    def __str__(self):
        return f"<Course {self.course_name} ({self.course_id})>)"


class User(StructuredNode):
    user_id = StringProperty(required=True, unique_index=True)
    user_name = StringProperty(required=True, unique_index=True)

    enrolled_course = RelationshipTo(
        Course,
        "ENROLLED_IN",
        cardinality=ZeroOrOne
    )

    def __str__(self):
        return f"<User {self.user_name} ({self.user_id})>"


class KnowledgeNode(StructuredNode):

    node_id = StringProperty(required=True, unique_index=True)
    node_name = StringProperty(required=True)

    description = StringProperty()

    course = RelationshipTo(
        Course,
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

    def __str__(self):
        return f"<KnowledgeNode {self.node_name} ({self.node_id})>"


