"""Small, inspectable research algorithms used by Pathloom investigations.

The Diagnostic Duel is a Bayesian teaching prototype, not a calibrated clinical
or educational measurement instrument. Likelihoods are authored assumptions and
must be evaluated against labelled student data before any real deployment.
"""

from dataclasses import dataclass
from math import log2

from sympy import expand, roots, symbols


HYPOTHESES = (
    "SUM_PRODUCT_CONFUSION",
    "SIGN_CONFUSION",
    "ROOT_FACTOR_CONFUSION",
    "EXPANSION_DIRECTION_CONFUSION",
)


@dataclass(frozen=True)
class DiagnosticQuestion:
    id: str
    prompt: str
    options: tuple[dict[str, str], ...]
    likelihoods: dict[str, dict[str, float]]
    concept: str = "MATH-ALG-07"


QUESTIONS = (
    DiagnosticQuestion(
        id="duel-product-sum",
        prompt="For x² + 5x + 6, what should a factor pair satisfy?",
        options=(
            {"id": "product_only", "label": "Only multiply to 6"},
            {"id": "sum_only", "label": "Only add to 5"},
            {"id": "both", "label": "Multiply to 6 and add to 5"},
        ),
        likelihoods={
            "SUM_PRODUCT_CONFUSION": {"product_only": 0.62, "sum_only": 0.28, "both": 0.10},
            "SIGN_CONFUSION": {"product_only": 0.20, "sum_only": 0.18, "both": 0.62},
            "ROOT_FACTOR_CONFUSION": {"product_only": 0.25, "sum_only": 0.25, "both": 0.50},
            "EXPANSION_DIRECTION_CONFUSION": {"product_only": 0.30, "sum_only": 0.22, "both": 0.48},
        },
    ),
    DiagnosticQuestion(
        id="duel-signs",
        prompt="Which pair can factor x² − 5x + 6?",
        options=(
            {"id": "positive_pair", "label": "2 and 3"},
            {"id": "negative_pair", "label": "−2 and −3"},
            {"id": "opposite_pair", "label": "−2 and 3"},
        ),
        likelihoods={
            "SUM_PRODUCT_CONFUSION": {"positive_pair": 0.34, "negative_pair": 0.34, "opposite_pair": 0.32},
            "SIGN_CONFUSION": {"positive_pair": 0.12, "negative_pair": 0.68, "opposite_pair": 0.20},
            "ROOT_FACTOR_CONFUSION": {"positive_pair": 0.34, "negative_pair": 0.34, "opposite_pair": 0.32},
            "EXPANSION_DIRECTION_CONFUSION": {"positive_pair": 0.32, "negative_pair": 0.36, "opposite_pair": 0.32},
        },
    ),
    DiagnosticQuestion(
        id="duel-roots",
        prompt="If (x + 2)(x + 3) = 0, what are the roots?",
        options=(
            {"id": "positive_roots", "label": "2 and 3"},
            {"id": "negative_roots", "label": "−2 and −3"},
            {"id": "factor_pair", "label": "The roots are x + 2 and x + 3"},
        ),
        likelihoods={
            "SUM_PRODUCT_CONFUSION": {"positive_roots": 0.30, "negative_roots": 0.38, "factor_pair": 0.32},
            "SIGN_CONFUSION": {"positive_roots": 0.22, "negative_roots": 0.36, "factor_pair": 0.42},
            "ROOT_FACTOR_CONFUSION": {"positive_roots": 0.18, "negative_roots": 0.18, "factor_pair": 0.64},
            "EXPANSION_DIRECTION_CONFUSION": {"positive_roots": 0.30, "negative_roots": 0.34, "factor_pair": 0.36},
        },
    ),
    DiagnosticQuestion(
        id="duel-expansion",
        prompt="When expanding (x + 2)(x + 3), which terms appear before combining?",
        options=(
            {"id": "four_terms", "label": "x² + 3x + 2x + 6"},
            {"id": "two_terms", "label": "x² + 6 only"},
            {"id": "reverse", "label": "x² + 2x + 3x − 6"},
        ),
        likelihoods={
            "SUM_PRODUCT_CONFUSION": {"four_terms": 0.55, "two_terms": 0.25, "reverse": 0.20},
            "SIGN_CONFUSION": {"four_terms": 0.52, "two_terms": 0.24, "reverse": 0.24},
            "ROOT_FACTOR_CONFUSION": {"four_terms": 0.56, "two_terms": 0.25, "reverse": 0.19},
            "EXPANSION_DIRECTION_CONFUSION": {"four_terms": 0.12, "two_terms": 0.28, "reverse": 0.60},
        },
    ),
)


