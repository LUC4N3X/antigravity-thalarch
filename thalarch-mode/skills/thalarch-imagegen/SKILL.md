---
name: thalarch-imagegen
description: >
  Creates and edits project images through the strongest image-generation/editing capability
  actually available on the current host. Uses disciplined visual briefs, explicit art direction,
  anti-AI-slop quality gates, reference-role labeling, invariants, deliberate iteration,
  exact-text handling, brand consistency, and post-generation review. Use for raster artwork,
  photography, mockups, marketing assets, textures, concept visuals, compositing, and semantic
  image edits.
---

# Thalarch Imagegen

Use a real host-provided image-generation/editing tool when raster generation or semantic image
editing is the correct medium. Antigravity may expose `generate_image`; other hosts may expose a
different image tool or none at all.

**Never invent a tool call because another host supports it.** If no compatible image capability is
available, keep generation/editing `UNVERIFIED`/unperformed and use a deterministic alternative only
when it genuinely satisfies the request.

The goal is not to write the longest prompt. The goal is to make visual intent unambiguous, specific,
and art-directed while leaving irrelevant details unconstrained.

## 1. Confirm capability and artifact path

Before generation/editing:

- confirm the current host exposes a compatible image tool;
- confirm whether it accepts text-only generation, image references, editing, masks, aspect ratio,
  transparency, or other requested controls;
- use the tool's **actual current schema**, not remembered parameters from another host;
- preserve source/reference images unless replacement is explicitly requested.

If the host only supports text generation but not precise edits, do not claim edit invariants can be
preserved with the same confidence.

## 2. Establish the visual thesis

Before writing a generation prompt, reduce the request to a compact art-direction decision:

`PURPOSE | AUDIENCE | MEDIUM | FOCAL POINT | COMPOSITION | LIGHT | PALETTE | MATERIAL/TEXTURE | NEGATIVE SPACE | SIGNATURE ELEMENT | ANTI-CLICHES`

The **visual thesis** is the one-sentence reason the image should look the way it does. It must be
specific to the actual product, brand, subject, or destination. `Premium`, `cinematic`, `modern`,
`beautiful`, and `professional` are not sufficient directions by themselves.

For open-ended, high-visibility work such as branding, hero art, store graphics, launch assets, or
campaign imagery, consider a small set of materially different concepts before converging. Vary a
real design axis — composition, medium, point of view, negative space, material language, or visual
metaphor — not merely color. Do not generate extra concepts when the direction is already explicit or
when the additional cost has little value.

## 3. Build the generation brief

Normalize the request into this order:

1. **Use case / destination**
2. **Asset type**
3. **Primary request**
4. **Visual thesis / quality bar**
5. **Canvas / aspect ratio / framing**
6. **Subject and key details**
7. **Composition / focal hierarchy / negative space**
8. **Style / medium / material character**
9. **Lighting / mood**
10. **Palette / brand constraints**
11. **Text (verbatim), if any**
12. **Input image roles**
13. **Invariants**
14. **Forbidden elements / anti-cliches**
15. **Output intent**

Do not add story, objects, colors, or copy the user did not request unless the request is genuinely
open-ended and the addition materially improves the result.

## 4. Professional aesthetic bar

When the user asks for `professional`, `premium`, `beautiful`, `editorial`, `brand-grade`,
`marketing-grade`, or another high-finish result, correctness is necessary but not sufficient.

Require intentional visible choices:

- one clear focal hierarchy rather than equal emphasis everywhere;
- composition that feels chosen for the destination rather than default centered symmetry;
- useful negative space and breathing room where the format benefits from it;
- a controlled palette with purposeful contrast;
- a coherent medium: photography should behave like photography, illustration like one consistent
  illustrative/material system;
- plausible light direction, shadows, perspective, reflections, surfaces, and material response;
- texture and detail appropriate to the medium instead of uniform synthetic smoothness;
- restrained decoration: every glow, particle, line, prop, texture, or effect must earn its place;
- framing and crop that still work at the real destination size;
- at least one task-specific or brand-specific signature decision when distinctiveness matters.

Do not confuse complexity with quality. A sparse image can be more art-directed than a highly
rendered one.

## 5. Anti-AI-slop gate

Avoid these as **generic defaults** unless the user, brand, or reference explicitly calls for them:

- gratuitous blue/purple neon gradients;
- excessive bloom, glow, rim light, lens flare, or floating particles;
- glossy pedestal + floating 3D object compositions used without a product reason;
- meaningless sci-fi HUD lines, grids, waves, circuitry, or holograms;
- glassmorphism, chrome, iridescence, or liquid-metal effects added merely to signal `premium`;
- oversaturated teal/orange grading;
- perfectly bilateral symmetry without a compositional reason;
- generic stock-photo posing and generic smiling-team imagery;
- over-smoothed plastic skin, fabric, metal, stone, or other materials;
- fake shallow depth of field or bokeh applied everywhere;
- impossible light sources, inconsistent shadows, broken perspective, or physically incoherent
  reflections;
