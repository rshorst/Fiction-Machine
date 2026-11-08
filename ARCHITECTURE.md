# Unslop — Architecture

*What the system currently is. Present tense, describing what runs.*

---

## The pipeline

A single seed sentence enters `run_full.py`. A PDF exits.

`run_full.py` derives a slug from the seed via a direct Haiku API call, confirms it interactively, stages the story directory under `vault/stories/[slug]/`, then chains three stage scripts as subprocesses. It runs under `caffeinate` to prevent macOS sleep during long runs. After the stages complete it calls `generate_pdf.py`.

Three stages:

- **`run_to_draft_01.py`** — Miranda deposits theory; Frances builds three characters and a relational web; a checkpoint is saved; Richard generates six plots; the Curator selects one; Richard writes draft_01.
- **`run_to_draft_02.py`** — Five annotators read draft_01 independently; Sean synthesizes their annotations into an editorial letter; Richard writes draft_02.
- **`run_to_draft_03.py`** — Guha reads draft_02 and produces draft_03 by subtraction. Python enforces the word-count quota. A metadata footer is appended.

Each stage script is idempotent: it checks for existing output files and skips stages already completed. A run interrupted mid-stage can be resumed by re-running the script.

---

## Stage 1

### Miranda — theory deposits

Miranda (Opus, max_iter=40, memory=True) runs before any character or draft exists. She searches for theory papers relevant to the project's standing questions and her own interests. The seed is ambient context — not what she searches with. She finds three papers, answers her questions about each, and writes deposits to two locations: the shared `miranda_papers` ChromaDB collection and the story's `theory_deposits/` directory as markdown files. `deposit_tool.py` also updates `vault/theory/bibliography.md`: appending a new entry under `## Papers in miranda_papers` with arXiv ID and year, or adding the current slug to an existing entry's `Engaged in:` line.

*Skip condition:* three or more deposit files already exist in `theory_deposits/`.

### Frances — three character builds

Frances (Opus, max_iter=100, memory=False) runs three separate Crew kickoffs, one character per kickoff. Each starts fresh. Characters are built in isolation from each other — no character knows the others exist during its build. This is load-bearing: the relational web is discovered afterward from the profiles, not embedded during construction.

For each character, Frances: calls `FetchPortraitsTool` to select a face from the local library (deduplicating against `vault/faces/used.json`); calls `ViewImageTool` to look at the photograph; builds name, face observation, history, stated and unstated desires, contradiction, and blind spot from what the face shows; conducts a 20-question interview; and writes the complete profile to `characters/[firstname_lastname].md` via `WriteCharacterFileTool`.

*Skip condition:* the first N kickoffs are skipped if N character files already exist.

### Frances — relational web

A fourth Frances kickoff after all three character files exist. Frances reads the three profiles at task-build time (embedded in the task description) and writes `characters/relations.md`. The web covers: who knows whom and how; what each person knows about the others that the others don't know they know; where desire sits between them (acted on, refused, half-acknowledged, withheld); possible collisions between their desires; and what each is to each across three pairs, from both perspectives.

*Skip condition:* `characters/relations.md` already exists.

### Checkpoint

Immediately after the relational web, before Richard runs: the system saves a checkpoint to `_checkpoint/` within the story directory. Copied: `seed.md`, `theory_deposits/`, `characters/`, `faces/`. Not copied: drafts, annotations, letters, plots.

`restore_checkpoint.py <slug>` reverses a failed downstream run: it deletes `drafts/`, `annotations/`, `letters/`, and `plots/`, then restores from `_checkpoint/`. Use when Richard's plot generation or draft writing fails and you want to retry without rerunning Miranda and Frances.

### Richard — plots and draft_01

Richard (Opus, max_iter=100, memory=False) runs `build_plots_task()`: reads the seed, all character files, and all theory deposits (all embedded at task-build time), then generates six plots in note form — one per emotional arc shape from Reagan et al. 2016. Each plot carries an explicit derivation: arc commitment, papers drawn from, what was picked up, what was left aside, and how these specific characters come into contact with the situation the seed describes.

The Curator (Opus, memory=True) reads the six plots and selects one, applying the project's narrative criteria and writing editorial feedback for Richard.

Richard then runs `build_draft_task()`: reads seed, characters, and the curator selection (all embedded), reaches once into the voices corpus for register calibration, and writes draft_01 to `drafts/draft_01.md`.

*Skip conditions:* plots.md, curator_selection.md, and draft_01.md each skip if their output file already exists.

---

## Stage 2

Five annotators read draft_01 independently. They do not read each other's annotations. Each develops a partial perspective. The non-communication is structural: the friction between what they produce is what Sean synthesizes.

