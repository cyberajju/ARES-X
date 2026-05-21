"""Monte Carlo simulation for attack path probability estimation."""

import math
import random

from app.models.attack_path import AttackPath, SimulationResult


class MonteCarloSimulator:
    """Runs Monte Carlo simulations to estimate attack path success probability."""

    def __init__(self, default_iterations: int = 10000):
        """Initialize the simulator with a default iteration count."""
        self.default_iterations = default_iterations

    def simulate(
        self,
        path: AttackPath,
        iterations: int = 0,
        confidence_level: float = 0.95,
    ) -> SimulationResult:
        """Run Monte Carlo simulation on an attack path.

        Each iteration traverses the path. For each step, success/failure is
        determined randomly based on the step probability (with +/- 10% variation).
        Tracks full-path traversals as successes.
        Uses convergence detection to stop early if results stabilize.
        """
        if iterations <= 0:
            iterations = self.default_iterations

        successes: list[float] = []
        full_success_count = 0
        recent_results: list[float] = []
        converged = False

        for i in range(iterations):
            path_succeeded = True
            cumulative_prob = 1.0

            for step in path.steps:
                # Add random variation (+/- 10%)
                variation = random.uniform(-0.1, 0.1)
                adjusted_prob = max(0.0, min(1.0, step.probability + variation))

                # Random success/fail for this step
                if random.random() > adjusted_prob:
                    path_succeeded = False
                    break
                cumulative_prob *= adjusted_prob

            result_value = cumulative_prob if path_succeeded else 0.0
            successes.append(result_value)

            if path_succeeded:
                full_success_count += 1

            # Convergence check after at least 1000 iterations
            recent_results.append(result_value)
            if len(recent_results) > 1000:
                recent_results.pop(0)

            if i >= 1000 and i % 100 == 0:
                recent_std = self._std_dev(recent_results)
                if recent_std < 0.001:
                    converged = True
                    break

        actual_iterations = len(successes)
        mean_prob = sum(successes) / actual_iterations if actual_iterations > 0 else 0.0
        std_dev = self._std_dev(successes)

        # Confidence interval
        z_score = self._z_score(confidence_level)
        margin = z_score * (std_dev / math.sqrt(actual_iterations)) if actual_iterations > 0 else 0.0
        ci_lower = max(0.0, mean_prob - margin)
        ci_upper = min(1.0, mean_prob + margin)

        # Percentiles
        sorted_results = sorted(successes)
        percentiles = {
            "p5": self._percentile(sorted_results, 5),
            "p25": self._percentile(sorted_results, 25),
            "p50": self._percentile(sorted_results, 50),
            "p75": self._percentile(sorted_results, 75),
            "p95": self._percentile(sorted_results, 95),
        }

        return SimulationResult(
            path_id=path.id,
            mean_probability=mean_prob,
            std_deviation=std_dev,
            confidence_interval=(ci_lower, ci_upper),
            percentiles=percentiles,
            iterations_run=actual_iterations,
            converged=converged,
        )

    def _std_dev(self, values: list[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    def _percentile(self, sorted_values: list[float], p: int) -> float:
        """Calculate the p-th percentile from sorted values."""
        if not sorted_values:
            return 0.0
        idx = (p / 100.0) * (len(sorted_values) - 1)
        lower = int(math.floor(idx))
        upper = int(math.ceil(idx))
        if lower == upper:
            return sorted_values[lower]
        fraction = idx - lower
        return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction

    def _z_score(self, confidence_level: float) -> float:
        """Return approximate z-score for common confidence levels."""
        z_scores = {
            0.90: 1.645,
            0.95: 1.960,
            0.99: 2.576,
        }
        # Find closest match
        closest = min(z_scores.keys(), key=lambda k: abs(k - confidence_level))
        return z_scores[closest]
