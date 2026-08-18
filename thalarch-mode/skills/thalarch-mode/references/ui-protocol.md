# UI / UX Protocol

Use this for visual redesigns, layout changes, interaction changes, responsive
behavior, animations, accessibility, or user-facing polish.

## Preserve product intent

Before editing, identify:

- primary user task;
- existing visual language;
- components that must remain recognizable;
- functional controls that cannot be removed;
- target platforms/screen sizes.

Do not turn "make it nicer" into a generic template redesign.

## Visual quality checks

Evaluate:

- hierarchy;
- spacing rhythm;
- typography scale/weight;
- alignment;
- contrast;
- touch/click targets;
- content density;
- empty/loading/error states;
- dark/light themes when supported;
- edge-to-edge/insets;
- motion continuity;
- truncation/localization;
- accessibility semantics.

## Evidence

For UI work, code review alone is insufficient when the runtime can render the
result.

Prefer:

- screenshots before/after;
- browser recording for web interactions;
- device/emulator screenshots for mobile;
- at least one compact and one large viewport when responsive;
- interaction check for the changed controls.

If no render path is available, mark visual quality as UNVERIFIED rather than
pretending source inspection proves the appearance.

## Anti-slop rules

Avoid:

- arbitrary gradients/glows everywhere;
- excessive cards inside cards;
- decorative elements that reduce information clarity;
- duplicated controls;
- animation without interaction purpose;
- generic "AI dashboard" visual clichés;
- inconsistent corner radii and spacing tokens.

The best change should feel native to the existing product, not imported from a
different design system.
