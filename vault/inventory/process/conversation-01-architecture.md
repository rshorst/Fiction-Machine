# Conversation 01 — System Architecture
*Date: April 10, 2026*

## What was decided

### Workspace
- Standalone workspace at ~/unslop — separate from ~/workspace
- Self-contained artifact that can be submitted and demonstrated independently

### Infrastructure carried over from ~/workspace
- ChromaDB + embedding pipeline (Ollama + nomic-embed-text)
- CrewAI platform (infrastructure only, new crew definitions written fresh)
- venv-crewai

### Not carried over
- Zotero integration
- Grant-specific collections
- Sync/index scripts tied to Zotero

### Corpus — four collections
- `corpus/theory` — curated theoretical texts (fictopoiesis, hyperstition, AI imaginaries, Borges on process)
- `corpus/writing` — Rachel's own writing as generative substrate (Substack essays, doctoral work)
- `corpus/process` — these conversations, the thinking that made the system
- `corpus/visual` — images and diagrams, accessed directly by a multimodal vision agent

### Agent architecture
- Non-linear, associative — more mind map than pipeline
- Agents stutter toward output rather than converge on it
- Residue of process visible in final story — not smoothed over
- Stopping condition: arrest, not optimization
- Multimodal vision agent (CrewAI multimodal=True, native as of v1.13.0)
- Token logging wrapper instead of LangFuse — ~30 lines Python, self-contained

### Budget
- $100 token budget
- Every agent call does real work
- Cost logging built into the crew

### Key theoretical commitments
- Fungibility is the core problem with AI fiction
- Friction and constraint are generative, not limiting
- The architecture is the argument
- The protocol is the site of authorship
- Residue of process is visible in output

## Reading list started
