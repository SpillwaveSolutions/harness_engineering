import random
from dataclasses import dataclass


@dataclass
class SampledOutput:
    output_id: str
    calibrated_score: float
    stratum: str
    booking_metadata: dict

def stratified_sample(
    outputs: list[SampledOutput],
    samples_per_stratum: int = 100,
) -> list[SampledOutput]:
    """
    Stratify outputs by calibrated confidence quartile;
    draw independent samples from each stratum.
    """
    strata: dict[str, list[SampledOutput]] = {
        "high_confidence": [],    # calibrated_score >= 0.90      ①
        "medium_confidence": [],  # 0.70 <= calibrated_score < 0.90
        "low_confidence": [],     # calibrated_score < 0.70
    }
    for output in outputs:
        if output.calibrated_score >= 0.90:
            strata["high_confidence"].append(output)
        elif output.calibrated_score >= 0.70:
            strata["medium_confidence"].append(output)
        else:
            strata["low_confidence"].append(output)

    sampled = []
    for stratum_outputs in strata.values():
        n = min(samples_per_stratum, len(stratum_outputs))
        sampled.extend(random.sample(stratum_outputs, n))          # ②
    return sampled
