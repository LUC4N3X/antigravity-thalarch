# Changelog

## 2.2.0 — 2026-08-18

Thalarch 2.2 adds project-aware polyglot engineering. The orchestrator now detects the real
language/toolchain and can delegate substantial implementation work to isolated language
specialists instead of applying one generic coding prompt to every stack.

### Added

- `thalarch-code-craft` universal coding guard against API hallucination, speculative
  abstraction, dependency bloat, error swallowing, fake-success paths, scope creep, and
  repository-style drift;
- dedicated project-aware skills for Java, Kotlin, Python, TypeScript/JavaScript, Go, and Rust;
- dedicated implementation agents for those six language families;
- `thalarch-refactor` for behavior-preserving refactors with baseline/characterization proof;
- `thalarch-performance` for measurement/profile-first optimization;
- `thalarch-api` for compatibility, errors, idempotency, retries, pagination, and distributed
  boundary semantics;
- `thalarch-data-sql` for ORM/query correctness, transactions, migrations, query plans, and
  data-safe rollout;
- `thalarch-dependency` for dependency/framework/toolchain changes with version/API verification;
- project-probe language detection across common source extensions while skipping generated,
  dependency, cache, and build directories;
- structural validator checks for all six language specialists.

### Changed

- router now selects process + language + domain overlays from repository evidence;
- orchestrator routes Java/Kotlin/Python/TypeScript/Go/Rust changes to dedicated clean-context
  specialists and uses an explicit integration stage for mixed-language contracts;
- `thalarch-test` now includes boundary matrices, property/metamorphic testing, fuzz-style
  regression discovery, concurrency test discipline, and mock-vs-integration proof boundaries;
- core coding protocol now requires version-sensitive external APIs to be confirmed rather than
  generated from memory;
- code-quality guidance is adaptive to repository conventions rather than imposing universal
  numeric function-size/argument-count rules;
- README documents the full polyglot, API/data, performance, and refactoring model.

### Design heritage

The polyglot update synthesizes public agentic-development patterns found in the
`agentic-awesome-skills` collection — including `super-code`, Java/Python specialist guidance,
Kotlin coroutine guidance, clean-code agent guardrails, and structured code review — into an
original project-aware Antigravity workflow.

## 2.1.0 — 2026-08-18

Thalarch 2.1 adds a full creative-engineering path for production websites,
visual design, and image generation/editing while keeping the core protocol
project-agnostic.

### Added

- `thalarch-web-design` for distinctive production websites and frontend work;
- `thalarch-design-system` for semantic visual-system extraction/creation;
- `thalarch-image` for routing visual tasks to generation, edit, vector, capture,
  compare, annotate, or optimization paths;
- `thalarch-imagegen` for disciplined use of Antigravity's native image generator;
- `thalarch-visual-qa` for independent pixel/metadata/reference verification;
- `thalarch-web-designer` agent for production frontend design + implementation;
- `thalarch-visual-director` agent with `generate_image` access;
- `thalarch-design-reviewer` for independent website/UI design review;
- `thalarch-vision-reviewer` for cold image/visual review;
- standard-library image metadata probe and optional Pillow-based decoded pixel diff;
- image and full-website cases in the evaluation corpus.

### Changed

- the router now recognizes image/visual work as a first-class mode;
- the orchestrator can coordinate web design, image creation, and independent
  visual review without gaining direct mutation/image-generation tools itself;
- UI work can delegate generated imagery while keeping implemented runtime UI
  separate from generated mockups;
- browser QA now explicitly uses real page screenshots/recordings and checks
  generated-image integration at responsive sizes;
- final verification distinguishes prompts, standalone assets, implemented UI,
  and real runtime visual evidence.

### Design principles

The new design path synthesizes proven public patterns around strong aesthetic
direction, semantic design systems, responsive composition, accessibility,
review discipline, and anti-template quality while remaining an original
Antigravity-native implementation.

## 2.0.0 — 2026-08-18

Thalarch 2.0 changes the project from a single broad high-rigor mode into a
progressively disclosed, task-routed engineering harness.

### Added

- task/risk router for surgical, bug, feature, architecture, UI, Android,
  security, CI, and Git workflows;
- executable acceptance/specification gate;
- bounded codebase-intelligence workflow;
- causal root-cause debugging protocol;
- falsifiable test/regression design;
- risk-sized review council with independent spec, security, and performance
  lenses;
- isolated researcher agent for current documentation and external contracts;
- UI/browser, Android, security, CI, Git, compounding, and self-evaluation skills;
- optional consequential-command hook, disabled by default;
- Linux/macOS installer;
- package validator and GitHub Actions validation workflow;
- MIT license.

### Changed

- the orchestrator remains structurally unable to edit project files or run shell
  commands and now routes tasks to the smallest relevant specialist stack;
- completion requires cold evidence-backed verification;
- reviewer findings must be confirmed before a fix is dispatched;
- long-session recovery uses an evidence ledger instead of conversational memory;
- core behavior is project-, language-, and framework-agnostic. Domain skills
  are optional overlays rather than assumptions.

### Removed

- redundant V1 protocol references that duplicated the new focused skills;
- generated Python cache artifacts from the distribution.