def initial_beliefs() -> dict[str, float]:
    value = round(1 / len(HYPOTHESES), 6)
    beliefs = {hypothesis: value for hypothesis in HYPOTHESES}
    beliefs[HYPOTHESES[-1]] += round(1 - sum(beliefs.values()), 6)
    return beliefs


def normalize(values: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, value) for value in values.values())
    if total <= 0:
        return initial_beliefs()
    return {key: round(max(0.0, value) / total, 6) for key, value in values.items()}


def posterior_update(beliefs: dict[str, float], question: DiagnosticQuestion, answer_id: str) -> dict[str, float]:
    updated = {
        hypothesis: beliefs.get(hypothesis, 0.0) * question.likelihoods[hypothesis].get(answer_id, 0.01)
        for hypothesis in HYPOTHESES
    }
    return normalize(updated)


def entropy(beliefs: dict[str, float]) -> float:
    return -sum(probability * log2(probability) for probability in beliefs.values() if probability > 0)


def expected_information_gain(beliefs: dict[str, float], question: DiagnosticQuestion) -> float:
    prior_entropy = entropy(beliefs)
    answer_probabilities = {
        option["id"]: sum(beliefs[hypothesis] * question.likelihoods[hypothesis].get(option["id"], 0.01) for hypothesis in HYPOTHESES)
        for option in question.options
    }
    expected_posterior_entropy = 0.0
    for answer_id, probability in answer_probabilities.items():
        if probability <= 0:
            continue
        posterior = posterior_update(beliefs, question, answer_id)
        expected_posterior_entropy += probability * entropy(posterior)
    return round(prior_entropy - expected_posterior_entropy, 6)


def select_question(beliefs: dict[str, float], asked_ids: list[str]) -> tuple[DiagnosticQuestion | None, float]:
    candidates = [question for question in QUESTIONS if question.id not in asked_ids]
    if not candidates:
        return None, 0.0
    scored = [(expected_information_gain(beliefs, question), question) for question in candidates]
    score, question = max(scored, key=lambda item: (item[0], item[1].id))
    return question, score


def diagnostic_status(beliefs: dict[str, float], asked_count: int, max_questions: int = 4) -> str:
    top = max(beliefs.values())
    if top >= 0.72:
        return "SUFFICIENT"
    if asked_count >= max_questions:
        return "INCONCLUSIVE"
    return "INVESTIGATING"


def question_payload(question: DiagnosticQuestion | None, beliefs: dict[str, float], asked_count: int) -> dict:
    if question is None:
        return {"id": None, "prompt": None, "options": [], "information_gain": 0.0, "status": diagnostic_status(beliefs, asked_count)}
    return {
        "id": question.id,
        "prompt": question.prompt,
        "options": list(question.options),
        "information_gain": expected_information_gain(beliefs, question),
        "status": diagnostic_status(beliefs, asked_count),
    }


def factorisation_experiment(factor_a: int, factor_b: int, target_sum: int = 5, target_product: int = 6) -> dict:
    """Evaluate a bounded monic quadratic experiment with symbolic algebra."""
    if not all(isinstance(value, int) and -20 <= value <= 20 for value in (factor_a, factor_b)):
        raise ValueError("Factors must be integers between -20 and 20.")
    x = symbols("x")
    expression = expand((x + factor_a) * (x + factor_b))
    polynomial_roots = roots(expression, x)
    return {
        "factors": [factor_a, factor_b],
        "expression": str(expression),
        "latex": str(expression),
        "expanded": str(expression),
        "sum": factor_a + factor_b,
        "product": factor_a * factor_b,
        "target_sum": target_sum,
        "target_product": target_product,
        "matches_target": factor_a + factor_b == target_sum and factor_a * factor_b == target_product,
        "roots": [str(root) for root in sorted(polynomial_roots, key=lambda value: float(value))],
        "explanation": (
            f"The constants add to {factor_a + factor_b} and multiply to {factor_a * factor_b}. "
            f"The target requires a sum of {target_sum} and a product of {target_product}."
        ),
    }
