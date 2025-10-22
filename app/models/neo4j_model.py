from neomodel import StructuredNode, StringProperty, ZeroOrOne, RelationshipTo


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