- decorative clutter that could be removed without weakening the concept.

These are not banned styles. They fail only when they appear as unmotivated model defaults rather
than deliberate art direction.

Use the **generic-AI test** for high-quality work: if the image could be dropped into dozens of
unrelated AI/startup/crypto/product prompts without changing its visual logic, it is not specific
enough yet.

## 6. Prompt discipline

Prefer positive, concrete art direction over adjective soup or enormous negative prompts.

- describe the focal relationship and composition before secondary detail;
- specify lighting as geometry and behavior when it matters, not as random `cinematic` vocabulary;
- name materials/textures only when they help the visual thesis;
- do not combine incompatible media or art directions unless the contrast is intentional;
- use camera/lens language only when it controls a meaningful photographic choice;
- use references for actual visual evidence rather than trying to reconstruct every property in
  prose;
- keep negative constraints focused on likely failure modes and user-prohibited elements.

A longer prompt is not automatically a better prompt.

## 7. Generation vs editing

### New generation

Use the current host's actual image-generation capability with the visual thesis and a concise
structured brief. Use a semantic asset name when naming is supported.

### Edit

Pass the real source image through the host's supported reference/edit mechanism.

State the mutation first:

`Change only <X>.`

Then restate invariants:

`Keep <Y, Z, composition, subject identity, lighting...> unchanged.`

Repeat critical invariants on every edit iteration. Do not rely on conversational memory to preserve
them.

## 8. Multi-reference control

When multiple inputs are supported, label them explicitly:

- `Image 1 — edit target`
- `Image 2 — style/medium reference`
- `Image 3 — composition reference`
- `Image 4 — brand/palette reference`

Describe exactly how they interact. References may control composition, material treatment, color,
photography, typography character, or mood independently. For compositing specify scale, placement,
perspective, lighting, and which image owns the base framing.

If the host cannot distinguish reference roles reliably, reduce the number of references or use a
more deterministic production path.

## 9. Preserve identity and structure

For identity-sensitive edits, explicitly lock attributes that must survive:

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

## 10. Text inside images

When text must be generated inside a raster image:

- author final copy first;
- place literal text in quotes;
- require verbatim rendering;
- specify location, hierarchy, alignment, and typographic character;
- prohibit extra text;
- inspect final image and read every visible word back.

If exact typography, legal copy, dense tables, or perfect spelling is mission-critical, prefer
deterministic text/vector composition over generative raster text.

## 11. Brand consistency

For brand work derive a compact brand lock:

- approved mark/logo;
- palette;
- shape language;
- typography character;
- spacing/density;
- photography/illustration treatment;
- signature visual behaviors;
- elements that must never change.

Use real reference assets when available. Do not invent a new brand system when the project already
has one. Distinctiveness must come from the actual brand/product, not from generic generative effects.

## 12. Exploration and convergence

### Exploration

When direction is genuinely undecided, create a small number of materially different concepts. Each
concept explores a real design axis, not trivial color swaps.

### Convergence

Once a direction is chosen:

- keep the strongest accepted output as anchor;
- change one meaningful axis per iteration;
- restate invariants;
- compare against the previous accepted anchor;
- preserve what already works;
- stop when both the contract and the applicable aesthetic quality bar are met.

Avoid endless generation loops. Do not hand off an obviously generic or visibly weak candidate just
because the requested objects are present.

## 13. Transparency and cutouts

If transparency is required, request it only when the current image tool supports that property and
verify the actual alpha channel afterward.

If output is opaque, do not call it transparent because the prompt asked for transparency.

For exact cutouts, use deterministic post-processing when available and inspect edge halos,
semi-transparent regions, shadows, glass, hair/fur, and despill artifacts.

## 14. Logos, icons, diagrams, and UI

Do not use raster generation by default for:

- exact SVG logos;
- simple icons;
- architecture diagrams with exact labels;
- charts driven by real data;
- production UI layout.

Use vector/code-native construction when determinism, editability, or exact text matters more than
organic imagery.

Generated mockups are appropriate for visual exploration, not proof that implemented UI matches.

## 15. Immediate post-generation check

Every generated or edited image must be viewed before acceptance when the host can expose the final
artifact. If the final pixels cannot be inspected, visual acceptance remains `UNVERIFIED`.

Check contract correctness **and** visible quality:

- composition and focal hierarchy;
- subject correctness;
- unwanted additions;
- anatomy/geometry where relevant;
- text accuracy;
- reference fidelity;
- crop/safe zones;
- transparency;
- edge artifacts;
- logos/watermarks;
- requested dimensions/export requirements;
- whether the hierarchy survives a thumbnail/squint check;
- whether light, material, perspective, and texture agree;
- whether decoration is purposeful or generic filler;
- whether the result feels specific to this product/brand/task;
- whether a strong human art director could plausibly ship it for the requested quality level;
- whether it still reads as generic AI output.

If a critical property or the applicable aesthetic bar fails, make a targeted edit/regeneration rather
than accepting a technically correct but weak image. The creator still does not self-certify final
quality; independent visual review remains required when available.
