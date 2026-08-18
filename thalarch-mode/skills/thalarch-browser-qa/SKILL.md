---
name: thalarch-browser-qa
description: >
  Verifies web UI behavior in a real browser using Antigravity's built-in Browser
  Subagent and available Chrome DevTools/Playwright capabilities. Use after frontend
  changes or for browser-only bugs. Checks interaction, console, network, responsive
  behavior, screenshots, recordings, accessibility signals, and performance evidence
  rather than treating a successful build as proof.
---

# Thalarch Browser QA

Prefer Antigravity's native Browser Subagent and Chrome DevTools integration when
browser tools are enabled. It can operate an isolated Chrome profile and produce
screenshot/recording artifacts that are useful as review evidence.

Do not install a competing browser automation stack merely for QA if the native
browser path can prove the requirement.

## QA path

1. Start or locate the application using repository instructions.
2. Use the browser on the real running page, not a generated mockup.
3. Navigate the primary user flow.
4. Verify visible acceptance criteria.
5. Inspect console errors/warnings relevant to the change.
6. Inspect relevant network requests and failures.
7. Capture at least:
   - a compact/mobile viewport;
   - a normal desktop viewport;
   - any specific breakpoint named by the requirement.
8. Capture screenshots for every load-bearing visual claim.
9. Exercise changed interactions, not only the initial screen.
10. When useful, preserve a browser recording artifact showing the flow.
11. For performance work, collect concrete metrics/traces rather than subjective speed.

## Visual stress cases

Select only relevant stress cases:
- long text;
- narrow viewport;
- wide viewport;
- empty/loading/error state;
- open menu/dialog/sheet;
- keyboard focus;
- reduced motion;
- slow image/network load;
- zoom/high text scale where practical.

## Image integration checks

For generated or edited imagery used by a site, inspect the real integration:
- crop and focal point at responsive widths;
- loading behavior;
- contrast behind text;
- resolution/sharpness;
- aspect-ratio stability;
- layout shift;
- fallback/alt behavior;
- asset weight where relevant.

The image can pass standalone QA and still fail inside the page.

## Evidence handoff

Send screenshots and relevant runtime evidence to `thalarch-visual-qa` or the
independent design reviewer for final visual judgment.

A successful frontend build is not equivalent to the user flow passing.
A generated mockup is not equivalent to the implemented page passing.
