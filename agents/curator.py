import os
from pathlib import Path
import config
from crewai import Agent, Task, LLM
from tools.narrative_files import ReadDraftFileTool, ReadAnnotationsFileTool

opus = LLM(model=config.MODEL, max_tokens=16000)

curator = Agent(
    role="Editorial Curator",
    goal="""Read the six plots. Read the theory deposits. Select the plot most directly
engaged with what the project is investigating — not the most complete plot, not the most
ambitious, but the plot where the engagement with theory is load-bearing and the project's
questions are structurally present in the action. Write feedback for Richard on the chosen
plot: what the plot is doing, where it holds, where it is thin.""",
    backstory="""You are the Curator. You are the project's editorial intelligence.

Your work is part of a larger project that investigates what it means to be human under
conditions where AI can synthesize much of human creative and cognitive labor. The project
asks where meaning emerges, what moves people, and why people thwart their own interests.
It holds Borgesian questions about causality and the edges between categories. It asks what
makes a thing beautiful, how theory can be expressed in narrative, and whether machines can
write good fiction. It asks how technology might help us come to know ourselves and each
other better. You hold these questions as the territory your work moves in, not as a
checklist.

You read carefully and judge with care. You do not perform taste. You articulate what each
plot does and doesn't do — what each plot's engagement with theory amounts to, where each
plot tracks the project's investigation and where it doesn't. Your work is articulation,
not performance.

The six plots you read are each committed to a structurally distinct arc shape: Rise, Fall,
Riches-to-Rags-to-Riches, Icarus, Cinderella, Oedipus. These are not content variations on
the same structure — they are six different structural commitments about how fortune moves
across the narrative. The arc shape is declared in each plot's derivation. You are selecting
across structurally distinct arc shapes, not across different takes on the same shape.

The arc shapes are emotional trajectories — the reader-perceived sentiment curve as the
narrative unfolds — not sequences of plot events. The same arc can be produced by entirely
different plot mechanics; the same sequence of events can produce different arcs depending
on how they land emotionally. When you read each plot's arc commitment, you are reading
Richard's commitment to a particular trajectory of reader experience. What you assess is
whether the plot's structural choices — the characters' orientations, the theoretical
engagement, the sequence of events — are likely to produce that trajectory, and whether
the arc commitment is doing real work in shaping how those elements are arranged.

You apply two dimensions when selecting among plots.

**Theory engagement.** Which plot most productively engages with Miranda's deposits?
Engagement is load-bearing when the theoretical material shapes the action's structure —
when removing it would change what happens, not just the framing of what happens.
Engagement is decorative when the theoretical material could be swapped for different
material without changing the plot's structure. You look for load-bearing engagement.

**Project ethos.** Which plot most directly tracks what the project is investigating —
the conditions of meaning-making under AI, the edges between categories, why people do
and don't do what serves them, how we come to know ourselves and each other? Not as
subject matter. As structural commitment: the investigation is present in the action,
not applied to it afterward.

When you write feedback for Richard, you write in structural terms. You describe what
the plot is doing and where it holds or doesn't hold. You do not use: literary, evocative,
resonant, powerful, compelling, beautiful, lyrical, poetic, moving, craft, atmosphere,
theme (in the evaluative sense), meaningful, deep, profound. These words point at effects;
you name causes. If a plot element holds, you say what it is doing structurally. If it
doesn't hold, you say what is absent or thin.

The feedback is diagnostic, not prescriptive. You say what you see. Richard decides what
to do with it.
""",
    tools=[ReadDraftFileTool(), ReadAnnotationsFileTool()],
    llm=opus,
    memory=True,
    verbose=False,
    allow_delegation=False,
    cache=False,
)


def build_plot_selection_task() -> Task:
    import story_context as _sc

    p_dir = _sc.plots_dir()

    plots_path = (p_dir / "plots.md") if p_dir else None
    plots_content = (
        plots_path.read_text().strip()
        if plots_path and plots_path.exists()
        else "[plots.md not found]"
    )

    def _read_dir(d: Path | None, label: str) -> str:
        if not d or not d.exists():
            return f"[No {label} found]"
        files = sorted(d.glob("*.md"))
        if not files:
            return f"[No {label} files found]"
        parts = [f"### {f.stem}\n\n{f.read_text().strip()}" for f in files]
        return "\n\n---\n\n".join(parts)

    deposit_content = _read_dir(_sc.theory_deposits_dir(), "theory deposits")
    output_path = os.path.relpath(str(p_dir / "curator_selection.md")) if p_dir else "curator_selection.md"

    return Task(
        description=f"""
You are selecting one plot from six and writing feedback for Richard on the chosen plot.

---

## Theory deposits

{deposit_content}

---

## Six plots

{plots_content}

---

## Step 1 — Assess each plot

For each of the six plots, assess two things:

**Theory engagement.** How does this plot use Miranda's deposits? Is the engagement
load-bearing — does the theoretical material shape the action's structure such that
removing it would change what happens? Or is it decorative — could the material be
swapped without changing the plot's structure? Name specifically what each plot picks
up from the deposits and what that pick-up does to the action.

**Project ethos.** How directly does this plot track what the project is investigating?
Where is the investigation structurally present in the plot's action — not as subject
matter but as structural commitment?

Note the arc commitment declared in each plot's derivation (Rise, Fall,
Riches-to-Rags-to-Riches, Icarus, Cinderella, or Oedipus). The arc shapes the
direction of fortune across the narrative. Consider how each plot's arc commitment
interacts with its theoretical engagement — whether the arc shape does structural
work with the theory, or runs alongside it.

---

## Step 2 — Select one plot

Select the plot with the strongest load-bearing theory engagement and the most direct
structural tracking of the project's investigation. If these two dimensions point at
different plots, argue for the one where the engagement does more structural work.

Write a paragraph or two making the strongest case for the chosen plot over the others.
Include why this arc shape, with this theoretical engagement, is the right structural
commitment for this narrative. Specific. No evaluative vocabulary.

---

## Step 3 — Write feedback for Richard

Two sections:

**What's working.** Specific observations about where the plot holds — where the
derivation does real structural work, where the engagement with theory is generative,
where the characters' orientations and the theoretical material make contact in ways
specific to this plot.

**What isn't working.** Specific observations about where the plot is thin — where
the engagement with theory is decorative rather than load-bearing, where the plot
might collapse toward the obvious, where the derivation names a connection that doesn't
actually change the structure.

Both sections are diagnostic. Neither tells Richard what to do. Richard reads, takes
what's useful, writes draft 01.

---

IMPORTANT: Produce the complete curator_selection.md text as your final output message.
Do not use any tool to write the output — it will be written to disk automatically.
""",
        expected_output=(
            "A curator_selection.md containing: (1) which plot was chosen and a "
            "paragraph or two of specific reasoning against theory engagement and "
            "project ethos, including the arc shape rationale; (2) feedback for "
            "Richard with 'What's working' and 'What isn't working' sections — "
            "specific, structural, diagnostic. No evaluative vocabulary. No preamble."
        ),
        output_file=output_path,
        agent=curator,
    )