**Sue Pen (Opus, memory=True, two passes)** attends to language. Pass 1 surfaces specific passages and names what they are doing. Pass 2 applies cross-paragraph operations: anaphora mapping, echo tracking, density analysis. Both passes write to `annotations/sue_pen.md` (pass 2 overwrites). She loads `reader.md` and `voice.md`.

**Material (Opus, memory=False, two passes)** attends to the physical world. Pass 1 checks individual claims: substitution (is this specific to this place, or could it be anywhere?), timing, sensory accuracy, behavioral plausibility. Pass 2 checks consistency of named objects across the draft. Both passes write to `annotations/material.md`. She loads `voice.md`.

**Frances (Opus, max_iter=100, memory=False, one pass)** reads draft_01 asking one question: are these the people she built? For each character she identifies the moment that is specific to them, the moment that is generic, where their voice holds or fails, and whether their unstated desire is legible in the prose. Writes to `annotations/frances.md` via `output_file`.

**Miranda (Opus, max_iter=40, memory=True, one pass)** runs a theoretical annotation pass. Writes to `annotations/miranda.md`.

**Sean (Opus, memory=True)** reads draft_01 and all four annotation files, all embedded at task-build time. Writes an editorial letter to `letters/sean_letter.md` covering paragraph-keyed sentence-level verdicts across five channels (character, plot, language, setting, digitality) and an arc-level verdict (arc shape, current position, what arrest requires, one flag).

**Richard (Opus, max_iter=100, memory=False)** reads draft_01, Sean's letter, and Frances's annotation — all embedded. Richard receives Frances's annotation directly, not only through Sean's synthesis, because character fidelity requires specific replacement at the sentence level. Writes draft_02 to `drafts/draft_02.md`.

---

## Stage 3

**Guha (Opus, memory=True)** reads draft_02 cold — no annotations, no letters. Her attention is her own. She subtracts.

If draft_02 exceeds 4,500 words, the task description opens with a hard word-count block computed at task-build time: the exact word count, the exact target (85% of draft_02), and an instruction to do a structural pass first (remove whole paragraphs) before applying horst-prose. After Guha's kickoff, `run_to_draft_03.py` counts the actual words in draft_03. If the quota was not met — Guha estimates her own output length and estimates wrong — a trim pass runs: `build_trim_task()` gives Guha the exact gap and asks her to find that many words to remove from the already-cut draft. One trim pass only.

Guha writes `letters/guha_note.md` recording what snagged, which principle each snag failed, what was cut, and the title decision.

A metadata footer is appended to draft_03:

```
---
System: unslop.
Designed by: Rachel Horst (April 2026)
Generated: [timestamp PDT]
Models: claude-opus-4-7
Narrative Cost: $X.XX (X.XM tokens)
```

`generate_pdf.py` converts draft_03.md to PDF: pandoc produces HTML5 with embedded CSS, then Chrome headless (`--headless=new --print-to-pdf`) renders it. Typography: EB Garamond 13pt, 1.7 line-height, 34em max-width, letter-size page, 3cm/3.5cm margins. The metadata footer renders in Courier New 8.5pt.

---

## Agents

| Agent | Model | memory | max_iter | Tasks |
|---|---|---|---|---|
| Miranda | Opus | True | 40 | `build_task(seed)`, `build_annotation_task()` |
| Frances | Opus | False | 100 | `build_character_task()` ×3, `build_relations_task()`, `build_annotation_task()` |
| Richard | Opus | False | 100 | `build_plots_task(seed)`, `build_draft_task()`, `build_revision_task()` |
| Curator | Opus | True | — | `build_plot_selection_task()` |
| Sue Pen | Opus | True | — | `build_pass1_task()`, `build_pass2_task()` |
| Material | Opus | False | — | `build_pass1_task()`, `build_pass2_task()` |
| Sean | Opus | True | — | `build_task()` |
| Guha | Opus | True | — | `build_task()`, `build_trim_task(path, target)` |

All agents: `verbose=False`, `allow_delegation=False`, `cache=False`, `max_tokens=16000`.

*— max_iter: not explicitly set; uses CrewAI default of 25.*

Richard and Material use `memory=False` by design: Richard's revision benefits from distance from his own prior work; Material's claim-checking must read each draft cold.

---

## Corpus

Three ChromaDB collections embedded with `all-MiniLM-L6-v2` (sentence-transformers):

**`voices`** (1,060 chunks) — Rachel's writing: essays, academic papers, Substack posts. Indexed from `vault/writing/`. Used by Richard (one reach for register calibration at draft writing and revision) and Sue Pen (one reach during annotation). Inflects prose register; does not drive plot.

