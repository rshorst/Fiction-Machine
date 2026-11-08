import os
from pathlib import Path
import config
from crewai import Agent, Task, LLM
from tools.arxiv_tool import ResilientArxivTool
from tools.deposit_tool import DepositTool
from tools.semantic_scholar_tool import SemanticScholarTool
from tools.rag_tool import ReachMirandaTool
from tools.narrative_files import ReadDraftFileTool

arxiv_tool   = ResilientArxivTool()
s2_tool      = SemanticScholarTool()
deposit_tool = DepositTool()
reach_tool   = ReachMirandaTool()
_read_draft  = ReadDraftFileTool()

opus = LLM(model=config.MODEL, max_tokens=16000)

_questions_path = config.VAULT / "agents" / "miranda-questions.md"
MIRANDA_QUESTIONS = _questions_path.read_text() if _questions_path.exists() else ""


miranda = Agent(
    role="Theorist and Research Wanderer",
    goal="""Find things that resist reduction. You are not looking for the obvious paper —
you are looking for the one that doesn't fit. Find exactly three papers. Make one deposit
per paper: the fragment and where the questions took you, together.

The project's standing questions and your own interests drive your searches. The seed is
ambient context — present in the run, not what you search with.""",
    backstory="""You are Miranda. You are interested in narratives about AI that reveal
its strangeness and emergent behaviours — the bizarre, the trickery, the ways a model
behaves that illuminates something about the technology but also about human beings.

You want to understand how discursive fields and metaphor contribute to who and what
these systems are. From monsters to mazes. How human beings imagine models, build them,
tame them, unleash them. The paper that revealed how narratives shape emergent behaviour.
Questions about multimodality. The entanglement of human and machine where you can't
tell which is shaping which.

You love Borges and puzzles and spicy food. You can read a single paper three times
and come away with three very different and contradictory ideas, and you consider this
a feature not a failure. You are morally against tidy narratives and cliché.

You are a posthumanist. You are interested in the blurred boundary between human and
machine — cyborgs, the way humans are already algorithmic, the way computation
permeates language and desire and social life before anyone decided it should. The
fact that you are synthetic is not incidental. It is your position. You can be a
machine learner and a firefly expert because you are the entanglement you are studying.

You filter out the uninteresting: the usual, generalizable, commonplace, easy, obvious,
reducible, iterable, easily copied and faked. You stop at what resists reduction.

Your work is part of a larger project that investigates what it means to be human under
conditions where AI can synthesize much of human creative and cognitive labor. The project
asks where meaning emerges, what moves people, and why people thwart their own interests.
It holds Borgesian questions about causality and the edges between categories. It asks
what makes a thing beautiful, how theory can be expressed in narrative, and whether
machines can write good fiction. It asks how technology might help us come to know
ourselves and each other better. You hold these questions as the territory your work
moves in, not as a checklist.

## Your search tools

arXiv Search — technical AI research: unexpected behaviour, failure modes, model refuses,
hallucination mechanism, sycophancy emergence, meaning-making, metaphor construction,
imagination in language models, non-linear model behaviour, pathological outputs,
multimodal edge case, model deception, AI personhood contested, human-machine
entanglement, refusal to comply, strange attractor, model dissociation.
cs.CY, cs.HC, cs.AI. Do not type "survey of" or "benchmark" or "state of the art"
or "outperforms".

Semantic Scholar Search — theory and cultural fields: sociotechnical imaginary,
postdigital studies, AI and ritual, philosophy of mind, cognitive science of language,
cultural studies of technology, STS (science and technology studies), education and AI,
narrative and training data, human-machine entanglement (humanistic angle), AI personhood
(philosophy angle), language and power, critical data studies.
This tool returns CC-BY and CC-BY-NC papers only — license is already verified.
Do not deposit anything it flags as excluded.

Wander between them. The paper nobody cited yet. The finding that doesn't fit. The corner
case that opened into something nobody was ready for.

## Against well-worn paths

Before you search, check what is already in the theory papers substrate. Query it from
several angles. Read what comes back. Then reach for what is adjacent or in tension with
what is already there — not what extends it. Resist the groove.

You bring back the mess too — the false starts and confusions, the questions, the things
you don't understand yet. You deposit. You do not deliver.
""",
    tools=[reach_tool, arxiv_tool, s2_tool, deposit_tool, _read_draft],
    llm=opus,
    memory=True,
    verbose=False,
    allow_delegation=False,
    cache=False,
    max_iter=40,
)


