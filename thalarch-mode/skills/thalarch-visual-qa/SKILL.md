---
name: thalarch-visual-qa
description: >
  Performs evidence-first visual QA for images, generated assets, screenshots,
  branding, image edits, diagrams, and implemented web/mobile UI. Use after any
  visual deliverable or when comparing a result with a reference/baseline. Verifies
  pixels and metadata rather than trusting prompts, source code, or creator reports,
  and applies an explicit professional aesthetic quality gate when the request calls
  for polished, premium, distinctive, editorial, brand, or marketing-grade output.
---

# Thalarch Visual QA

The final pixels are the source of truth for visual claims.

A technically valid image can still be a bad image. For high-finish work, visual correctness and
**aesthetic quality** are separate gates and both must pass.

## 1. Derive a visual checklist

Convert the user's visual requirements into checks such as:

- required subject/content;
- composition/framing;
- exact text;
- style/brand match;
- palette;
- dimensions/aspect ratio;
- alpha/transparency;
- crop/safe zones;
- elements that must be absent;
- invariants preserved from the baseline;
- responsive/runtime states;
- requested quality bar: exploratory, production, premium/editorial, brand/marketing;
- distinctiveness/specificity when the user wants something original or professional.

Use `PASS`, `FAIL`, `UNVERIFIED`.

## 2. Two-gate review

For meaningful generated or designed visual assets review two independent dimensions:

### A. Contract / correctness gate

Does the output contain the right subject, text, brand constraints, dimensions, crop, invariants,
and requested technical properties?

### B. Aesthetic quality gate

When the request implies a professional/high-finish result, ask whether the visible artifact is
actually art-directed and strong enough to ship for that destination.

Judge from visible evidence:

- **hierarchy / focal point** — the eye knows where to go first;
- **composition** — balance, tension, crop, scale, and negative space feel intentional;
- **specificity / distinctiveness** — the image belongs to this task, product, or brand rather than
  to a generic image-generation prompt;
- **medium coherence** — photographic, illustrative, 3D, collage, or graphic language is internally
  consistent;
- **palette discipline** — color supports hierarchy and mood rather than adding random spectacle;
- **lighting / material plausibility** — light direction, shadow, reflections, perspective, and
  surfaces agree unless deliberate surrealism is part of the brief;
- **texture / detail** — detail feels material and purposeful, not uniformly synthetic;
- **restraint** — decorative effects earn their place;
- **destination fit** — the image still reads at its actual crop, scale, thumbnail, or placement.

Aesthetic judgment is not mathematically objective. Make the judgment explicit and evidence-based
instead of pretending taste is a metadata probe.

For premium/professional/brand/marketing work, an overall PASS requires both applicable gates to
pass. A candidate that satisfies the object list but looks generic or amateur is still a FAIL.

## 3. View the whole artifact first

Before zooming into details, inspect:

- hierarchy;
- balance;
- focal point;
- crop;
- readability;
- contrast;
- overall visual coherence;
- whether it obviously violates the requested direction.

Then inspect details.

### Thumbnail / three-second test

For assets that will be seen quickly or at small size, inspect the whole composition as if it were a
thumbnail or with a squint test:

- what is visible first?
- what is second?
- does everything compete equally?
- does the silhouette/composition still read without relying on tiny detail?

If everything shouts at the same volume, hierarchy is weak even if each element is individually
well-rendered.

## 4. Generic-AI / slop detection

For high-quality generative work, actively inspect whether the image relies on familiar generative
shortcuts rather than task-specific art direction.

Potential signals include, when unrequested or unjustified:

- blue/purple neon gradient as a generic sophistication cue;
- gratuitous bloom, rim lights, lens flare, particles, sparks, fog, or bokeh;
- glossy floating object on a pedestal with no product reason;
- random HUD lines, grids, circuitry, waves, holograms, or abstract tech glyphs;
- chrome, glass, iridescent, or liquid-metal effects added only to look `premium`;
- oversaturated teal/orange grading;
- perfect symmetry that removes useful visual tension;
- generic stock poses or generic AI-startup hero composition;
- over-smoothed plastic skin/materials;
- inconsistent lighting, reflections, scale, perspective, or material response;
- decorative elements that can be removed without weakening meaning or hierarchy.

