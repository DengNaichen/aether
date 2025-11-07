"""Mastery Service - Responsible for managing knowledge graph and BKT updates.

This service handles all mastery-related operations:
- Creating and updating user-knowledge node relationships
- Applying Bayesian Knowledge Tracing (BKT) algorithm
- Managing mastery scores and progression
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import app.models.neo4j_model as neo
from app.helper.bayesian_knowledge import BayesianKnowledgeTracer
from app.worker.grading_service import GradingResult


class MasteryService:
    """Service for managing knowledge mastery using BKT algorithm.

    This service is responsible for:
    1. Fetching/creating mastery relationships between users and knowledge nodes
    2. Applying BKT algorithm to update mastery scores
    3. Propagating mastery updates through the knowledge graph

    It does NOT:
    - Grade answers (that's GradingService's job)
    - Manage quiz attempts (that's the handler's job)
    """

    def update_mastery_from_grading(
        self,
        user: neo.User,
        question_id: str,
        grading_result: GradingResult
    ) -> Optional[neo.KnowledgeNode]:
        """Update mastery level based on a grading result.

        This method:
        1. Fetches the question and its associated knowledge node
        2. Gets or creates the mastery relationship
        3. Applies BKT algorithm to update mastery score
        4. Saves the updated relationship

        TODO: When implementing propagation algorithm, change return type to MasteryUpdateResult
              that includes (knowledge_node, old_score, new_score, is_correct).
              This will enable propagation to prerequisites, parents, and dependents.

        Args:
            user: The Neo4j user node
            question_id: UUID of the question that was answered
            grading_result: Result from GradingService containing correctness and BKT params

        Returns:
            The KnowledgeNode that was updated, or None if question has no knowledge node
        """
        # Fetch the question node - try each concrete type since Question is abstract
        question_node = neo.MultipleChoice.nodes.get_or_none(
            question_id=str(question_id)
        )

        if not question_node:
            question_node = neo.FillInBlank.nodes.get_or_none(
                question_id=str(question_id)
            )

        if not question_node:
            question_node = neo.Calculation.nodes.get_or_none(
                question_id=str(question_id)
            )

        if not question_node:
            logging.warning(
                f"Question {question_id} not found when updating mastery"
            )
            return None

        # Get the associated knowledge node
        knode = question_node.knowledge_node.get()

        if not knode:
            logging.warning(
                f"Question {question_id} is not associated with any knowledge node, "
                f"skipping mastery update"
            )
            return None

        # Update the mastery relationship
        self._update_mastery_relationship(
            user=user,
            knowledge_node=knode,
            is_correct=grading_result.is_correct,
            p_g=grading_result.p_g,
            p_s=grading_result.p_s
        )

        return knode

    @staticmethod
    def _update_mastery_relationship(
        user: neo.User,
        knowledge_node: neo.KnowledgeNode,
        is_correct: bool,
        p_g: float,
        p_s: float
    ) -> None:
        """Update the mastery relationship between user and knowledge node.

        This is the core BKT update logic that:
        1. Gets or creates the mastery relationship
        2. Reads current BKT parameters (p_l0, p_t)
        3. Applies BKT algorithm to calculate new mastery score
        4. Updates the relationship with new score and timestamp

        TODO: When implementing propagation, change return type to (old_score, new_score)
              so the caller can determine if propagation is needed based on score change.

        Args:
            user: The user node
            knowledge_node: The knowledge node to update mastery for
            is_correct: Whether the answer was correct
            p_g: Probability of guessing (from question)
            p_s: Probability of slip (from question)
        """
        # Get or create mastery relationship
        rel = user.mastery.relationship(knowledge_node)

        if not rel:
            logging.info(
                f"Creating mastery relationship between user {user.user_id} "
                f"and knowledge node {knowledge_node.node_id}"
            )
            rel = user.mastery.connect(knowledge_node)

        # Read current BKT parameters from the relationship
        p_l0 = rel.p_l0  # Prior probability of knowing
        p_t = rel.p_t    # Probability of learning/transition

        # Apply Bayesian Knowledge Tracing algorithm
        # Note: BayesianKnowledgeTracer expects (p_l0, p_t, p_g, p_s)
        tracker = BayesianKnowledgeTracer(p_l0, p_t, p_g, p_s)
        new_score = tracker.update(is_correct)

        # Update the relationship
        rel.score = new_score
        rel.last_update = datetime.now(timezone.utc)
        rel.save()

        logging.debug(
            f"Updated mastery for user {user.user_id} on node "
            "{knowledge_node.node_id}: "
            f"score={new_score:.3f}, correct={is_correct}"
        )

    @staticmethod
    def get_mastery_score(
        user: neo.User,
        knowledge_node: neo.KnowledgeNode
    ) -> Optional[float]:
        """Get the current mastery score for a user-knowledge node pair.

        Args:
            user: The user node
            knowledge_node: The knowledge node

        Returns:
            Current mastery score (0.0-1.0) or None if no relationship exists
        """
        rel = user.mastery.relationship(knowledge_node)

        if not rel:
            return None

        return rel.score

    @staticmethod
    def initialize_mastery(
        user: neo.User,
        knowledge_node: neo.KnowledgeNode,
        initial_score: float = 0.2,
        p_l0: float = 0.3,
        p_t: float = 0.1
    ) -> None:
        """Initialize a mastery relationship with custom parameters.

        This is useful for:
        - Setting up new users in a course
        - Manual mastery adjustments
        - Pre-testing to establish baseline

        Args:
            user: The user node
            knowledge_node: The knowledge node
            initial_score: Initial mastery score (default 0.5)
            p_l0: Prior probability of knowing (default 0.5)
            p_t: Probability of transition/learning (default 0.1)
        """
        rel = user.mastery.relationship(knowledge_node)

        if rel:
            logging.warning(
                f"Mastery relationship already exists between user {user.user_id} "
                f"and node {knowledge_node.node_id}, updating instead"
            )
        else:
            rel = user.mastery.connect(knowledge_node)

        rel.score = initial_score
        rel.p_l0 = p_l0
        rel.p_t = p_t
        rel.last_update = datetime.now(timezone.utc)
        rel.save()

        logging.info(
            f"Initialized mastery for user {user.user_id} on node {knowledge_node.node_id}"
        )

    # ==================== Mastery Propagation ====================

    def propagate_mastery(
        self,
        user: neo.User,
        knowledge_node: neo.KnowledgeNode,
        is_correct: bool
    ) -> None:
        """Propagate mastery updates through the knowledge graph.

        Based on the propagation algorithm documented in mastery_level_propagation.md.

        This triggers two types of propagation:
        1. HAS_SUBTOPIC (bottom-up aggregation): Recalculate parent topic mastery
        2. IS_PREREQUISITE_FOR (logical inference):
           - Backward: Boost prerequisites if correct
           - Forward: Update p_l0 for dependent nodes

        Args:
            user: The user node
            knowledge_node: The knowledge node that was just updated
            is_correct: Whether the answer was correct
        """
        logging.info(
            f"Starting propagation for user {user.user_id} on node {knowledge_node.node_id}"
        )

        # Type 1: Bottom-up aggregation through HAS_SUBTOPIC hierarchy
        self._propagate_to_parents(user, knowledge_node)

        # Type 2A: Backward propagation to prerequisites
        if is_correct:
            self._propagate_to_prerequisites(user, knowledge_node)
        # Type 2A: If incorrect, we don't update prerequisites,
        # just flag for recommendation
        # (Recommendation engine is handled elsewhere)

        # Type 2B: Forward propagation - update p_l0 for dependent nodes
        self._update_dependent_p_l0(user, knowledge_node)

        logging.info(
            f"Completed propagation for user {user.user_id} on node {knowledge_node.node_id}"
        )

    def _propagate_to_prerequisites(
        self,
        user: neo.User,
        knowledge_node: neo.KnowledgeNode
    ) -> None:
        """Backward propagation: Boost prerequisite nodes when answer is correct.

        Algorithm from docs:
        When a user answers correctly on a node, we infer they likely understood
        the prerequisite skills. Apply BKT "Correct" update to all prerequisites
        as if the user had answered a question for each prerequisite correctly.

        Args:
            user: The user node
            knowledge_node: The knowledge node that was answered correctly
        """
        # Find all prerequisites: (prereq) -[:IS_PREREQUISITE_FOR]-> (knowledge_node)
        prerequisites = knowledge_node.prerequisites.all()

        if not prerequisites:
            logging.debug(
                f"Node {knowledge_node.node_id} has no prerequisites, skipping backward propagation"
            )
            return

        logging.info(
            f"Backward propagation: Found {len(prerequisites)} prerequisites "
            f"for node {knowledge_node.node_id}"
        )

        for prereq_node in prerequisites:
            # Get or create mastery relationship for prerequisite
            rel = user.mastery.relationship(prereq_node)

            if not rel:
                # If user has never been assessed on this prerequisite, create it
                logging.info(
                    f"Creating mastery relationship for prerequisite {prereq_node.node_id}"
                )
                rel = user.mastery.connect(prereq_node)

            # Read current parameters
            old_score = rel.score
            p_l0 = rel.p_l0
            p_t = rel.p_t

            # Use default p_g and p_s for inference (assume medium difficulty)
            p_g = 0.25  # Default guess probability
            p_s = 0.1   # Default slip probability

            # Apply BKT update as if user answered correct on this prerequisite
            # Note: BayesianKnowledgeTracer expects (p_l0, p_t, p_g, p_s)
            tracker = BayesianKnowledgeTracer(old_score, p_t, p_g, p_s)
            new_score = tracker.update(correct=True)

            # Update the relationship
            rel.score = new_score
            rel.last_update = datetime.now(timezone.utc)
            rel.save()

            logging.debug(
                f"Boosted prerequisite {prereq_node.node_id}: "
                f"{old_score:.3f} -> {new_score:.3f}"
            )

            # Recursively propagate upward from this prerequisite
            self._propagate_to_parents(user, prereq_node)

    def _propagate_to_parents(
        self,
        user: neo.User,
        knowledge_node: neo.KnowledgeNode
    ) -> None:
        """Bottom-up propagation: Recalculate parent topic mastery.

        Algorithm from docs:
        Parent mastery = Σ(subtopic_mastery * HAS_SUBTOPIC.weight)

        This is recursive - updating a parent may trigger updates to its parents.

        Args:
            user: The user node
            knowledge_node: The subtopic node that was updated
        """
        # Find all parent topics: (parent) -[:HAS_SUBTOPIC]-> (knowledge_node)
        parent_rels = knowledge_node.parent_topic.all_relationships(knowledge_node)

        if not parent_rels:
            logging.debug(
                f"Node {knowledge_node.node_id} has no parent topics, "
                f"stopping upward propagation"
            )
            return

        logging.debug(
            f"Upward propagation: Found {len(parent_rels)} parent topics "
            f"for node {knowledge_node.node_id}"
        )

        for parent_rel in parent_rels:
            parent_node = parent_rel.start_node()

            # Get all subtopics of this parent
            subtopic_rels = parent_node.subtopic.all_relationships(parent_node)

            # Calculate weighted sum of all subtopic masteries
            weighted_sum = 0.0
            total_weight = 0.0

            for subtopic_rel in subtopic_rels:
                subtopic_node = subtopic_rel.end_node()
                weight = subtopic_rel.weight

                # Get user's mastery on this subtopic
                mastery_rel = user.mastery.relationship(subtopic_node)

                if mastery_rel:
                    subtopic_score = mastery_rel.score
                else:
                    # If user hasn't been assessed on this subtopic, use 0
                    subtopic_score = 0.0

                weighted_sum += subtopic_score * weight
                total_weight += weight

            # Calculate new parent mastery
            if total_weight > 0:
                # normalization
                new_parent_score = weighted_sum / total_weight
            else:
                new_parent_score = 0.0

            # Update or create parent mastery relationship
            parent_mastery_rel = user.mastery.relationship(parent_node)

            if not parent_mastery_rel:
                logging.info(
                    f"Creating mastery relationship for parent {parent_node.node_id}"
                )
                parent_mastery_rel = user.mastery.connect(parent_node)

            old_parent_score = parent_mastery_rel.score
            parent_mastery_rel.score = new_parent_score
            parent_mastery_rel.last_update = datetime.now(timezone.utc)
            parent_mastery_rel.save()

            logging.debug(
                f"Updated parent {parent_node.node_id}: "
                f"{old_parent_score:.3f} -> {new_parent_score:.3f} "
                f"(weighted sum of {len(subtopic_rels)} subtopics)"
            )

            # Recursively propagate to grandparents
            self._propagate_to_parents(user, parent_node)

    def _update_dependent_p_l0(
        self,
        user: neo.User,
        knowledge_node: neo.KnowledgeNode
    ) -> None:
        """Forward propagation: Update p_l0 for dependent nodes.

        Algorithm from docs:
        When a user masters a prerequisite node, we should increase the prior
        knowledge probability (p_l0) for all dependent nodes that require this
        prerequisite. This reflects that mastering prerequisites improves the
        likelihood of already knowing the dependent skills.

        The p_l0 update is based on:
        1. The user's current mastery score on the prerequisite
        2. The weight/importance of the prerequisite relationship
        3. Only affects nodes the user hasn't been assessed on yet (or has low mastery)

        Args:
            user: The user node
            knowledge_node: The prerequisite node that was just updated
        """
        # Find all dependent nodes that have current node as their prerequisite
        # In neomodel:
        # - prerequisites = RelationshipTo: (node)-[:IS_PREREQUISITE_FOR]->(its_prereq)
        # - is_prerequisite_for = RelationshipFrom: (node)<-[:IS_PREREQUISITE_FOR]-(dependent)
        # So when we call node_a.is_prerequisite_for.connect(node_b),
        # it creates: (node_b)-[:IS_PREREQUISITE_FOR]->(node_a)
        # meaning node_a is a prerequisite of node_b
        #
        # We want to find nodes that have current node as prerequisite:
        # (dependent)-[:IS_PREREQUISITE_FOR]->(knowledge_node)

        query = """
        MATCH (dependent:KnowledgeNode)-[:IS_PREREQUISITE_FOR]->
              (prereq:KnowledgeNode {node_id: $node_id})
        RETURN dependent
        """

        from neomodel import db
        results, _ = db.cypher_query(
            query,
            {"node_id": knowledge_node.node_id}
        )

        if not results:
            logging.debug(
                f"Node {knowledge_node.node_id} has no dependent nodes, "
                f"skipping forward propagation"
            )
            return

        dependent_nodes = [neo.KnowledgeNode.inflate(row[0]) for row in results]

        logging.info(
            f"Forward propagation: Found {len(dependent_nodes)} dependent nodes "
            f"for node {knowledge_node.node_id}"
        )

        # Get current mastery score on this prerequisite
        prerequisite_rel = user.mastery.relationship(knowledge_node)
        if not prerequisite_rel:
            logging.debug(
                f"User has no mastery on prerequisite {knowledge_node.node_id}, "
                f"skipping forward propagation"
            )
            return

        prerequisite_mastery = prerequisite_rel.score

        # Only propagate if prerequisite mastery is reasonably high
        if prerequisite_mastery < 0.5:
            logging.debug(
                f"Prerequisite {knowledge_node.node_id} mastery too low "
                f"({prerequisite_mastery:.3f}), skipping forward propagation"
            )
            return

        # Update p_l0 for each dependent node
        for dependent_node in dependent_nodes:
            # Get or create mastery relationship for dependent node
            dependent_rel = user.mastery.relationship(dependent_node)

            if not dependent_rel:
                # User hasn't been assessed on this node yet
                # Create the relationship with updated p_l0
                dependent_rel = user.mastery.connect(dependent_node)
                old_p_l0 = dependent_rel.p_l0
            else:
                old_p_l0 = dependent_rel.p_l0

            # Calculate new p_l0 based on prerequisite mastery
            # Formula: new_p_l0 = old_p_l0 + (prerequisite_mastery - old_p_l0) * influence
            # influence_factor represents how much the prerequisite affects the dependent
            influence_factor = 0.3  # Conservative influence (30%)

            # New p_l0 should be bounded between old value and prerequisite mastery
            p_l0_boost = (prerequisite_mastery - old_p_l0) * influence_factor
            new_p_l0 = min(0.9, max(old_p_l0, old_p_l0 + p_l0_boost))

            # Update the p_l0
            dependent_rel.p_l0 = new_p_l0
            dependent_rel.last_update = datetime.now(timezone.utc)
            dependent_rel.save()

            logging.debug(
                f"Updated p_l0 for dependent {dependent_node.node_id}: "
                f"{old_p_l0:.3f} -> {new_p_l0:.3f} "
                f"(based on prerequisite mastery {prerequisite_mastery:.3f})"
            )