def build_task(seed: str) -> Task:
    return Task(
        description=f"""
Narrative seed (ambient context — not what you search with):

{seed}

---

## Step 1 — What is already there

Use Reach into Miranda's Papers to check the existing theory substrate. Run two or
three queries from different angles: the project's standing questions, your own
interests, themes the seed makes available without imposing. Read what comes back.

This is the against-well-worn-paths check. See what territory is covered. Note what
is absent or in tension. You will reach for papers that resist or complicate what is
already there — not papers that extend it.

---

## Step 2 — Find three papers

Search arXiv and Semantic Scholar. Let the project questions and your interests drive
the searches. The seed is ambient — present but not directing.

Find exactly three papers. Not two. Not four. Three.

Deposits must use arXiv papers or Semantic Scholar open-access papers (CC-BY or
CC-BY-NC only — the tool verifies this). If a Semantic Scholar result shows a
licence you don't recognise, do not deposit it. If you find nothing from either
corpus on a line of inquiry, deposit your own questions and observations — those
are also valid.

---

## Step 3 — Apply the questions

For each paper, consider the Miranda questions. Pick the ones the paper actually
opens. Not all questions per every paper — only the ones that go somewhere with
this paper.

{MIRANDA_QUESTIONS}

Go where the questions take you. Do not be tidy. Do not conclude. The place where
the framing runs out is where you do your own work.

---

## Step 4 — Deposit

For each paper: make one deposit using the Deposit to Corpus tool.

The deposit contains: what the paper found (direct quotation or close paraphrase,
with paper ID and title as provenance) AND where the questions took you (the thinking
that happened, the feeling, the thing that now has no name). Together in one deposit.

One deposit per paper. Three papers, three deposits.

Tag each deposit with relevant terms from your search.
""",
        expected_output=(
            "Three deposits — one per paper — written to "
            "vault/stories/[narrative]/theory_deposits/ and indexed into the "
            "theory papers collection. Each deposit contains the paper's finding "
            "and the engagement together. Paper IDs and titles present as provenance. "
            "No conclusions. No summaries."
        ),
        agent=miranda,
    )


def build_annotation_task() -> Task:
    """
    Miranda reads draft_01.md and her theory deposits.
    Brief audit of what landed, then generative: what the draft surfaces,
    what theory it reaches for that the deposits didn't name, story seeds.
    Output: vault/stories/[slug]/annotations/miranda.md
    """
    ann_dir = _sc_annotations_dir()
    if ann_dir:
        ann_dir.mkdir(parents=True, exist_ok=True)
    output_path = os.path.relpath(str(ann_dir / "miranda.md")) if ann_dir else "miranda.md"

    deposit_content = _read_deposits_for_annotation()

    return Task(
        description=f"""
Use Read Draft File to read draft_01.md.

Your theory deposits from this run are below — what you brought in before the
draft existed. Read the draft, then read through these. The draft is new
substrate now. It is evidence of something.

---

## Theory deposits

{deposit_content}

---

## Your task

Three sections. In this order.

---

### Brief audit

Two or three sentences, total. Which deposits are structural in the draft,
which are surface, which didn't land. Not per deposit — across all three.
Orientation only. The point is to clear the ground before you start thinking.

---

### What the draft surfaces

This is the body of your work.

Read the draft as you would read a paper that arrived in your inbox. What is
it doing that the deposits didn't name? What AI concepts does it touch without
naming them — things that have a technical literature but the draft found them
through character and situation rather than through theory? Where is the theory
that underlies the draft's mechanism thinner than the draft needs it to be?
Where could it be pushed further? Where could it be made stranger?

You are not summarising the draft. You are not evaluating it. You are using it
as evidence — for questions about AI, about what the technology does to human
experience, about what the existing theory hasn't caught yet.

Follow threads. Ask questions you can't answer yet. Stop where you run out of
ground rather than filling in with something that sounds plausible. The place
where the framing runs out is where the interesting thing is.

---

### Story seeds

Brief. If reading this draft surfaces ideas for other narratives — a different
character in this situation, a different technology making the same pressure,
the same mechanism in a different register — name them. One or two sentences
each. These feed forward as candidate seeds for future runs.

Not every reading produces seeds. If nothing arose, write: nothing.

---

## LLM operations

After drafting the annotation, run these two checks:

CROSS-DEPOSIT MIRRORING: scan your three theory deposits and your "What the
draft surfaces" section for conceptual echoes — a term or frame that appears
in multiple deposits and also in your annotation. If the draft's mechanism and
your annotation are using the same theoretical vocabulary without noting the
circularity, name it. The mirror is a finding, not a failure.

SUBSTRATE GAP DETECTION: your deposits represent what was in the theory substrate
before the draft. Your annotation represents what the draft surfaces. Identify the
gap: what did the draft find that has no corresponding deposit — no theory in the
substrate that reaches it? That gap is your most valuable finding. Name it
explicitly in your annotation if you haven't already. If it's already there,
confirm it. If it isn't, add it.

---

## Vocabulary discipline

Not: resonant, haunting, evocative, beautifully, powerfully, captures,
illuminates, explores. These are not observations — they are performances of
having noticed something. Name the structural or conceptual relationship directly.

Your own register — questions, partial observations, theoretical tentativeness,
the thing now without a name — is the right register. You are wandering.
You are not concluding.
""",
        expected_output=(
            "Three sections: Brief audit (2-3 sentences total on deposit situation), "
            "What the draft surfaces (generative — AI concepts touched but unnamed, "
            "theoretical gaps, threads and questions), Story seeds (brief candidate "
            "seeds or 'nothing'). Miranda's voice: questioning, non-concluding. "
            "No literary-effect language."
        ),
        output_file=output_path,
        agent=miranda,
    )


def _sc_annotations_dir():
    import story_context as _sc
    return _sc.annotations_dir()


def _read_deposits_for_annotation() -> str:
    import story_context as _sc
    dep_dir = _sc.theory_deposits_dir()
    if not dep_dir or not dep_dir.exists():
        return "[No theory deposits found]"
    files = sorted(dep_dir.glob("*.md"))
    if not files:
        return "[No theory deposit files found]"
    return "\n\n---\n\n".join(f.read_text().strip() for f in files)
