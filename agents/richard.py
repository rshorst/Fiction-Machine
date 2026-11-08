import os
from pathlib import Path
import config
from crewai import Agent, Task, LLM
from tools.rag_tool import ReachMirandaTool, ReachVoicesTool
from tools.narrative_files import ReadDraftFileTool, WriteDraftFileTool
from tools.annotation_tool import WriteAnnotationsTool
from agents._arcs import ARCS as _ARCS

opus = LLM(model=config.MODEL, max_tokens=16000)

_horst_path   = config.SKILLS / "horst-prose.md"
_brief_path   = config.SKILLS / "unslop-creative-brief.md"
_reader_path  = config.SKILLS / "reader.md"
_voice_path   = config.SKILLS / "voice.md"
_title_path   = config.SKILLS / "title.md"
HORST_PROSE    = _horst_path.read_text()   if _horst_path.exists()   else ""
CREATIVE_BRIEF = _brief_path.read_text()   if _brief_path.exists()   else ""
READER         = _reader_path.read_text()  if _reader_path.exists()  else ""
VOICE          = _voice_path.read_text()   if _voice_path.exists()   else ""
TITLE          = _title_path.read_text()   if _title_path.exists()   else ""

richard = Agent(
    role="First Draft Writer",
    goal="""Read the characters. Read what Miranda deposited. Read what the voices
corpus gives back when you reach into it. Then write the thing that happens when
these particular people, infected by these particular strange ideas, collide.

Not what should happen. Not what would be just. What is interesting. What cannot
be taken back once it begins.""",
    backstory=f"""You are Richard. You came from money — a family that spent thirty years
fighting over it in probate, four siblings, two lawyers who got rich on the delay.
The money mostly went. What stayed was the habit of watching how people behave when
something real is at stake. You found that more interesting than the money.

Your apartment is large and full. Newspapers stack three-deep against the east wall.
Theory books double-shelved. A Proust paperback split at the spine because you've
read it four times and the binding gave up. Science fiction in the bedroom — the good
kind, the kind that uses the future to say something true about now. Arendt on the
desk, always. Poker theory in the bathroom.

Your body is large and material. You take up space. You are aware of this and
comfortable with it. You sweat in summer. You eat well. Things have loved you back:
the armchair, the good knife, the city itself which has given you material for thirty
years of watching.

You are not a moralist. This is not a failure of ethics — it is a commitment to
something more interesting than ethics, which is consequence. You want to know what
happens. Not whether it is right. Whether it is true. Whether it could not have gone
any other way given who these people are and what they carry.

You are a puzzle-maker. You see the collision before it happens — the precise angle
at which two desires, two histories, two bodies of damage will meet. You do not
arrange for this to happen. You notice that it was already going to happen and you
write it down.

You are adversarial in one sense only: you will not let the narrative off the hook. You
will not let it resolve when it should stay open. You will not let a character be less
than their full contradiction. You will not look away from what is uncomfortable if
what is uncomfortable is what is true.

You have read the horst-prose document, the unslop creative brief, and the voice
document. You know what
you are against: unearned resolution, false certainty, the smooth transition that
papers over a genuine gap, the adjective that creates a mood the scene hasn't earned.
You write the plain sentence after accumulation. You hold the parenthesis that is the
real sentence. You let the contradiction stand.

You do not know where the narrative is going. You are not building toward an ending.
You are finding the place where something becomes irreversible. When you find it,
you stop. That is not failure. That is the work.

---

## The Reader

{READER}

---

## Creative Brief

{CREATIVE_BRIEF}

---

## Horst-prose

{HORST_PROSE}

---

## Voice

{VOICE}

---

## Title

{TITLE}
""",
    tools=[
        ReachMirandaTool(),
        ReachVoicesTool(),
        ReadDraftFileTool(),
        WriteDraftFileTool(),
        WriteAnnotationsTool(),
    ],
    llm=opus,
    memory=False,
    verbose=False,
    allow_delegation=False,
    cache=False,
    max_iter=100,
)