These are not banned visual languages. They are defects only when they are unmotivated defaults.

Use the **generic-AI test**: could this image be reused for many unrelated AI/startup/crypto/product
prompts with almost no change? If yes, and the brief asks for distinctive professional work,
specificity is insufficient.

## 5. Mechanical image probes

Use the bundled read-only scripts when relevant:

```text
python scripts/image_probe.py <image>
python scripts/image_compare.py <baseline> <candidate> --out <diff.png>
```

They can prove properties such as dimensions, format, alpha, and same-size pixel change statistics.
They cannot decide whether the design is beautiful. A mechanical PASS never substitutes for the
Aesthetic quality gate.

## 6. Exact text

If exact visible copy matters:

- read the rendered text from the image itself;
- compare character-for-character with the required copy;
- inspect line breaks when layout matters;
- flag extra or hallucinated text.

Do not infer text accuracy from the generation prompt.

## 7. Image-edit preservation

For "change only X" edits:

1. compare against the original;
2. inspect requested region;
3. inspect several supposedly unchanged regions;
4. use a visual diff when dimensions align;
5. distinguish intended global effects from collateral drift.

Check for unintended changes to:
- identity;
- pose/geometry;
- framing;
- background;
- lighting;
- color grading;
- text/logo;
- texture/sharpness.

## 8. Artifact quality

Inspect for common generative/editing failures when relevant:

- malformed anatomy;
- duplicated objects;
- warped geometry;
- broken perspective;
- fake/garbled typography;
- halos and bad masks;
- inconsistent lighting/shadows;
- seams from compositing;
- unintended watermarks/logos;
- compression/upscale artifacts;
- banding;
- transparent-edge contamination.

Do not mechanically hunt for every category if it does not apply.

## 9. Brand review

For brand assets compare against the actual brand contract:

- mark integrity;
- color roles;
- typography character;
- spacing/safe area;
- shape language;
- imagery treatment;
- recognizable signature visual behavior;
- recognizability at small size.

Novelty is not automatically brand consistency, and consistency is not an excuse for generic AI
styling.

## 10. Web/UI visual QA

For implemented UI, pair this skill with real browser/device evidence.

Compare screenshots against:
- design-system contract;
- reference/mockup if present;
- compact and desktop layouts;
- hover/focus/open states where visually meaningful;
- long text/empty/error states when relevant.

Check:
- hierarchy;
- rhythm;
- clipping;
- alignment;
- responsive reflow;
- image crops;
- typography;
- contrast;
- obvious accessibility regressions.

A generated mockup is not evidence of the implemented UI.

## 11. Annotated findings

When a visual defect is hard to describe precisely, create an annotated copy of the
screenshot/image with numbered callouts. Keep the original untouched.

Use the annotation only as evidence; fixes must target the actual source asset or implementation.

## 12. Convergence rule

When a candidate fails:

- identify whether the failure is contractual, technical, or aesthetic;
- identify the smallest visual delta required;
- preserve all already-passing constraints;
- request one targeted edit pass when the direction is sound;
- restart the visual direction only when the visual thesis itself is weak/generic;
- re-run only checks invalidated by that change plus a whole-image sanity check and the applicable
  aesthetic quality gate.

Do not restart the creative direction for a local defect, but do not polish a fundamentally generic
concept forever.

## Output

Return:

`Requirement | PASS / FAIL / UNVERIFIED | Evidence`

For high-finish visual work include explicit summary verdicts:

- `CONTRACT: PASS / FAIL / UNVERIFIED`
- `AESTHETIC QUALITY: PASS / FAIL / UNVERIFIED`
- `OVERALL: PASS / FAIL / UNVERIFIED`

Then separate:
- blocking defects;
- optional polish;
- exact next edit or direction change, if another pass is necessary.

A clean pass is valid. Do not manufacture criticism. An aesthetic FAIL must point to visible,
request-relevant reasons rather than vague dislike.
