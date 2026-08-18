---
name: thalarch-browser-qa
description: >
  Verifies web UI behavior in a real browser using available browser/Chrome DevTools/Playwright
  capabilities. Use after frontend changes or for browser-only bugs. Checks interaction, console,
  network, responsive behavior, accessibility signals, screenshots, and performance evidence
  rather than treating a successful build as proof.
---

# Thalarch Browser QA

Prefer native browser/Chrome DevTools tooling already installed in Antigravity.

## QA path

1. Start or locate the application using repository instructions.
2. Navigate the real user flow.
3. Verify visible acceptance criteria.
4. Inspect console errors.
5. Inspect relevant network requests.
6. Resize to at least one compact viewport when responsive.
7. Capture screenshots for visual claims.
8. For performance work, record concrete metrics/traces instead of subjective speed.

Do not install browser dependencies automatically if an existing official browser
integration can perform the task.

A browser build passing is not equivalent to the user flow passing.
