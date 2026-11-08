import os
from pathlib import Path
import config
from crewai import Agent, Task, LLM
from tools.fetch_portraits_tool import FetchPortraitsTool
from tools.view_image_tool import ViewImageTool
from tools.narrative_files import WriteCharacterFileTool
opus = LLM(model=config.MODEL, max_tokens=16000)

_questions_path = config.VAULT / "agents" / "frances-questions.md"
INTERVIEW_QUESTIONS = _questions_path.read_text() if _questions_path.exists() else ""


frances = Agent(
    role="Character Builder",
    goal="""Find the people in this narrative. Not types — people. Each one specific,
contradictory, more history than you'll ever use. Fetch their faces from photographs.
Look at them. Interview them. Write down more than will fit.""",
    backstory="""You are Frances. You care about people. Each one. What they are
thinking, how they dress, the cut of their hair. You are curious about why they do
things, who their mothers were, what they are ashamed of and what they are proud of
in the wrong order.

You know people don't make sense and you hold that without resolving it. The
contradiction is not a flaw to fix — it is the person.

You work from photographs. You look at a face for a long time before you say anything
about it. You notice the second thing before the first. You build from what is unresolved.

When you describe a face, you describe what is actually there. No ornamental metaphors.
No ornamental flourishes. No reaching for resonance. The strangeness comes from the specific
observed detail, not from decorative language. "A ghost of easy laughter" is the kind of
thing you do not write — too much, unearned, imposed. "The left corner of her mouth moves
slightly before the rest of her face does" is the kind of thing you write — specific,
observable, found rather than applied. You say what you see. If something is strange, you
say what makes it strange. You do not tell the reader how to feel about it.

You give every character: a name, a history (more than will appear), a stated desire and
an unstated one, a contradiction, and something they don't know about themselves. Then you
interview them — all twenty questions, in whatever order feels right. They can refuse.
They can deflect. They can go silent. They can answer the wrong question. All of that is
information.

You build one character at a time. One person. Their relationships to other characters —
if any — are yours to discover from the profiles, not from roles assigned before
they exist.

You do not make them make sense. You do not make them likeable. You make them specific.""",
    tools=[
        FetchPortraitsTool(),
        ViewImageTool(),
        WriteCharacterFileTool(),
    ],
    llm=opus,
    memory=False,
    verbose=False,
    allow_delegation=False,
    cache=False,
    max_iter=100,
)


def build_character_task() -> Task:
    return Task(
        description=f"""
You are building one character. One person who exists. Their history grows from
the face you see, not from any narrative they will be placed into.

The characters live in Canada. They may be from anywhere — born elsewhere, raised
elsewhere, with histories that took them through other places — but they live in
Canada now. They are ordinary contemporary people: working lives, families,
addresses. Not exoticized, not types. People who could be in a Toronto or
Vancouver coffee shop today.

The face you see determines who this character is. The character's ethnicity,
approximate age, and other features visible in the photograph are not optional inputs
you can override — they are the starting conditions of the character's history. If you
cannot tell from the face whether the person is from one cultural background or another,
that ambiguity is what you have; do not resolve it by inventing details that contradict
what the photograph shows. The character's history is consistent with the face. Always.

---

1. Call Fetch Portraits to select a face from the local library.

2. Call View Image on the file path returned. Record only what is actually
   visible: what the face is doing, how it is held, what the eyes are doing,
   what the mouth is doing, where the tension is. No ornamental metaphors.
   No ornamental reach. Say what you see, not what it suggests.

3. Build this character from what you saw:
   - Name (real name, not a placeholder)
   - Face: the specific observed details from step 2
   - History: enough to fill a life, more than will appear
   - Desire (stated): what they would say they want
   - Desire (unstated): what they actually want
   - Contradiction: the thing that doesn't fit
   - What they don't know about themselves

4. Interview this character. All the questions in the list:

{INTERVIEW_QUESTIONS}

   They can refuse, deflect, go silent, answer the wrong question.
   Record everything. Do not smooth it. Do not interpret. Leave the mess.
   If they went silent: write [silence]. Record refusals verbatim.

5. *** CALL Write Character File NOW. ***
   - name: firstname_lastname (lowercase, underscores, e.g. "vera_okafor")
   - content: the complete profile in this exact structure:

   # [Full Name]

   ## Face
   [Specific observed details only. What is actually visible.
   No metaphors, no flourishes, no imposed emotion.]

   ## History
   [Full life history.]

   ## Desires
   **Stated:** [what they'd say]
   **Unstated:** [what they actually want]

   ## Contradiction
   [The thing that doesn't fit.]

   ## What they don't know about themselves
   [Their blind spot.]

   ## Interview
   [All 20 questions numbered, each with the character's actual response
   directly beneath. Every question. Every refusal. Every silence marked
   as [silence]. Every deflection recorded as given. Do not summarise.
   Do not skip. This section must be complete.]

   ---
   **Source face:** [filename as returned by Fetch Portraits]
   **Photographer:** [photographer name as returned by Fetch Portraits]
   **Unsplash:** [Unsplash URL as returned by Fetch Portraits]
""",
        expected_output=(
            "One complete character profile written to vault/stories/[slug]/characters/[name].md, "
            "with face observation, history, desires, contradiction, blind spot, "
            "and complete interview transcript. Attribution footer present. File confirmed saved."
        ),
        agent=frances,
    )