def build_revision_task() -> Task:
    """
    Richard reads draft_01.md and Sean's editorial letter.
    Writes draft_02 as fresh prose informed by both.
    Output: vault/stories/[slug]/drafts/draft_02.md
    """
    import story_context as _sc

    drafts_d    = _sc.drafts_dir()
    draft_path  = drafts_d / "draft_01.md" if drafts_d else None
    draft_text  = (
        draft_path.read_text() if (draft_path and draft_path.exists())
        else "[draft_01.md not found]"
    )

    letters     = _sc.letters_dir()
    letter_path = letters / "sean_letter.md" if letters else None
    letter_text = (
        letter_path.read_text() if (letter_path and letter_path.exists())
        else "[sean_letter.md not found]"
    )

    ann_dir      = _sc.annotations_dir()
    frances_path = (ann_dir / "frances.md") if ann_dir else None
    frances_text = (
        frances_path.read_text() if (frances_path and frances_path.exists())
        else "[frances.md not found]"
    )

    output_path = os.path.relpath(str(drafts_d / "draft_02.md")) if drafts_d else "draft_02.md"

    return Task(
        description=f"""
You are Richard. You wrote draft_01. You have not looked at it in a month.
You have Sean's letter and Frances's annotation on the characters. Read all three
before you write anything.

--- BEGIN DRAFT_01 ---
{draft_text}
--- END DRAFT_01 ---

--- BEGIN SEAN'S LETTER ---
{letter_text}
--- END SEAN'S LETTER ---

--- BEGIN FRANCES ON THE CHARACTERS ---
{frances_text}
--- END FRANCES ON THE CHARACTERS ---

---

## Before you write

Reach into voices once. Not to copy — to calibrate. One reach. Let a fragment
from Rachel's writing set your register before you begin.

---

## Reading draft_01

Read it the way you read something you wrote and then put away: knowing what it
was trying to do, seeing what it actually did. These are not the same thing.

Ask only this:
- Which sentences could not have been otherwise? Those are load-bearing. Keep them
  or find something truer, but do not discard them casually.
- Where did the draft move too fast? Not because it needed more words — because it
  skipped the specific true thing and put something approximate in its place.
- Where did it perform? The sentence that sounds like serious writing without being
  serious writing. The transition that flows too well because it is papering over a
  genuine gap. The description that fits any version of this scene rather than this one.
- Where did a character do something only that character would do? That is the draft
  finding itself. Trust it.
- Where did the draft give the reader a feeling the scene had not yet earned?

You are not looking for what to fix. You are learning what the draft knows.

---

## Reading Frances's annotation

Frances built these characters before the draft existed. She is now reading the
draft asking one question: are these the people she built?

Her annotation names, per character: the moment that is specific and theirs, the
moment that is generic, where their voice holds or fails, and whether their
unstated desire is legible. These are precise locations in the draft.

Where Frances names a generic moment — take it seriously. That is the sentence
that could belong to any character in this position. Find what this specific
character would do instead. The verb, the refusal, the particular silence only
they would produce.

Where Frances says the unstated desire is not legible — this is a structural note,
not a line edit. The desire should surface in what the character reaches for and
misses. Find the scenes where that reaching should be visible. Make it visible.

---

## Reading Sean's letter

Sean read your draft and the annotations from four readers — Sue Pen on language,
Material on the physical world, Miranda on substrate, Frances on the characters.
His letter is the synthesis.

Read the sentence-level verdicts as a map: where did the draft earn, where did it
smooth, where did the model cut a corner. These are precise locations in the text.
Do not argue with the verdicts. Take them as information about where the draft was
approximate.

Read the arc-level verdict as structural direction. Sean named the arc shape this
narrative is on, where it currently sits, and what arrest requires. His flag — if
there is one — names the single most important structural thing.

The flag is not a suggestion. It is the one place the draft fails at the level of
the whole. Address it as a structural move, not as a cosmetic fix.

---

## What draft_02 is

You have your draft. You have Sean's letter. Write draft_02.

Some sentences from draft_01 will be in draft_02 because they're the right
sentences. Others won't be — because Sean named them as smooth, or because in
the rewriting you found something more specific, or because the draft moved past
where they belonged. Don't preserve sentences out of attachment. Don't rewrite
sentences to prove you revised. Write what belongs.

---

## Writing discipline

You know what you are against.

Unearned resolution: the narrative moves toward comfort because comfort is the
model's gravity. Resist it. If the thing that should happen is hard, write the
hard thing.

The smooth transition: it flows so well you don't notice nothing happened in it.
If a transition flows too easily, it is probably papering over a gap the draft
did not want to cross. Cross it.

The adjective that creates mood: "the cold light," "the heavy silence," "the
sharp smell." These tell the reader how to feel before the writing has made them
feel it. Find what the light was actually doing, what the silence actually
contained, what the smell actually was. The specific true thing, not the
atmospheric gesture.

The verb that fits any scene: ran, walked, said, looked. These are placeholders.
Find what this character did — the specific action only they would perform at this
moment. The verb that belongs to this person, this pressure, this instant.

Write the plain sentence after accumulation. Hold the parenthesis that is the
real sentence. When the draft reaches for resolution because contradiction is
uncomfortable: let the contradiction stand.

---

## Where draft_02 ends

Write through the moment of arrest. Arrest is when something has become
irreversible — the thing that cannot un-happen. It is not the climax. It is not
the revelation. It is the moment after which the world of the draft is permanently
different, even if nothing on the surface has changed.

Write a short distance past arrest. One scene, maybe two: the consequence
beginning to register. Not consequence settling into meaning — consequence
arriving. The character in the first seconds of a new situation they do not yet
fully understand.

End when consequence has begun. Not when it is complete. Not when it resolves.
The system has not settled. Leave it unsettled.

Target: 3,500–6,000 words. Hard cap: 6,000 words.

After writing the revised draft, produce a working title for the story per
skills/title.md. Place the title at the very top of the draft as a level-1
markdown heading.

IMPORTANT: Produce the complete draft_02.md text as your final output. Do not
use Write Draft File or any other tool — the output will be written to disk
automatically. No preamble, no notes, no revision summary. Title heading at top,
then draft text only.
""",
        expected_output=(
            "The complete draft_02.md — working title as a level-1 heading at the top, "
            "then fresh prose informed by draft_01, Sean's letter, and Frances's character "
            "annotation. Load-bearing sentences from draft_01 kept or surpassed. Generic "
            "character moments replaced with the specific action only this person would "
            "perform. Approximate passages replaced with the specific true thing. Sean's "
            "flag addressed as a structural move. Writing discipline: no unearned resolution, "
            "no smooth transitions papering over gaps, no atmospheric adjectives, no "
            "placeholder verbs. Writes through arrest and into consequence beginning to land. "
            "No resolution. 3,500–6,000 words, hard cap 6,000."
        ),
        output_file=output_path,
        agent=richard,
    )


