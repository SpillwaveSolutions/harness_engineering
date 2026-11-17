# Pattern-to-framework coverage table builder
# Run this as a decision tool before picking a framework

from dataclasses import dataclass
from typing import Literal

Coverage = Literal["OTS", "CONF", "BYO"]


@dataclass
class PatternCoverage:
    pattern: str
    category: str
    claude_sdk: Coverage
    deep_agents: Coverage
    google_adk: Coverage


COVERAGE_TABLE = [                                                    # ①
    # --- Five harness patterns ---
    PatternCoverage(
        "Progressive disclosure", "harness", "OTS", "OTS", "CONF"
    ),
    PatternCoverage(
        "Isolation", "harness", "CONF", "OTS", "CONF"
    ),
    PatternCoverage(
        "Spec-first", "harness", "OTS", "OTS", "OTS"
    ),
    PatternCoverage(
        "Mechanical enforcement", "harness", "CONF", "OTS", "CONF"
    ),
    PatternCoverage(
        "Integrated feedback", "harness", "CONF", "OTS", "OTS"
    ),
    # --- Five workflow patterns ---                                   # ②
    PatternCoverage(
        "Prompt chaining", "workflow", "BYO", "CONF", "OTS"
    ),
    PatternCoverage(
        "Routing", "workflow", "BYO", "CONF", "OTS"
    ),
    PatternCoverage(
        "Parallelization", "workflow", "OTS", "CONF", "OTS"
    ),
    PatternCoverage(
        "Orchestrator-workers", "workflow", "OTS", "OTS", "OTS"
    ),
    PatternCoverage(
        "Evaluator-optimizer", "workflow", "BYO", "CONF", "CONF"
    ),
    # --- Three composite patterns ---                                 # ③
    PatternCoverage(
        "Hub-and-spoke", "composite", "CONF", "CONF", "OTS"
    ),
    PatternCoverage(
        "Dual-agent handoff", "composite", "OTS", "CONF", "CONF"
    ),
    PatternCoverage(
        "Generator-critic-arbiter", "composite", "BYO", "BYO", "BYO"
    ),
]