**`miranda_papers`** (179 documents, growing) — theory deposits from all Miranda runs across all narratives. Accumulates monotonically. Each deposit is tagged with its source slug. Used by Miranda (queries the existing corpus to find what's adjacent or in tension before reaching the web) and Richard (at plot generation via `ReachMirandaTool`).

**`faces`** (67 entries) — portrait photographs indexed from `vault/faces/`. Used by Frances via `FetchPortraitsTool`. `used.json` in the same directory tracks which face IDs have been assigned within a run, preventing the same face from being used for two characters.

---

## Skills

Skill files live in `skills/` and are loaded at module import time, embedded in agent backstories. They describe ways of reading, not instructions.

**`horst-prose.md`** — six principles derived from Rachel Horst's writing: the anchor and the drift; the parenthesis; the sentence that turns on itself; the plain sentence after accumulation; the admission; the ending past the ending. Loaded by: Guha (backstory), Richard (backstory).

**`unslop-creative-brief.md`** — the system's creative commitments across seven sections: what kind of story; the register; on AI (as condition, not subject); on using character background (the weight is below the surface); on false atmosphere; the reader; what arrest is. Loaded by: Richard (backstory), Sean (backstory).

**`voice.md`** — how to read a fragment from the voices corpus and let it calibrate register without copying. Loaded by: Richard (backstory), Sean (backstory), Guha (backstory), Material (backstory).

**`reader.md`** — the reader's experience as the measure of the work. Loaded by: Richard (backstory), Guha (backstory), Sue Pen (backstory).

**`title.md`** — how to decide a working title. Loaded by: Richard (backstory), Guha (backstory).

**`corpus-design.md`** — notes on corpus architecture. Not loaded by any agent.

---

## What gets produced

```
vault/stories/[slug]/
├── seed.md
├── _checkpoint/
│   ├── seed.md
│   ├── theory_deposits/
│   ├── characters/
│   └── faces/
├── theory_deposits/          Miranda's per-run deposits as .md files
├── characters/
│   ├── [firstname_lastname].md  × 3
│   └── relations.md
├── faces/                    Portrait images
├── plots/
│   ├── plots.md
│   └── curator_selection.md
├── annotations/
│   ├── sue_pen.md
│   ├── material.md
│   ├── frances.md
│   └── miranda.md
├── letters/
│   ├── sean_letter.md
│   └── guha_note.md
└── drafts/
    ├── draft_01.md
    ├── draft_02.md
    ├── draft_03.md           (with metadata footer)
    └── draft_03.pdf
```

---

## The collection

Unslop is not a system that produces one story. It produces a continuing body of work — non-fungible by design, accumulating across runs. `compile_book.py` reads all stories under `vault/stories/` that have completed the full pipeline (`draft_03.md` exists), assembles them into a single bound document — *Complete Stories of Unslop* — and renders to PDF.

Each story enters the collection as a chapter when it lands. The book grows with the system. The collection is itself a record of the system's argument: the stories, taken together, demonstrate what the architecture has produced.

Output:
- `complete_stories_of_unslop.pdf` — the bound volume
- `complete_stories_of_unslop.md` — source markdown

Structure of the book:
- Title page
- Table of contents (each story by title, with its first sentence as one-line excerpt)
- Each chapter: title, prose, metadata footer
- Colophon: total stories, total tokens, total cost across the system's history

The book is regenerated whenever new stories complete. It is not part of the runtime pipeline; it is a separate compilation step.

---

## Key architectural decisions

**Architecture is the argument.** The system embodies its thesis structurally. The claim is that specificity and resistance to substitution emerge from process rather than from optimization. The pipeline's complexity — independent agents, non-communicating annotators, structured friction between three substrates — is not overhead. It is the work.

**Non-communication between annotators.** Sue Pen, Material, Frances, and Miranda each read draft_01 without access to each other's work. Each develops a partial perspective along a single channel. The friction between partial perspectives is what Sean synthesizes. If the annotators communicated, they would converge; the synthesis would have nothing to do.

**Frances builds characters in isolation; the relational web is a separate pass.** Three separate Crew kickoffs with `memory=False` prevent context accumulation across character builds. Each character is built from a single face, without knowledge of the others. Relations are discovered afterward from the profiles — not constructed during them.

**Guha's word-count quota is Python-enforced.** Prompt-based word count instructions are unreliable — the model estimates its own output length and estimates wrong. The actual word count is checked after every Guha kickoff; a trim pass runs if the quota wasn't met.

**The compatibility patch.** `compatibility_patches.py` is imported before any CrewAI import in every stage script. It patches `handle_max_iterations_exceeded` in both `crewai.utilities.agent_utils` and `crewai.agents.crew_agent_executor` to emit `role="user"` rather than `role="assistant"` when an agent hits its iteration limit. Claude 4.x rejects assistant-role prefill; without this patch a max-iterations event raises an API error and terminates the run.
