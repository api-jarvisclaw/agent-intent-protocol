"""
Agent Intent Protocol (AIP)
============================
A protocol for AI agents to declare intents and automatically discover
the best-matching service providers.

Default platform: https://api.jarvisclaw.ai
"""

__version__ = "0.1.0"
__author__ = "JarvisClaw"
__default_endpoint__ = "https://api.jarvisclaw.ai"

from .client import AIPClient
from .resolver import IntentResolver
from .models import Intent, Constraint, Preference, MatchResult

__all__ = [
    "AIPClient",
    "IntentResolver",
    "Intent",
    "Constraint",
    "Preference",
    "MatchResult",
]
