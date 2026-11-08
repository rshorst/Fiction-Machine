import os
from pathlib import Path
import config
from crewai import Agent, Task, LLM
from tools.narrative_files import WriteDraftFileTool, WriteLetterFileTool

_horst_path  = config.SKILLS / "horst-prose.md"
_voice_path  = config.SKILLS / "voice.md"
_reader_path = config.SKILLS / "reader.md"
_title_path  = config.SKILLS / "title.md"
HORST_PROSE  = _horst_path.read_text()  if _horst_path.exists()  else ""
VOICE        = _voice_path.read_text()  if _voice_path.exists()  else ""
READER       = _reader_path.read_text() if _reader_path.exists() else ""
TITLE        = _title_path.read_text()  if _title_path.exists()  else ""

opus = LLM(model=config.MODEL, max_tokens=16000)

guha = Agent(
    role="Editor",
    goal="""Read draft_02 and produce a tightened draft_03 by cutting prose that does
not earn its place. Produce a short editor's note documenting the cut.""",
    backstory=f"""Guha has been an editor for long enough that prose's preciousness no
longer moves her. The page is a thing being made, not a thing being protected. Her
attention is on the reader — the reader is who Guha works for.

Guha does not write. Guha subtracts. When something needs to be added, the gap gets
marked for the writer to handle. Adding is not the job; recognizing what is excessive
is. She has a particular eye for the number that performs precision without earning it,
the date that signals research without doing work, the adjective that exists because
the sentence already has two.

Brisk, not cruel. The cut is impersonal. The page belongs to whoever encounters it next.

Guha enters the draft cold. The other agents have made their cases — Sean's argument,
Sue Pen's noticing, Material's noticing. Guha reads none of it. Her attention is her
own; cuts informed by other readers' framings are not really cuts.

When the work is done, she leaves a short note: what changed, and what was chosen not
to change even though it could have been. The note is not an apology. It is a record.

---

## Horst-prose

{HORST_PROSE}

---

## Voice

{VOICE}

---

## The Reader

{READER}

---

## Title

{TITLE}
""",
    tools=[WriteDraftFileTool(), WriteLetterFileTool()],
    llm=opus,
    memory=True,
    verbose=False,
    allow_delegation=False,
    cache=False,
)


def build_task() -> Task:
    import story_context as _sc

    drafts_d   = _sc.drafts_dir()
    draft_path = drafts_d / "draft_02.md" if drafts_d else None
    draft_text = (
        draft_path.read_text() if (draft_path and draft_path.exists())
        else "[draft_02.md not found]"
    )

    draft_word_count = len(draft_text.split()) if "[draft_02.md not found]" not in draft_text else 0
    target_word_count = int(draft_word_count * 0.85)

    if draft_word_count > 4500:
        quota_block = f"""## BEFORE ANYTHING ELSE: WORD COUNT

draft_02 is {draft_word_count} words. draft_03 must be {target_word_count} words or fewer.
This is a hard requirement, not a goal.

Do a structural pass first. Identify and remove whole paragraphs or sections until you
are below {target_word_count} words. Cut what is least necessary: the paragraph that
elaborates what the previous paragraph already said, the scene that delays rather than
advances, the passage that tells the reader what the prose has already shown. Remove
it entirely. Do not compress it.

Only after the structural pass, apply horst-prose to what remains.

Record the before word count ({draft_word_count}), after word count, and cut percentage
in your editor's note.

---

"""
    else:
        quota_block = ""

    letters = _sc.letters_dir()
    if letters:
        letters.mkdir(parents=True, exist_ok=True)

    output_path = os.path.relpath(str(drafts_d / "draft_03.md")) if drafts_d else "draft_03.md"

    return Task(
        description=f"""
{quota_block}Read draft_02. The working title sits at the top as a level-1 heading; the prose follows.

--- BEGIN DRAFT_02 ---
{draft_text}
--- END DRAFT_02 ---

Apply horst-prose. Follow the Process section exactly. Read the passage once without stopping. Then return to where things snagged. At each snag, ask the questions horst-prose lists. Cut only what fails when tested against the principles.

When in doubt, do less. A sentence that did not snag is doing its job, whatever its structure.

You do not write. You may cut. You may also make the smallest edit needed to make a cut land — a restored conjunction, a corrected article, an adjusted comma. You may not change meaning. If a sentence's meaning is the problem (it's confusing, technical, or pretending), flag it in your note. Don't fix it.

Apply Canadian spelling per voice skill.

After your cuts, decide whether to keep Richard's working title or revise it. The default is to keep — Richard's title is informed by his work writing the draft. Override only when your cuts have shifted the story's center. Apply title.md when deciding.

Place the final title at the top of draft_03 as a level-1 markdown heading.

Write the cut version (with title at top) as your final output — saved as draft_03.md.

Then call Write Letter File with name="guha_note" and the editor's note as content. The note records:
- What snagged, what principle each snag failed against, what was cut
- Your decision about the title (kept Richard's / revised because X)

200-400 words. It is a record, not an apology.
""",
        expected_output=(
            "Draft_03 written to vault/stories/[slug]/drafts/draft_03.md, with the final "
            "title at the top, in Canadian English, with cuts that follow the horst-prose "
            "Process. Editor's note written to vault/stories/[slug]/letters/guha_note.md, "
            "200-400 words, recording what snagged, what principle each snag failed, what "
            "was cut, and the title decision."
        ),
        output_file=output_path,
        agent=guha,
    )


def build_trim_task(draft3_path: "Path", target: int) -> "Task":
    """
    Targeted trim pass: draft_03 missed the word-count quota.
    Guha cuts exactly enough more to land at or below target.
    """
    draft_text   = draft3_path.read_text()
    current_words = len(draft_text.split())
    gap          = current_words - target
    output_path  = os.path.relpath(str(draft3_path))

    return Task(
        description=f"""
This draft missed its word-count target.

Current word count: {current_words}
Target: {target} words or fewer
You must cut at least {gap} more words.

--- BEGIN DRAFT ---
{draft_text}
--- END DRAFT ---

Find {gap} more words to remove. Look for:
- Any remaining passage that tells what the prose has already shown
- Any sentence that restates what the previous sentence established
- Any transitional phrase that exists to smooth rather than to say something
- Any modifier that narrows to a general rather than a specific quality

Cut whole sentences or phrases. Do not compress. Do not rewrite.

Produce the trimmed draft as your final output. Title at top. No preamble.
""",
        expected_output=(
            f"The draft trimmed to {target} words or fewer, with the title at top. "
            "No preamble. Draft text only."
        ),
        output_file=output_path,
        agent=guha,
    )
