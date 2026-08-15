"""Belief update engine — deterministic confidence scoring.

No LLM produces arbitrary confidence numbers. Scoring is transparent,
auditable, and normalized across competing hypotheses.
"""

from __future__ import annotations

from packages.contracts.domain import (
    Evidence,
    Experiment,
    Hypothesis,
    HypothesisStatus,
    VerificationOutcome,
    VerificationResult,
)


class BeliefUpdateEngine:
    """Deterministic scoring function for competing hypotheses.

    Inputs:
      - evidence support count and strength
      - experiment verification outcomes
      - contradicting evidence
      - alternative hypothesis strength

    Scores are normalized so they sum to ~1.0 across all hypotheses.
    The calculation breakdown is returned for UI transparency.
    """

    # Weights
    EVIDENCE_WEIGHT = 0.15        # per supporting evidence item (scaled by strength)
    EXPERIMENT_VERIFIED = 0.35    # bonus for verified experiment
    EXPERIMENT_REJECTED = -0.30   # penalty for rejected experiment
    EXPERIMENT_INCONCLUSIVE = 0.0
    CONTRADICTION_PENALTY = -0.10 # per contradicting evidence item
    HISTORICAL_BONUS = 0.05       # if similar past incident supports this hypothesis

    def update(
        self,
        hypotheses: list[Hypothesis],
        verifications: list[VerificationResult],
        evidence: list[Evidence],
        experiments: list[Experiment],
    ) -> dict[str, float]:
        """Compute updated scores for all hypotheses. Returns {hypothesis_id: score}."""
        raw_scores: dict[str, float] = {}
        evidence_by_id = {e.id: e for e in evidence}

        # Verification results are evidence only for the hypothesis the
        # corresponding experiment actually targeted. Never let a successful
        # experiment inflate competing hypotheses.
        experiment_by_id = {experiment.id: experiment for experiment in experiments}
        verification_by_hyp: dict[str, VerificationResult] = {}
        for verification in verifications:
            experiment = experiment_by_id.get(verification.experiment_id)
            if experiment:
                verification_by_hyp[experiment.target_hypothesis] = verification

        for h in hypotheses:
            score = h.score  # start from prior score

            # Evidence support
            for ev_id in h.supporting_evidence:
                ev = evidence_by_id.get(ev_id)
                strength = ev.strength if ev else 0.5
                score += self.EVIDENCE_WEIGHT * strength

            # Evidence contradictions
            for ev_id in h.contradicting_evidence:
                score += self.CONTRADICTION_PENALTY

            # Experiment results for this hypothesis
            if h.id in verification_by_hyp:
                v = verification_by_hyp[h.id]
                if v.outcome == VerificationOutcome.VERIFIED:
                    score += self.EXPERIMENT_VERIFIED
                elif v.outcome == VerificationOutcome.REJECTED:
                    score += self.EXPERIMENT_REJECTED

            # Clamp to [0.01, 0.99]
            raw_scores[h.id] = max(0.01, min(0.99, score))

        # Normalize so scores sum to 1.0
        total = sum(raw_scores.values())
        if total > 0:
            normalized = {
                hid: round(s / total, 3) for hid, s in raw_scores.items()
            }
        else:
            n = len(raw_scores)
            normalized = {hid: round(1.0 / n, 3) for hid in raw_scores}

        return normalized

    def explain(
        self,
        hypothesis: Hypothesis,
        verification: VerificationResult | None,
        evidence: list[Evidence],
    ) -> dict:
        """Return a breakdown of how the score was calculated for one hypothesis."""
        evidence_by_id = {e.id: e for e in evidence}

        support_score = sum(
            self.EVIDENCE_WEIGHT * (evidence_by_id.get(eid, Evidence(
                incident_id="", type="LOG", source="", observation=""
            )).strength)
            for eid in hypothesis.supporting_evidence
        )
        contradiction_score = len(hypothesis.contradicting_evidence) * self.CONTRADICTION_PENALTY

        experiment_score = 0.0
        if verification:
            if verification.outcome == VerificationOutcome.VERIFIED:
                experiment_score = self.EXPERIMENT_VERIFIED
            elif verification.outcome == VerificationOutcome.REJECTED:
                experiment_score = self.EXPERIMENT_REJECTED

        return {
            "prior_score": hypothesis.score,
            "evidence_support": round(support_score, 3),
            "contradiction_penalty": round(contradiction_score, 3),
            "experiment_effect": round(experiment_score, 3),
            "raw_total": round(
                hypothesis.score + support_score + contradiction_score + experiment_score, 3
            ),
        }
