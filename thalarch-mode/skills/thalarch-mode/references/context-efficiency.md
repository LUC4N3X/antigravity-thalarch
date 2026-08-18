# Context and Token Efficiency

Thalarch Mode should be rigorous without flooding the context.

## Retrieval

1. Search symbols/strings first.
2. Open the narrowest relevant region.
3. Expand to full files only when architecture or control flow requires it.
4. Prefer project docs and current source over memory.

## Subagent handoff

Give each subagent:

- one clear role;
- one bounded task;
- exact file paths;
- exact acceptance criteria;
- relevant prior decisions;
- a requested compact result format.

Do not paste the whole conversation or giant logs.

## Persistent evidence

Store long plans, command output, screenshots, and review packages in artifacts
or files when available. Refer to them by path.

## Parallelism

Parallel agents are useful when work is independent. Do not parallelize two
agents that will edit the same stateful surface unless they use isolated
worktrees and a deliberate integration step.

## Model economy

For Thalarch quality, planning/debugging/review should favor the strongest available
reasoning tier. Mechanical repetitive work may use a faster tier only when the
task is completely specified and easily verified.

The cheapest model is not cheaper if it takes three times as many turns.