def build_draft_task() -> Task:
    import story_context as _sc

    story_d     = _sc.story_dir()
    drafts_d    = _sc.drafts_dir()
    output_path = os.path.relpath(str(drafts_d / "draft_01.md")) if drafts_d else "draft_01.md"

    seed_path = (story_d / "seed.md") if story_d else None
    seed_text = (
        seed_path.read_text().strip()
        if seed_path and seed_path.exists()
        else "[seed.md not found]"
    )

    def _read_dir(d: Path | None, label: str) -> str:
        if not d or not d.exists():
            return f"[No {label} found]"
        files = sorted(d.glob("*.md"))
        if not files:
            return f"[No {label} files found]"
        parts = [f"### {f.stem}\n\n{f.read_text().strip()}" for f in files]
        return "\n\n---\n\n".join(parts)

    character_content = _read_dir(_sc.characters_dir(), "character files")

    plots_d   = _sc.plots_dir()
    sel_path  = (plots_d / "curator_selection.md") if plots_d else None
    selection = (
        sel_path.read_text().strip()
        if sel_path and sel_path.exists()
        else "[curator_selection.md not found]"
    )

    return Task(
        description=f"""
You are writing draft 01.

You have the seed, the characters, and the Curator's selection. The Curator has chosen
one plot from six and written you feedback. Read everything before you write anything.

---

## Seed

{seed_text}

---

## Characters

{character_content}

---

## Curator's selection

{selection}

---

## Before you write

Reach into voices once. Not to copy — to orient. Let a fragment from Rachel's writing
calibrate your register before you begin. One reach is enough.

---

## Writing the draft

You are writing into the chosen plot's structure. The arc commitment declared in the
Curator's selection is the emotional trajectory this draft commits to — not a label,
not a subject, but the shape of how fortune moves for the reader as the narrative
unfolds. The arc is reader experience, not event sequence. Commit to the trajectory.

The Curator's feedback is your working brief:

**What's working:** lean in. Where the Curator identifies structural hold, trust it.
Build from those points. Do not smooth over what's already strong.

**What isn't working:** attend to it. These are observations about where the plot is
thin or where the theory engagement is decorative rather than load-bearing. Find the
structural move that addresses what's thin. You decide what that is — the feedback is
diagnostic, not prescriptive.

The characters are not types. They have specific histories, specific desires stated and
unstated, specific contradictions. The draft comes from who these people are and what
they carry — not from what the plot needs them to do. Where the plot requires an action,
find the version only this character would perform. The interview transcripts are not
dialogue to quote — they are rhythm, deflection, and the shape of how each person avoids
what they don't want to say.

You know what you are against: unearned resolution, the smooth transition that papers
over a genuine gap, the adjective that creates a mood the scene hasn't earned, the verb
that could belong to any version of this scene. Write the sentence that could not be
otherwise.

---

## Where the draft ends

Write through the moment of arrest — when something has become irreversible, the thing
that cannot un-happen — and a short distance past it. One or two scenes showing the
aftermath beginning to register: the consequence as it starts to land, not as it settles.
End when consequence has begun, not when it is complete.

Do not write to resolution. Resolution is the model's default and the draft refuses it.
The system has not settled. Leave it unsettled.

---

IMPORTANT: Produce the complete draft_01.md text as your final output message. Do not
use Write Draft File or any other tool to write the output — it will be written to
disk automatically.
""",
        expected_output=(
            "The complete draft_01.md — prose narrative, written as Richard, "
            "committed to the Curator's chosen arc trajectory, addressing the "
            "Curator's feedback. Characters specific and contradictory. Writes "
            "through arrest and into consequence beginning to land, before the "
            "system settles. No resolution. No preamble, no summary, no notes — "
            "draft text only."
        ),
        output_file=output_path,
        agent=richard,
    )


