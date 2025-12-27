from datetime import timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from fsrs import Card, Rating, State

from app.domain.mastery_logic import MasteryLogic
from app.models.user import FSRSState, UserMastery
from app.utils.time_utils import get_now


class TestMasteryLogic:
    def test_build_fsrs_card_new(self):
        """Verify a new card is created with default values when no prior review exists.

        Expected:
            - Card state is State.Learning.
            - Step is 0.
        """
        mastery = UserMastery(
            user_id=uuid4(),
            graph_id=uuid4(),
            node_id=uuid4(),
            last_review=None,
            fsrs_state=FSRSState.LEARNING.value,
        )

        card = MasteryLogic.build_fsrs_card(mastery)

        assert isinstance(card, Card)
        # New cards default to State.Learning (1) in fsrs-python
        # (State.New does not exist in this version)
        assert card.state == State.Learning
        assert card.step == 0

    def test_build_fsrs_card_existing(self):
        """Verify an existing card is reconstructed correctly from DB fields.

        Expected:
            - Card properties match the database record exactly.
        """
        node_id = uuid4()
        now = get_now()
        mastery = UserMastery(
            user_id=uuid4(),
            graph_id=uuid4(),
            node_id=node_id,
            last_review=now,
            fsrs_state=FSRSState.REVIEW.value,
            fsrs_stability=5.0,
            fsrs_difficulty=6.0,
            due_date=now + timedelta(days=5),
        )

        card = MasteryLogic.build_fsrs_card(mastery)

        assert card.state == State.Review
        assert card.stability == 5.0
        assert card.difficulty == 6.0
        # Check date approximate equality (fsrs stores as naive or formatted strings internally sometimes)
        # But Card.due is a datetime
        assert card.due.year == mastery.due_date.year
        assert card.due.month == mastery.due_date.month
        assert card.due.day == mastery.due_date.day

    def test_card_id_stability(self):
        """Verify card_id is generated deterministically from node_id.int.

        This ensures that FSRS internal consistent hashing works even across
        server restarts (unlike Python's random hash()).

        Expected:
            - Same node_id produces identical card_id.
            - card_id equals node_id.int % 10^12.
        """
        node_id = uuid4()
        mastery = UserMastery(
            user_id=uuid4(),
            graph_id=uuid4(),
            node_id=node_id,
            # Need last_review to trigger the card_dict building logic
            last_review=get_now(),
            fsrs_state=FSRSState.LEARNING.value,
        )

        card1 = MasteryLogic.build_fsrs_card(mastery)
        card2 = MasteryLogic.build_fsrs_card(mastery)

        # 1. Stability check
        assert card1.card_id == card2.card_id

        # 2. Algo check: it should be int % 10^12
        expected_id = node_id.int % (10**12)
        assert card1.card_id == expected_id

    def test_step_persistence(self):
        """Verify that 'step' is correctly recovered from the review_log.

        Crucial for multi-step learning phases to prevent infinite loops.

        Expected:
            - Card step matches the last value in review_log.
        """
        node_id = uuid4()
        mastery = UserMastery(
            user_id=uuid4(),
            graph_id=uuid4(),
            node_id=node_id,
            last_review=get_now(),
            fsrs_state=FSRSState.LEARNING.value,
            # Simulate a log where we were at step 1
            review_log=[
                {"rating": 1, "state_after": "learning", "step": 0},
                {"rating": 3, "state_after": "learning", "step": 1},
            ],
        )

        card = MasteryLogic.build_fsrs_card(mastery)

        assert card.step == 1

    def test_step_persistence_missing_log(self):
        """Verify default step is 0 if logs are missing or malformed.

        Expected:
            - Card step defaults to 0.
        """
        mastery = UserMastery(
            user_id=uuid4(),
            graph_id=uuid4(),
            node_id=uuid4(),
            last_review=get_now(),
            fsrs_state=FSRSState.LEARNING.value,
            review_log=[],
        )
        card = MasteryLogic.build_fsrs_card(mastery)
        assert card.step == 0

        mastery.review_log = [{"rating": 3}]  # Missing 'step' key
        card = MasteryLogic.build_fsrs_card(mastery)
        assert card.step == 0

    def test_calculate_next_state_correct_basic(self):
        """Verify basic FSRS update on a correct answer.

        Expected:
            - Stability and difficulty are updated.
            - Review is logged with rating and step.
        """
        now = get_now()
        mastery = UserMastery(
            user_id=uuid4(),
            graph_id=uuid4(),
            node_id=uuid4(),
            last_review=None,  # New card
            fsrs_state=FSRSState.LEARNING.value,
        )

        updates = MasteryLogic.calculate_next_state(
            mastery=mastery, is_correct=True, p_g=0.0, p_s=0.0, now=now
        )

        assert (
            updates["fsrs_state"] == FSRSState.LEARNING.value
        )  # First good on new card -> still Learning
        assert updates["fsrs_stability"] is not None
        assert updates["last_review"] == now
        # Check review log
        assert "review_log_entry" in updates
        assert updates["review_log_entry"]["rating"] == Rating.Good.value
        # Ensure step is recorded
        assert "step" in updates["review_log_entry"]

    def test_guessing_adjustment(self):
        """Verify stability gain is damped when p_g (guessing probability) is high.

        Expected:
            - New stability is lower than pure FSRS update would suggest.
            - Damping follows formula: gain * (1 - p_g).
        """
        now = get_now()

        # Create a card in REVIEW state with some stability
        # We need to manually construct a state where stability will INCREASE
        # so we can test the damping.
        # Actually easiest is to trust the logic: logic only runs if new > old.
        # We can unit test the logic block by mocking review_card return?
        # Or just run a scenario we know increases stability (e.g. Good review).

        # Let's use a mock scheduler to control the "new card" values perfectly
        # avoiding dependency on FSRS internal math for this specific test.

        # Store original scheduler
        original_scheduler = MasteryLogic._fsrs_scheduler
        mock_scheduler = MagicMock()
        MasteryLogic._fsrs_scheduler = mock_scheduler

        try:
            old_stability = 5.0
            new_undamped_stability = 10.0
            p_g = 0.5

            # Setup mastery
            mastery = UserMastery(
                user_id=uuid4(),
                graph_id=uuid4(),
                node_id=uuid4(),
                last_review=now,
                fsrs_state=FSRSState.REVIEW.value,
                fsrs_stability=old_stability,
                fsrs_difficulty=5.0,
            )

            # Mock return of review_card
            mock_new_card = Card()
            mock_new_card.stability = new_undamped_stability
            mock_new_card.state = State.Review
            mock_scheduler.review_card.return_value = (mock_new_card, None)
            mock_scheduler.get_card_retrievability.return_value = 0.9

            # Run
            updates = MasteryLogic.calculate_next_state(
                mastery=mastery, is_correct=True, p_g=p_g, p_s=0.0, now=now
            )

            # Expected calc:
            # gain = 10 - 5 = 5
            # damped_gain = 5 * (1 - 0.5) = 2.5
            # final = 5 + 2.5 = 7.5

            assert updates["fsrs_stability"] == 7.5

        finally:
            # Restore scheduler
            MasteryLogic._fsrs_scheduler = original_scheduler

    def test_slipping_adjustment(self):
        """Verify stability is recovered when p_s (slip probability) is high on incorrect answer.

        Expected:
            - Stability drop is mitigated correctly.
            - New stability is capped at old stability.
        """
        now = get_now()
        original_scheduler = MasteryLogic._fsrs_scheduler
        mock_scheduler = MagicMock()
        MasteryLogic._fsrs_scheduler = mock_scheduler

        try:
            old_stability = 10.0
            # FSRS usually slashes stability on fail, e.g. to 6.0
            new_raw_stability = 6.0
            p_s = 0.4

            mastery = UserMastery(
                user_id=uuid4(),
                graph_id=uuid4(),
                node_id=uuid4(),
                last_review=now,
                fsrs_state=FSRSState.REVIEW.value,
                fsrs_stability=old_stability,
                fsrs_difficulty=5.0,
            )

            mock_new_card = Card()
            mock_new_card.stability = new_raw_stability
            mock_new_card.state = State.Relearning
            mock_scheduler.review_card.return_value = (mock_new_card, None)
            mock_scheduler.get_card_retrievability.return_value = 0.5

            updates = MasteryLogic.calculate_next_state(
                mastery=mastery,
                is_correct=False,  # Incorrect
                p_g=0.0,
                p_s=p_s,
                now=now,
            )

            # Logic:
            # recovery_factor = p_s * 0.5 = 0.2
            # recovery_stability = new_card.stability + (old_stability * recovery_factor)
            #                    = 6.0 + (10.0 * 0.2) = 8.0
            # Check cap (min(8.0, 10.0)) -> 8.0

            assert updates["fsrs_stability"] == 8.0

        finally:
            MasteryLogic._fsrs_scheduler = original_scheduler
