# vault/

The vault is the system's persistent substrate — the corpus it draws on and the work it produces. It holds two things: the raw material agents read from (theory, voices) and the outputs they write (stories, characters, annotations, deposits). The running code lives elsewhere; what's here is everything the code accumulates over time.

---

## Directory map

**stories/**
Produced narratives, one folder per story slug. Each slug directory contains:
- `seed.md` — the input seed text
- `_checkpoint/` — snapshot of seed, theory deposits, characters, and faces taken after Frances completes; used by `restore_checkpoint.py` to retry Richard without rerunning Miranda and Frances
- `drafts/` — draft_01, draft_02, draft_03 (markdown) and `[slug].pdf`
- `characters/` — character profiles (face observation, history, desires, contradictions, interview transcript) and `relations.md` (relational web across the three characters)
- `faces/` — portrait images used for each character in this run
- `theory_deposits/` — story-local copies of Miranda's theory deposits made during that run
- `annotations/` — agent working notes (Sue Pen, Material, Frances, Miranda)
- `letters/` — editorial correspondence: Sean's letter, Guha's editor's note
- `plots/` — Richard's six plot sketches (`plots.md`) and the Curator's selection and feedback (`curator_selection.md`)

**theory/**
The theory corpus. Contains:
- `deposits/` — permanent shared store of Miranda's deposits across all runs. Each deposit is a markdown file with YAML frontmatter (source, provenance, tags, story, doc_id)
- `bibliography.md` — cumulative index of all papers deposited, with story engagement tracking
- `reagan_arcs.md` — six emotional arc shapes from Reagan et al. 2016, with operational interpretations for plot generation. Used by Richard via `agents/_arcs.py`; referenced by Sean.

**voices/**
Index of the voices corpus. Contains:
- `bibliography.md` — list of Rachel Horst's writing indexed into the `voices` ChromaDB collection. Source files are not in the vault (deliberately excluded).

**agents/**
Structured reference documents for each agent: role, model, memory/delegation/cache settings, and notes on how each agent is configured and what it is trying to do. Not the executable code — those are at `~/unslop/agents/`.

**inventory/**
Methodological record of the system's development. Build notes, design decisions, propagation flags, architecture history. Not necessary for reading stories — useful for understanding why the system works the way it does.

---

## How things relate

Agents read from three ChromaDB collections: `miranda_papers` (built from `vault/theory/deposits/`), `voices` (built from Rachel's writing; source files outside the vault), and `faces` (built from the portrait pool at `faces/`). Miranda deposits theory fragments into `miranda_papers` before the first draft is written; those deposits contaminate the draft agent's starting material. The voices collection gives Richard and Sue Pen access to Rachel's writing as an orientation — a way of seeing, not a style to imitate. The faces collection is queried by Frances when building characters; she retrieves portrait candidates and looks at them directly before writing profiles. All story output lands in `vault/stories/[slug]/`. Each story directory is self-contained; the theory corpus and voices corpus accumulate across runs and are shared.

---

## What's not here

**Running code** — agents, tools, skills, and pipeline scripts are at the project root (the repo folder): `agents/`, `tools/`, `skills/`, `run_*.py`, `run_full.py`.

**ChromaDB databases** — the actual vector databases (`miranda_papers`, `voices`, and `faces` collections) are at `chromadb/` (rebuilt by `ingest.py`). What's in this vault is the source material those databases are built from.

**Face pool** — the portrait photograph library Frances draws from is at `faces/`. Per-run copies of the images used are at `vault/stories/[slug]/faces/`.

**Source writing** — the texts indexed into the `voices` collection live outside the vault by design. The bibliography at `vault/voices/bibliography.md` is the record of what's there.

**Logs and outputs** — token logs, per-run cost records, and other operational outputs are at `outputs/`.