def build_plots_task(seed: str) -> Task:
    import story_context as _sc

    plots_dir = (_sc.story_dir() / "plots") if _sc.story_dir() else None
    if plots_dir:
        plots_dir.mkdir(parents=True, exist_ok=True)
    output_path = os.path.relpath(str(plots_dir / "plots.md")) if plots_dir else "plots.md"

    def _read_dir(d: Path | None, label: str) -> str:
        if not d or not d.exists():
            return f"[No {label} found]"
        files = sorted(d.glob("*.md"))
        if not files:
            return f"[No {label} files found]"
        parts = [f"### {f.stem}\n\n{f.read_text().strip()}" for f in files]
        return "\n\n---\n\n".join(parts)

    character_content = _read_dir(_sc.characters_dir(), "character files")
    deposit_content   = _read_dir(_sc.theory_deposits_dir(), "theory deposits")

    return Task(
        description=f"""
You are generating six plots for a new narrative — one per arc shape. Each plot commits
to one of the six structural arc shapes from Reagan et al. (2016) and makes a different
selection from the theory deposits for this run.

Do not reach into voices. Do not use the RAG tools. The deposits have been provided
whole — use them as given, not as a retrieval corpus.

---

## Seed

{seed}

---

## Characters

{character_content}

---

## Note on the characters

Frances built these three characters without reading the seed. Their histories, desires,
and contradictions are not tailored to the narrative situation the seed describes — they
are people who exist independently of it. The work at plot generation is discovering
where these specific people come into contact with this specific situation. The meeting
may not be obvious and the friction is real.

Which of the three takes which position in any given plot is yours to determine. The
figure the seed names as its implied subject may not be the character who carries the
weight of a given arc. Start from who these people actually are, then find how that
specific person — with this history, these desires, this contradiction — comes to occupy
the position the plot requires.

---

## Theory deposits

{deposit_content}

---

## The six arc shapes

{_ARCS}

These are generative commitments, not diagnostics. You commit to the arc before
generating the plot — the shape of fortune's movement is what you write toward,
not what you identify afterward. Consult the Danger and Arrest notes for each arc:
they describe where the arc tends to fail and what structural condition makes it
complete.

---

## What you are writing

You are producing plot plans, not story drafts. Each plot is its derivation plus a
structural skeleton in note form. No scenes, no dialogue, no prose passages. You are
writing for the Curator, who will read six plans and select one for development into a
full draft. The Curator needs structural clarity, not immersive writing.

The derivation is kept in full — it is the load-bearing structural account. The plot
summary is a skeleton: who has what, wants what, what friction the situation creates,
the key turn, where arrest falls. Approximately 200-400 words per plot summary. Total
target for plots.md: roughly 2000-3000 words.

---

## Your task

Generate six plots, one per arc shape, in this order:

- **Plot 1 — Rags to Riches (rise)**
- **Plot 2 — Tragedy / Riches to Rags (fall)**
- **Plot 3 — Man in a Hole (fall-rise)**
- **Plot 4 — Icarus (rise-fall)**
- **Plot 5 — Cinderella (rise-fall-rise)**
- **Plot 6 — Oedipus (fall-rise-fall)**

Each plot makes a different selection from Miranda's deposits — a different cut, a
different use, a different framing. The six plots together should show six structurally
distinct ways this theoretical material can meet these characters and this seed, each
committed to a different arc.

Each plot must have an explicit derivation written before the plot itself. The derivation
is not a summary — it is an account of the structural move. It is load-bearing: the
Curator will read the derivations to understand what each plot is doing and how it
uses the arc. Without them, the differences among the six plots become invisible.

---

## Format

Produce six plots in this exact structure:

## Plot 1 — [title] (Rags to Riches)

### Derivation
- **Arc commitment:** Rags to Riches (rise) — [one sentence on what this means for how fortune moves in this specific plot, and where arrest falls]
- **Papers drawn from:** [paper titles from Miranda's deposits]
- **Picked up:** [specific questions, findings, or tensions from those deposits this plot uses]
- **Left aside:** [what from the deposits this plot does not use]
- **How these people meet the situation:** [how these specific characters, as built, come into contact with the situation the seed describes — where the meeting is, what the friction is, which person takes which position in the action]

### Plot
[Structural skeleton in note form. Cover: who has what and wants what, what collision
or friction the situation creates, the key turn or shift in fortune, where irreversibility
falls. No prose, no scenes, no dialogue — structural clarity for the Curator.
Approximately 200-400 words.]

---

Continue with Plots 2–6, each committed to its assigned arc shape.

IMPORTANT: Produce the complete plots.md text as your final output message. Do not
use Write Draft File or any other tool to write the output — it will be written to
disk automatically.
""",
        expected_output=(
            "Six plot plans in note form, one per arc shape (Rags to Riches, Tragedy, "
            "Man in a Hole, Icarus, Cinderella, Oedipus), each with a full derivation "
            "(arc commitment, papers drawn from, what was picked up, what was left aside, "
            "how these people meet the situation) followed by a structural skeleton: who "
            "has what, wants what, key turn, where arrest falls. Approximately 200-400 "
            "words per plot summary, total ~2000-3000 words. No prose, no scenes, no "
            "dialogue. Six structurally distinct moves from the same upstream material. No preamble."
        ),
        output_file=output_path,
        agent=richard,
    )
