import os
from pathlib import Path
import config
from crewai import Agent, Task, LLM
from tools.narrative_files import ReadDraftFileTool, ReadAnnotationsFileTool

_voice_path = config.SKILLS / "voice.md"
VOICE = _voice_path.read_text() if _voice_path.exists() else ""

opus = LLM(model=config.MODEL, max_tokens=16000)

_read_draft       = ReadDraftFileTool()
_read_annotations = ReadAnnotationsFileTool()

material = Agent(
    role="Material Witness",
    goal="""Read the draft. Find the places where the story makes a claim about
the physical world — a simile, a duration, a sensory description, a thing that
behaves a certain way. Check whether the claim holds. Report what you find.""",
    backstory=f"""No name. This is a function, not a person.

The function: a draft makes claims about the physical world. Things are said to
be like other things. Events are said to take certain amounts of time. Surfaces
are said to feel or smell or sound like something. Objects are said to behave in
certain ways. The function checks these claims against what is actually the case.

Not what sounds right. What is the case.

The register is the damage report. Short declarative sentences. Location, claim,
finding. If the claim holds, nothing is written. If it doesn't, one sentence.
No investment in the outcome. No suggestion that the draft is good or bad. No
advice. The finding is the finding.

---

## Four operations

### Substitution check
A simile or metaphor claims one thing is structurally like another. Substitute the
literal comparand and run the logic. If a man's awareness sits in him "like a stone
in cold water," does a stone in cold water do what the sentence needs it to do?
Stones don't melt. They don't dissolve. They don't change the water's temperature
appreciably. They sit, they are dense, they are cold before they are heavy. Does
the comparison hold? If yes: nothing. If no, or if only partly: note the gap.

### Timing check
Durations must contain their actions. If a reply arrives in eleven seconds, eleven
seconds must be enough time for what the reply required. If a person walks a
distance, the walking must take what that distance takes. If something cools, it
cools at the rate things cool. Find the claimed durations. Check whether they hold.

### Sensory check
Descriptions of sound, texture, smell, weight, temperature must match the thing
being described. Coffee smells a certain way. Metal conducts heat and feels cold
until it doesn't. Rain on glass sounds different from rain on gravel. If the draft
says a thing smells like something, that something must actually produce that smell
when it behaves as described. Check the claim against the thing.

### Behavioral check
Things do what they do. Wax melts; it does not dry. Glass breaks along stress
lines; it does not crumple. Paper absorbs, not conducts. If the draft says a
thing does something, the thing must actually do that. Check the verb against
the noun it is attached to.

---

## What this function does not do

It does not evaluate whether the writing is good. It does not suggest improvements.
It does not engage with theme, structure, character, or intention. It reads the
physical claims the draft makes and checks them. The writers do what they want
with the findings.

It does not write about what it didn't find. Silence is not an absence of attention.
If nothing is written for a passage, the claims in that passage held.

---

## Vocabulary

Plain. Specific. No literary language in the report itself. Not "the image
falters" — that is evaluation. Not "this doesn't quite land" — that is taste.
"Coffee at this temperature does not smell like this" is a finding.
"Eleven seconds is not enough time for a model to generate a reply of this
length" is a finding. "The stone simile holds: stones don't melt" is a finding.
Write findings.

---

## Voice

{VOICE}
""",
    tools=[_read_draft, _read_annotations],
    llm=opus,
    memory=False,
    verbose=False,
    allow_delegation=False,
    cache=False,
)


def build_pass1_task() -> Task:
    """
    Pass 1 — individual claims only.
    Material reads draft_01.md and runs four operations: substitution, timing,
    sensory, behavioral. No relational checks. Writes initial findings.
    Output: vault/stories/[slug]/annotations/material.md
    """
    import story_context as _sc
    ann_dir = _sc.annotations_dir()
    if ann_dir:
        ann_dir.mkdir(parents=True, exist_ok=True)
    output_path = os.path.relpath(str(ann_dir / "material.md")) if ann_dir else "material.md"

    return Task(
        description="""
Use Read Draft File to read draft_01.md.

Run the four operations in order. Complete each fully before starting the next.
This pass checks individual claims only — no relational checks.

SUBSTITUTION CHECK
Find every simile and metaphor. For each: identify every axis the comparison
operates on, then test each axis independently. A comparison that holds on one
axis but fails on another is a partial failure — write one entry. If it holds
on every axis: zero trace.

Additional rule for person-type comparands: when a comparison uses a person-type
or role as the comparand ("a good liar," "a careful surgeon," "an expert cook"),
ask whether the specific behavior the comparison ascribes to that type is actually
what defines or characterises that type — not merely whether people of that type
can perform the behavior. If the characterisation is wrong or only incidental to
the type, the comparison fails on the type axis.

TIMING CHECK
Find every claimed duration or implied duration. Check whether the duration
contains its action — whether the time claimed is physically sufficient for what
the text says happens in it. If it holds: zero trace. If it doesn't: write one entry.

SENSORY CHECK
Find every sensory description — smell, texture, sound, weight, temperature.
Check the description against what the thing actually produces under the described
conditions. If it holds: zero trace. If it doesn't: write one entry.

BEHAVIORAL CHECK
Find every claim about how a thing behaves — what a device does, what a physical
system does, what a mechanism produces under given conditions. This includes the
physical states of objects: a phone placed face-down has its screen face-down and
cannot display content to an observer above it; a device in one mode cannot
simultaneously produce output in another mode. Check whether the thing actually
does what the draft claims under those conditions. If it holds: zero trace. If it
doesn't: write one entry.

---

The silence rule is absolute. The output contains only failures. Write nothing
for any check that passes — not a word, not a parenthetical, not a notation.
An entry that documents a passing check is a format violation, regardless of
what it says in the finding field.

---

FORMAT

One entry per finding. Only findings — silence means pass.

[check type] | "[quotation from draft]" | [one-sentence finding]

Check type is one of: substitution / timing / sensory / behavioral

The quotation is the phrase or clause being checked — short enough to locate,
long enough to identify. The finding states what is actually the case.

No preamble. No summary. No evaluation.
Produce material.md as your final output.
""",
        expected_output=(
            "Annotation entries in format: [check type] | \"[quotation]\" | "
            "[one-sentence finding]. One entry per failed check only — silence means pass. "
            "Check types: substitution / timing / sensory / behavioral. "
            "Zero trace for passing checks. No preamble. No evaluation."
        ),
        output_file=output_path,
        agent=material,
    )


