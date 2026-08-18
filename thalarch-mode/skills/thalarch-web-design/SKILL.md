---
name: thalarch-web-design
description: >
  Designs and implements distinctive, production-grade websites, landing pages,
  dashboards, web apps, and frontend components. Use when the user asks to build,
  redesign, beautify, or substantially restyle a web interface. Establishes a
  product-specific aesthetic direction, design system, responsive composition,
  imagery strategy, accessibility, performance, motion, and real browser proof
  while avoiding generic template-like AI aesthetics.
---

# Thalarch Web Design

Build websites like a small design studio that also owns the production code.
The result must have a point of view **and** work.

## 1. Ground the site

Before coding, establish:

- what the product/subject actually is;
- who the page is for;
- the page's single most important job;
- primary and secondary actions;
- content hierarchy;
- technical constraints;
- accessibility/performance constraints;
- existing brand/design system, if any.

If the brief is open-ended, make one concrete, reversible design ruling instead
of producing a generic "modern SaaS" page.

## 2. Commit to an aesthetic direction

Choose a deliberate direction that fits the subject. Examples are only prompts
for thought: editorial, restrained luxury, expressive typography, industrial,
playful, archival, technical, organic, neo-brutalist, cinematic, utilitarian.

The direction must answer:

- What should this feel like?
- What makes it recognizably *this* product?
- What is the one visual decision a visitor may remember?
- What common design cliché are we intentionally not using?

Minimal design still requires character. Maximal design still requires hierarchy.

## 3. Design system before sprawl

For multi-section or multi-page work, load `thalarch-design-system`.

Use shared tokens and reusable primitives for:
- color;
- typography;
- spacing;
- radius/borders/shadows;
- layout widths/grid;
- motion;
- component states.

Do not hardcode a different visual language into every section.

## 4. Typography

Typography is structure, not decoration.

- Choose typefaces that fit the subject and are legally/technically available.
- Use a deliberate display/body relationship when useful.
- Control line length, line height, weight, and tracking.
- Give headings real hierarchy instead of scaling the same font mechanically.
- Avoid defaulting to the same ubiquitous tech fonts on every project.
- Use fallback stacks and loading behavior that do not destroy layout.

## 5. Color and material

- Build a palette with clear functional roles.
- Strong hierarchy beats distributing five accent colors evenly.
- Use gradients, blur, glass, texture, glow, noise, or shadows only when they
  support the chosen material language.
- Maintain readable contrast and visible focus states.
- Treat dark mode as a designed mode, not simple color inversion.

## 6. Spatial composition

Avoid the default stack of centered hero → three cards → logo strip → CTA.

Use composition intentionally:
- asymmetry where it helps hierarchy;
- overlap only with readable z-order;
- controlled grid-breaking moments;
- generous whitespace or controlled density depending on the product;
- strong alignment anchors;
- section transitions that feel authored rather than repeated templates.

## 7. Content before decoration

Use realistic content structure.

- Do not hide weak information architecture behind effects.
- Keep one clear primary action per context when possible.
- Expose the next step.
- Do not ship placeholder links, fake disabled controls, or lorem ipsum as final content.
- Error, empty, loading, success, and long-content states are part of the design.

## 8. Imagery strategy

Decide whether the site needs imagery at all.

Possible paths:
- repository/user-provided assets;
- real product screenshots;
- generated raster imagery through `thalarch-imagegen`;
- deterministic SVG illustration/diagram;
- CSS/Canvas/WebGL visual treatment when it belongs to the concept.

Generated assets must inherit the design-system contract and be independently
reviewed with `thalarch-visual-qa` before integration.

Do not use generated imagery as filler just because image generation is available.

## 9. Motion

Use motion to establish hierarchy, feedback, or continuity.

Prefer:
- one composed entry sequence;
- meaningful hover/focus transitions;
- restrained scroll choreography;
- motion tied to user intent.

Avoid:
- every element floating;
- constant ambient motion with no purpose;
- long transitions that block interaction;
- motion that ignores `prefers-reduced-motion`.

Use native CSS where adequate. Follow the repository's existing motion stack
when one exists instead of adding a library casually.

## 10. Responsive behavior

Design at least:
- compact/mobile;
- normal desktop;
- one stress case such as wide desktop, long labels, or dense content.

Check:
- navigation collapse;
- reordering;
- tap targets;
- text wrap;
- overflow;
- image crop;
- sticky/fixed elements;
- viewport units and mobile browser chrome;
- safe areas where relevant.

Mobile is a recomposition, not desktop compressed to 390px.

## 11. Accessibility and trust

Implement real semantics:
- landmarks and headings;
- labels;
- keyboard operation;
- focus visibility;
- contrast;
- reduced motion;
- meaningful alt text;
- no interaction hidden behind hover only.

Error and destructive actions must be understandable before and after activation.

## 12. Performance discipline

Design quality includes delivery quality.

Inspect:
- image dimensions/format/weight;
- font loading;
- layout shift;
- unnecessary JS;
- animation cost;
- giant shadows/filters on hot paths;
- responsive image behavior;
- lazy loading where appropriate.

Do not sacrifice the whole concept for a synthetic benchmark, but do not ship a
hero that downloads megabytes unnecessarily.

## 13. Implementation

Respect the existing stack. Do not rewrite React to Vue, replace a component
library, or introduce a new CSS framework just to express the design.

Prefer:
- existing primitives;
- semantic tokens;
- small reusable components;
- real interactions;
- minimal dependency growth.

## 14. Browser proof

After implementation use `thalarch-browser-qa` and `thalarch-visual-qa`.

A finished website requires, when browser tooling is available:
- real page load;
- screenshot evidence;
- compact + desktop viewport;
- primary interaction path;
- console check;
- relevant network failures absent;
- visual inspection against the design contract.

If browser tooling cannot run, appearance/interaction remain `UNVERIFIED`.

## 15. Design quality gate

Before completion ask:

- Could this page belong to a completely different product with only the logo swapped?
- Is the primary action obvious?
- Is there one coherent visual thesis?
- Are typography and spacing doing real hierarchy work?
- Is every decorative technique justified?
- Does mobile feel designed?
- Are images integrated into the composition rather than pasted on top?
- Does the implemented browser result match the design intent?

If the answer to the first question is yes, the design is not distinctive enough.
