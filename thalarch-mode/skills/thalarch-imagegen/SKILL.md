---
name: thalarch-imagegen
description: >
  Creates and edits project images with Antigravity's native generate_image tool
  using disciplined visual briefs, reference-role labeling, invariants, deliberate
  iteration, exact-text handling, brand consistency, and post-generation review.
  Use for raster artwork, photography, mockups, marketing assets, textures,
  concept visuals, compositing, and semantic image edits.
---

# Thalarch Imagegen

Use Antigravity's native `generate_image` tool when raster generation or semantic
image editing is the correct medium.

The goal is not to write the longest prompt. The goal is to make the visual
intent unambiguous while leaving irrelevant details unconstrained.

## 1. Build the generation brief

Normalize the request into this order:

1. **Use case / destination**
2. **Asset type**
3. **Primary request**
4. **Canvas / aspect ratio / framing**
5. **Subject and key details**
6. **Style / medium**
7. **Lighting / mood**
8. **Palette / brand constraints**
9. **Text (verbatim), if any**
10. **Input image roles**
11. **Invariants**
12. **Forbidden elements**
13. **Output intent**

Do not add story, objects, colors, or copy the user did not ask for unless the
request is genuinely open-ended and the addition materially improves the result.

## 2. Generation vs editing

### New generation

Use `generate_image` with a concise, structured prompt and a semantic
`ImageName`.

### Edit

Pass the actual source image path(s) via `ImagePaths`.

State the mutation first:

`Change only <X>.`

Then restate the invariants:

`Keep <Y, Z, composition, subject identity, lighting...> unchanged.`

Repeat critical invariants on every edit iteration. Do not rely on the model
remembering them from a prior turn.

## 3. Multi-reference control

When using multiple inputs, label them inside the prompt:

- `Image 1 — edit target`
- `Image 2 — style reference`
- `Image 3 — brand/logo reference`

Describe exactly how they interact.

For compositing, specify scale, placement, perspective, lighting, and which image
owns the base framing.

## 4. Preserve identity and structure

For identity-sensitive edits, explicitly lock the attributes that must survive:

- facial/character identity;
- body proportions;
- pose;
- hairstyle;
- clothing;
- object geometry;
- camera framing;
- perspective;
- brand marks;
- lighting direction.

Do not claim preservation until the rendered output is inspected.

## 5. Text inside images

When text must be generated inside a raster image:

- author the final copy first;
- place literal text in quotes;
- require verbatim rendering;
- specify location, hierarchy, alignment, and typographic character;
- prohibit extra text;
- inspect the final image and read every visible word back.

If exact typography, legal copy, dense tables, or perfect spelling is
mission-critical, prefer deterministic text/vector composition over asking a
generative model to rasterize it.

## 6. Brand consistency

For brand work, derive a compact brand lock:

- approved mark/logo;
- palette;
- shape language;
- typography character;
- spacing/density;
- photography/illustration treatment;
- elements that must never change.

Use reference assets when available. Do not invent a new brand system when the
project already has one.

## 7. Exploration and convergence

### Exploration

When the direction is genuinely undecided, create a small number of materially
different concepts. Each concept should explore a real design axis, not trivial
color swaps.

### Convergence

Once a direction is chosen:
- keep the strongest output as the anchor;
- change one meaningful axis per iteration;
- re-state invariants;
- compare against the previous accepted anchor;
- stop when the acceptance contract is met.

Avoid endless generation loops.

## 8. Transparency and cutouts

If transparency is required, request it explicitly and verify the actual alpha
channel afterward.

If the generated result is opaque, do not call it transparent merely because the
prompt asked for transparency.

For exact cutouts, use a deterministic post-processing path when available and
inspect edge halos, semi-transparent regions, shadows, glass, hair/fur, and
despill artifacts.

## 9. Logos, icons, diagrams, and UI

Do not use raster generation by default for:
- exact SVG logos;
- simple icons;
- architecture diagrams with exact labels;
- charts driven by real data;
- production UI layout.

Use vector/code-native construction when determinism, editability, or exact text
is more important than organic imagery.

Generated mockups are appropriate for visual exploration, not as proof that the
implemented UI matches the mockup.

## 10. Immediate post-generation check

Every generated or edited image must be viewed before acceptance.

Check:
- composition;
- subject correctness;
- unwanted additions;
- anatomy/geometry where relevant;
- text accuracy;
- reference fidelity;
- crop/safe zones;
- transparency;
- edge artifacts;
- logos/watermarks;
- requested dimensions/export requirements.

If a critical property fails, make a targeted edit rather than rewriting the
entire creative brief.