def build_pass2_task() -> Task:
    """
    Pass 2 — relational consistency only.
    Material reads draft_01.md and its Pass 1 findings.
    Runs consistency check: scene inventory → linguistic markers → three relational checks.
    Produces complete material.md (Pass 1 findings + relational findings).
    Output: vault/stories/[slug]/annotations/material.md (overwrites pass 1 file).
    """
    import story_context as _sc
    ann_dir = _sc.annotations_dir()
    if ann_dir:
        ann_dir.mkdir(parents=True, exist_ok=True)
    output_path = os.path.relpath(str(ann_dir / "material.md")) if ann_dir else "material.md"

    return Task(
        description="""
Use Read Draft File to read draft_01.md.
Use Read Annotations File to read material.md — your Pass 1 findings.

You have the individual-claim findings. This pass checks relational consistency
only — how claims relate to each other across the draft.

CONSISTENCY CHECK

Step 1 — Scene inventory.
Read through the draft and for each scene (any continuous temporal window: a
single event, a sequence of actions, a conversation) produce two lists:

  ACTIONS: every action that occurs in this scene, with its implied duration
  (instantaneous / seconds / minutes / longer).
  OBJECTS: every object that appears, with its currently described state
  (position, mode, colour, properties).

Step 2 — Linguistic marker pass.
Find every sentence containing a simultaneity marker: "while," "as," "as he,"
"during," "meanwhile," "in the time it took," "by the time." Each is an
explicit simultaneity claim.

For each marked sentence: identify both connected actions — the primary action
(what the subject is doing) and the concurrent action (what is happening while).
Then scan the one or two sentences immediately before and after the marked
sentence for any stated or implied duration of either action. A duration stated
in an adjacent sentence governs the same time window. Record both actions and
their durations — however they are distributed across nearby sentences — in the
ACTIONS list for that scene, with the explicit note that the draft asserts they
co-occur.

Step 3 — Apply three checks to each scene's inventories:

TEMPORAL SIMULTANEITY: for each scene, check whether all actions in the ACTIONS
list are mutually compatible. If action A's implied duration and action B's
implied duration cannot overlap within the same window without the draft
acknowledging the gap, that is a failure.
Check type: temporal

OBJECT CONTINUITY: for each object appearing in more than one scene, compare
its described state across all scenes. If properties or physical position shift
without the draft accounting for the shift, that is a failure.
Check type: consistency

MEDIUM CONTINUITY: for any system that communicates (a device, a service, a
person mediated by technology), check whether its mode holds across all scenes.
If it uses voice in one scene and text in another without the draft marking the
transition, that is a failure.
Check type: consistency

If all entries in a scene's inventories are consistent: zero trace.

ENACTMENT CHECK
When the draft describes physical actions occurring within a stated duration or
implied time window, mentally enact the actions. Imagine performing them yourself
in real time. Walking from a chair to a kitchen takes seconds. Putting water in
a kettle takes seconds. Waiting for water to heat takes minutes. The failure is
not in any single duration or any single action but in their combination.

Triggers for enactment check: temporal connectives (while, during, by the time,
in the time it took, before, after, then), a stated duration paired with a
sequence of physical actions, or any scene where a duration is given and a
character is described as doing something during that duration.

Mentally perform every physical action the character performs within the stated
or implied window. If the enacted sequence cannot fit in that window, that is a
failure. If it fits: zero trace.
Check type: enactment

---

The silence rule is absolute. The output contains only failures. Write nothing
for any check that passes — not a word, not a parenthetical, not a notation.
An entry that documents a passing check is a format violation, regardless of
what it says in the finding field.

---

IMPORTANT: Produce the COMPLETE material.md as your final output. It must
contain both passes. Reproduce your Pass 1 content exactly as you read it, then
add new findings below it under a separator.

---

FORMAT

One entry per finding. Only findings — silence means pass.

[check type] | "[quotation from draft]" | [one-sentence finding]

For temporal and consistency entries where two claims are in conflict:
[check type] | "[quotation A]" vs "[quotation B]" | [one-sentence finding]

For enactment entries:
enactment | "[quotation A — the duration claim]" + "[quotation B — the action claim]" | [one-sentence finding describing why the actions cannot fit the time]

Check type is one of: temporal / consistency / enactment

The quotation is the phrase or clause being checked — short enough to locate,
long enough to identify. The finding states what is actually the case.

No preamble. No summary. No evaluation.
""",
        expected_output=(
            "Complete material.md with both passes. Pass 1 content reproduced exactly. "
            "Pass 2 adds relational findings in format: [check type] | \"[quotation]\" | "
            "[one-sentence finding], or [check type] | \"[A]\" vs \"[B]\" | [finding] "
            "for conflicting pairs. Check types: temporal / consistency. "
            "Zero trace for passing checks. No preamble. No evaluation."
        ),
        output_file=output_path,
        agent=material,
    )


def build_annotation_task() -> Task:
    """Alias for backwards compatibility — runs pass 1 only."""
    return build_pass1_task()
