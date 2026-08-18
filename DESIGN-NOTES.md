# Design Notes

Thalarch Mode combines several ideas into an Antigravity-native structure.

## Structural delegation

The most important enforcement mechanism is tool separation:

- orchestrator: read/search/delegate only;
- debugger: read/search/diagnose only;
- implementer: mutation allowed;
- reviewer: read/execute checks only;
- verifier: read/execute checks only, cold context.

This prevents the coordinator from casually doing the implementation itself.

## Separate truth channels

The implementer's reasoning is not treated as proof.

Thalarch uses:
1. implementation evidence;
2. independent engineering review;
3. cold requirement verification.

These channels may disagree; the orchestrator resolves disagreements using code,
tests, logs, and documented contracts.

## Progressive disclosure

The core skill stays general. Detailed protocols are loaded only for the relevant
domain (debugging, review, UI, Android, context efficiency).

## Scope discipline

Thalarch explicitly treats unrequested cleanup as a risk, not as a bonus.

## Evidence language

PASS, FAIL, and UNVERIFIED are intentionally distinct. This prevents "could not
prove" from becoming "probably okay", and prevents speculative reviewer concerns
from becoming fake defects.
