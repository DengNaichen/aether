class BayesianKnowledgeTracer:
    """Bayesian Knowledge Tracing model for estimating learner knowledge state.

    This class implements a Bayesian Knowledge Tracing (BKT) algorithm that updates
    the probability of a learner knowing a skill based on their performance on
    practice problems. It uses Bayesian inference to update knowledge estimates.

    Attributes:
        p_l (float): Current probability that the learner has mastered the skill.
        p_t (float): Transition (learning) probability - probability of learning
            the skill after attempting a problem.
        p_g (float): Guess probability - probability of answering correctly
            without knowing the skill.
        p_s (float): Slip probability - probability of answering incorrectly
            despite knowing the skill.
    """

    def __init__(self, p_l0, p_t, p_g, p_s):
        """Initialize the Bayesian Knowledge Tracer.

        Args:
            p_l0 (float): Prior knowledge probability - initial probability that
                the learner has mastered the skill. Must not be zero.
            p_t (float): Transition (learning) probability - probability of
                learning the skill after attempting a problem.
            p_g (float): Guess probability - probability of answering correctly
                without knowing the skill.
            p_s (float): Slip probability - probability of answering incorrectly
                despite knowing the skill.
            forgetting_lambda (float, optional): Decay constant for the forgetting
                curve. Defaults to 0.099.

        Raises:
            AssertionError: If p_l0 is zero.
        """
        assert p_l0 != 0
        self.p_l = p_l0
        self.p_t = p_t
        self.p_g = p_g
        self.p_s = p_s

    def update(self, correct: bool):
        """Update the knowledge probability based on learner's answer.

        Uses Bayesian inference to update the probability that the learner has
        mastered the skill (p_l) based on whether they answered correctly or
        incorrectly. The update incorporates the guess and slip probabilities
        and applies a learning transition probability.

        Args:
            correct (bool): True if the learner answered correctly, False otherwise.

        Returns:
            float: Updated probability that the learner has mastered the skill.
        """
        if correct:
            # Bayes update if Chloe answer correctly
            numerator = self.p_l * (1 - self.p_s)
            denominator = numerator + (1 - self.p_l) * self.p_g
        else:
            # Bayes update if Chloe answer incorrectly
            numerator = self.p_l * self.p_s
            denominator = numerator + (1 - self.p_l) * (1 - self.p_g)
        if denominator == 0:
            posterior = self.p_l
        else:
            posterior = numerator / denominator

        # Incorporate learning(transition learning)
        self.p_l = posterior + (1 - posterior) * self.p_t
        return self.p_l