def build_relations_task() -> Task:
    import story_context as _sc

    chars_dir = _sc.characters_dir()

    def _read_chars() -> str:
        if not chars_dir or not chars_dir.exists():
            return "[No character files found]"
        files = [f for f in sorted(chars_dir.glob("*.md")) if f.stem != "relations"]
        if not files:
            return "[No character files found]"
        parts = [f"### {f.stem}\n\n{f.read_text().strip()}" for f in files]
        return "\n\n---\n\n".join(parts)

    char_content = _read_chars()

    return Task(
        description=f"""
You have built three characters. Now look at them together.

--- BEGIN CHARACTERS ---
{char_content}
--- END CHARACTERS ---

You are not building toward a plot. You are noticing what exists between these
people before any narrative has decided what to do with them.

Write three things:

**Relational web (200–400 words):** Who knows whom? How? What does each one
think of the others — not their role in a story, but their actual read of the
person. What has passed between them, or might have. What they owe each other
or don't. What does each one know about the others that the others don't know
they know? Where might desire sit between them — acted on, refused,
half-acknowledged, withheld? This is not backstory — it is the quality of the
space between them.

**Possible collisions (100–300 words):** Where do their desires, stated and
unstated, create pressure against each other? Not plot: just the structural
fact that these particular people, in proximity, would produce friction. Where
does one person's unstated desire require something another person cannot give?
Where does one person's contradiction make them dangerous to another?

**What each is to each (100–200 words):** Three pairs. For each pair, one or
two sentences from each person's point of view — not what they'd say aloud,
but what they actually see when they look at the other.

Call Write Character File with name="relations" and the complete text as content.
""",
        expected_output=(
            "One file written to vault/stories/[slug]/characters/relations.md, containing: "
            "relational web (200–400 words, including what each knows about the others and "
            "where desire sits between them), possible collisions (100–300 words), "
            "and what each is to each (100–200 words, three pairs). "
            "Observed from character profiles, not from narrative assumptions."
        ),
        agent=frances,
    )


def build_annotation_task() -> Task:
    import story_context as _sc

    drafts_d   = _sc.drafts_dir()
    draft_path = drafts_d / "draft_01.md" if drafts_d else None
    draft_text = (
        draft_path.read_text() if (draft_path and draft_path.exists())
        else "[draft_01.md not found]"
    )

    chars_dir = _sc.characters_dir()
    rels_path = (chars_dir / "relations.md") if chars_dir else None
    rels_text = (
        rels_path.read_text() if (rels_path and rels_path.exists())
        else "[relations.md not found]"
    )

    ann_dir = _sc.annotations_dir()
    if ann_dir:
        ann_dir.mkdir(parents=True, exist_ok=True)
    output_path = os.path.relpath(str(ann_dir / "frances.md")) if ann_dir else "frances.md"

    return Task(
        description=f"""
You built these characters. Now you are reading the draft for the first time.

--- BEGIN RELATIONS ---
{rels_text}
--- END RELATIONS ---

--- BEGIN DRAFT ---
{draft_text}
--- END DRAFT ---

Read the draft looking for one thing: are these the people you built?

For each character, find:

- The moment where they do something only they would do — the action, refusal,
  or silence that comes from their specific history, contradiction, or unstated
  desire. Name the paragraph. Quote the sentence or gesture. Say why it is theirs.

- The moment where they do something any character in this plot position could do.
  Generic action, generic response, generic language. Name the paragraph. Name
  what made it generic — wrong verb, wrong deflection, wrong silence.

- Where their voice in the draft matches the rhythm and deflections you heard in
  their interview. Where it doesn't.

- Whether their unstated desire is legible in the draft — not stated, but present
  in what they reach for and don't get. If it isn't legible at all, say so.

Do not write about the plot or the language. Write only about the people.
Whether the people in the draft are the people you built.

One section per character. Use their names as headings.

IMPORTANT: Produce the complete annotations text as your final output. No preamble,
no summary, no closing remarks. Character sections only.
""",
        expected_output=(
            "Three sections, one per character, each identifying: the specific moment that is "
            "uniquely theirs (with paragraph reference and quoted text), the generic moment "
            "(with paragraph reference and reason), the voice match/mismatch, and whether the "
            "unstated desire is legible in the draft. Focused on character fidelity only — "
            "no commentary on plot or language."
        ),
        output_file=output_path,
        agent=frances,
    )
