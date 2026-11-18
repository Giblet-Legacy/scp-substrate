"""
agent_scp_substrate.py — scp-substrate's agent: it knows, checks and reports on itself

Function:
    scp-substrate's agent (agent-layer SPEC.md 0.1.0). It reads this
    repository's card from its own headers; checks its git state, its
    tests, VERSION against the CHANGELOG, dev markers, its sealed
    capsules, its archive and its file names; checks the siblings it
    depends on; and reports what needs James. It never edits, commits,
    pushes, signs or seals anything. The runtime is ../agent-layer/agent.py.

    python agent_scp_substrate.py [--no-tests] [--json]

Public API:
    1. DECLARATION — what this agent is and watches

Tier:     the Agent runtime (agent-layer), for Tier 1 — Consumer (The Memory)
Depends:  ../agent-layer/agent.py
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_RUNTIME = os.path.join(os.path.dirname(_HERE), "agent-layer")
if _RUNTIME not in sys.path:
    sys.path.insert(0, _RUNTIME)

# 1. DECLARATION
DECLARATION = {
    "repo": "scp-substrate",
    "role": "Tier 1 — Consumer (The Memory)",
    "main": ["serve_v8.py"],
    "tests": True,
    "watches": ["serve_v8.py"],
    "may_propose": True,
}

if __name__ == "__main__":
    import agent
    sys.exit(agent.main(_HERE, DECLARATION, sys.argv[1:]))
