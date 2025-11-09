# Mastery Level Based on Bayesian Knowledge Tracing (BKT) for single node.

## Bayes' Theorem

Bayes' Theorem describes how to update the probability of a hypothesis $H$ based on new evidence $H$:

$$
P(H \mid E) = \frac{P(E \mid H) \cdot P(H)}{P(E)}
$$

**Where:**

- $P(H)$ = prior probability of the hypothesis (before seeing the evidence)
- $P(E \mid H)$ = likelihood of observing the evidence if the hypothesis is true
- $P(E)$ = total probability of observing the evidence
- $P(H \mid E)$ = posterior probability of the hypothesis after observing the evidence

## Bayes' Knowledge Tracking

### Parameters

- **$P(L_0)$ - Prior Knowledge:** The initial probability that Chloe already knows the concept.
    
    *Example:* If $P(L_0) = 0.2$, there is a 20% chance that Chloe understands the material before practicing.
    
- **$P(T)$ - Transition:** The probability that Chloe will learn the knowledge from this practice problem, assuming she didn't know it beforehand.
- **$P(G)$ - Guess:** The probability that Chloe answers correctly by guessing, even if she doesn't know the material.
    
    *Example:* For a multiple-choice question with 4 options, 
    
    $P(G) = 0.25$.
    
- **$P(S)$ - Slip:** The probability that Chloe makes a careless mistake despite knowing the material.

---

To update a student's mastery level for a specific skill, we can use a probabilistic algorithm. This requires defining four key parameters. Assume we have a student called Chloe.

### If Chloe answers correctly:

The updated probability is given by:

$$
P(L_{t} \mid \text{Correct}) = \frac{P(L_{t-1})(1 - P(S))}{P(L_{t-1})(1 - P(S)) + (1 - P(L_{t-1}))P(G)}
$$

**Where:**

- **$P(L_{t-1})$:** Chloe's mastery level *before* this question.
- **$P(L_{t})$:** Chloe's mastery level *after* this question.

**Explanation:**

- **Numerator:** $P(L_{t-1})(1 - P(S))$ — probability that Chloe knew the skill and did not make a slip.
- **Denominator:** $P(L_{t-1})(1 - P(S)) + (1 - P(L_{t-1}))P(G)$ — total probability of a correct answer (either she knew it and didn’t slip, or she guessed correctly).

---

### If Chloe answers incorrectly:

$$
P(L_{t} \mid \text{Incorrect}) = \frac{P(L_{t-1})P(S)}{P(L_{t-1})P(S) + (1 - P(L_{t-1}))(1 - P(G))}
$$

Similar as above

---

### Incorporating Learning from Practice:

After considering the correctness of her answer, we update her mastery with the transition probability $P(T)$:

$$
P(L_t) = P(L_t \mid \text{evidence}) + \big(1 - P(L_t \mid \text{evidence})\big) \cdot P(T)
$$

*Here, "evidence" refers to whether Chloe answered correctly or incorrectly.*

# Forgetting Curve:

$$
P_{\text{new}} = P_{old} \cdot e^{\lambda \cdot -\Delta t}
$$

Assume the half-life is 7 days, the $\lambda = 0.099$. I will use this simple equation as start
