"""Course Service - Responsible for managing courses and enrollments in Neo4j.

This service handles all course-related operations:
- Creating and updating courses
- Enrolling and managing users
- Retrieving course and enrollment information
"""

import logging
from typing import Optional
from dataclasses import dataclass

from neomodel import DoesNotExist

import app.models.neo4j_model as neo


@dataclass
class CourseOperationResult:
    """Result of a course creation/update operation.

    Attributes:
        course: The Course node that was created or updated
        created: True if a new course was created, False if existing was
        updated: True if an existing course was updated, False otherwise
    """
    course: neo.Course
    created: bool
    updated: bool


@dataclass
class EnrollmentResult:
    """Result of a user enrollment operation.

    Attributes:
        user: The User node that was enrolled
        course: The Course node the user was enrolled in
        user_created: True if a new user was created, False if existing
        user_updated: True if existing user info was updated
        already_enrolled: True if user was already enrolled
    """
    user: neo.User
    course: neo.Course
    user_created: bool
    user_updated: bool
    already_enrolled: bool


class CourseService:
    """Service for managing courses and enrollments in the Neo4j knowledge graph.

    This service is responsible for:
    1. Creating and updating courses
    2. Creating and updating users
    3. Managing enrollment relationships between users and courses
    4. Retrieving course and enrollment information

    It does NOT:
    - Handle mastery tracking (that's MasteryService's job)
    - Grade submissions (that's GradingService's job)
    """

    # ==================== Course Management ====================
    @staticmethod
    def create_or_update_course(
        course_id: str,
        course_name: str
    ) -> CourseOperationResult:
        """Create a new course or update an existing one.

        This method:
        1. Checks if a course with the given ID exists
        2. If not, creates a new course
        3. If yes, updates the course name if it has changed

        Args:
            course_id: Unique identifier for the course
            course_name: Display name for the course

        Returns:
            CourseOperationResult with the course node and operation status
        """
        try:
            # Try to find existing course
            course_node = neo.Course.nodes.get(course_id=course_id)
            created = False
            updated = False

            logging.debug(f"Found existing course: {course_id}")

            # Update course name if it has changed
            if course_name != course_node.course_name:
                logging.info(
                    f"Updating course name for {course_id}: "
                    f"'{course_node.course_name}' -> '{course_name}'"
                )
                course_node.course_name = course_name
                course_node.save()
                updated = True

        except DoesNotExist:
            # Course doesn't exist, create new one
            logging.info(f"Creating new course: {course_id}")
            course_node = neo.Course(
                course_id=course_id,
                course_name=course_name
            ).save()
            created = True
            updated = False

        return CourseOperationResult(
            course=course_node,
            created=created,
            updated=updated
        )

    @staticmethod
    def get_course(course_id: str) -> Optional[neo.Course]:
        """Get a course by its ID.

        Args:
            course_id: Unique identifier for the course

        Returns:
            Course node if found, None otherwise
        """
        course_node = neo.Course.nodes.get_or_none(course_id=course_id)
        if course_node:
            logging.debug(f"Retrieved course: {course_id}")
        else:
            logging.warning(f"Course not found: {course_id}")
        return course_node

    @staticmethod
    def course_exists(course_id: str) -> bool:
        """Check if a course exists.

        Args:
            course_id: Unique identifier for the course

        Returns:
            True if the course exists, False otherwise
        """
        return neo.Course.nodes.get_or_none(course_id=course_id) is not None

    @staticmethod
    def list_all_courses() -> list[neo.Course]:
        """List all courses in the system.

        Returns:
            List of all Course nodes
        """
        courses = neo.Course.nodes.all()
        logging.debug(f"Retrieved {len(courses)} courses")
        return list(courses)

    @staticmethod
    def delete_course(course_id: str) -> bool:
        """Delete a course by its ID.

        WARNING: This will delete the course and all its relationships.
        Use with caution.

        Args:
            course_id: Unique identifier for the course to delete

        Returns:
            True if the course was deleted, False if it didn't exist
        """
        try:
            course_node = neo.Course.nodes.get(course_id=course_id)
            course_node.delete()
            logging.info(f"Deleted course: {course_id}")
            return True
        except DoesNotExist:
            logging.warning(f"Cannot delete - course not found: {course_id}")
            return False

    # ==================== User Management ====================
    @staticmethod
    def create_or_update_user(
        user_id: str,
        user_name: str
    ) -> tuple[neo.User, bool, bool]:
        """Create a new user or update an existing one.

        Args:
            user_id: Unique identifier for the user
            user_name: Display name for the user

        Returns:
            Tuple of (user_node, created, updated)
        """
        try:
            user_node = neo.User.nodes.get(user_id=user_id)
            created = False
            updated = False

            logging.debug(f"Found existing user: {user_id}")

            # Update user name if it has changed
            if user_name != user_node.user_name:
                logging.info(
                    f"Updating user name for {user_id}: "
                    f"'{user_node.user_name}' -> '{user_name}'"
                )
                user_node.user_name = user_name
                user_node.save()
                updated = True

        except DoesNotExist:
            logging.info(f"Creating new user: {user_id}")
            user_node = neo.User(
                user_id=user_id,
                user_name=user_name
            ).save()
            created = True
            updated = False

        return user_node, created, updated

    @staticmethod
    def get_user(user_id: str) -> Optional[neo.User]:
        """Get a user by their ID.

        Args:
            user_id: Unique identifier for the user

        Returns:
            User node if found, None otherwise
        """
        user_node = neo.User.nodes.get_or_none(user_id=user_id)
        if user_node:
            logging.debug(f"Retrieved user: {user_id}")
        else:
            logging.warning(f"User not found: {user_id}")
        return user_node

    # ==================== Enrollment Management ====================

    def enroll_user_in_course(
        self,
        user_id: str,
        user_name: str,
        course_id: str
    ) -> EnrollmentResult:
        """Enroll a user in a course.

        This method:
        1. Validates that the course exists
        2. Creates or updates the user
        3. Creates the enrollment relationship (ENROLLED_IN)

        Args:
            user_id: Unique identifier for the user
            user_name: Display name for the user
            course_id: Unique identifier for the course

        Returns:
            EnrollmentResult with details of the operation

        Raises:
            ValueError: If the course does not exist
        """
        # Check if course exists
        course_node = neo.Course.nodes.get_or_none(course_id=course_id)
        if not course_node:
            raise ValueError(f"Course '{course_id}' does not exist")

        # Create or update user
        user_node, user_created, user_updated = self.create_or_update_user(
            user_id, user_name
        )

        # Check if already enrolled
        already_enrolled = user_node.enrolled_course.is_connected(course_node)

        if not already_enrolled:
            # Enroll the user
            user_node.enrolled_course.connect(course_node)
            logging.info(f"Enrolled user {user_id} in course {course_id}")
        else:
            logging.debug(f"User {user_id} already enrolled in course {course_id}")

        return EnrollmentResult(
            user=user_node,
            course=course_node,
            user_created=user_created,
            user_updated=user_updated,
            already_enrolled=already_enrolled
        )

    def unenroll_user_from_course(
        self,
        user_id: str,
        course_id: str
    ) -> bool:
        """Unenroll a user from a course.

        Args:
            user_id: Unique identifier for the user
            course_id: Unique identifier for the course

        Returns:
            True if the user was unenrolled, False if they weren't enrolled
        """
        user_node = neo.User.nodes.get_or_none(user_id=user_id)
        course_node = neo.Course.nodes.get_or_none(course_id=course_id)

        if not user_node or not course_node:
            logging.warning(
                f"Cannot unenroll - user {user_id} or course {course_id} not found"
            )
            return False

        if user_node.enrolled_course.is_connected(course_node):
            user_node.enrolled_course.disconnect(course_node)
            logging.info(f"Unenrolled user {user_id} from course {course_id}")
            return True
        else:
            logging.debug(f"User {user_id} was not enrolled in course {course_id}")
            return False

    def is_user_enrolled(self, user_id: str, course_id: str) -> bool:
        """Check if a user is enrolled in a course.

        Args:
            user_id: Unique identifier for the user
            course_id: Unique identifier for the course

        Returns:
            True if the user is enrolled, False otherwise
        """
        user_node = neo.User.nodes.get_or_none(user_id=user_id)
        course_node = neo.Course.nodes.get_or_none(course_id=course_id)

        if not user_node or not course_node:
            return False

        return user_node.enrolled_course.is_connected(course_node)

    def get_enrolled_course(self, user_id: str) -> Optional[neo.Course]:
        """Get the course a user is enrolled in.

        Note: Based on the model, a user can only be enrolled in one course at a time
        (cardinality=ZeroOrOne).

        Args:
            user_id: Unique identifier for the user

        Returns:
            Course node if user is enrolled in a course, None otherwise
        """
        user_node = neo.User.nodes.get_or_none(user_id=user_id)
        if not user_node:
            logging.warning(f"User not found: {user_id}")
            return None

        # Get the enrolled course (single or none)
        enrolled_course = user_node.enrolled_course.single_or_none()

        if enrolled_course:
            logging.debug(f"User {user_id} enrolled in course {enrolled_course.course_id}")
        else:
            logging.debug(f"User {user_id} not enrolled in any course")

        return enrolled_course

    def get_enrolled_students(self, course_id: str) -> list[neo.User]:
        """Get all students enrolled in a course.

        Args:
            course_id: Unique identifier for the course

        Returns:
            List of User nodes enrolled in the course
        """
        course_node = neo.Course.nodes.get_or_none(course_id=course_id)
        if not course_node:
            logging.warning(f"Course not found: {course_id}")
            return []

        # Query users who have ENROLLED_IN relationship to this course
        enrolled_users = neo.User.nodes.filter(
            enrolled_course=course_node
        ).all()

        logging.debug(f"Found {len(enrolled_users)} students in course {course_id}")
        return list(enrolled_users)
