# The Emotional Arcs of Stories Are Dominated by Six Basic Shapes
## Reagan et al. (2016) — Curated extract

**Source:** Andrew J. Reagan, Lewis Mitchell, Dilan Kiley, Christopher M. Danforth,
Peter Sheridan Dodds. "The emotional arcs of stories are dominated by six basic shapes."
*EPJ Data Science* 5:31 (2016). DOI 10.1140/epjds/s13688-016-0093-1. Open Access (CC BY 4.0).

---

## What an emotional arc is — and what it isn't

The emotional arc of a story is the trajectory of reader-perceived sentiment as the
text unfolds. It is measured through the words used, not derived from the plot:

> "While the plot captures the mechanics of a narrative and the structure encodes
> their delivery, in the present work we examine the emotional arc that is invoked
> through the words used. The emotional arc of a story does not give us direct
> information about the plot or the intended meaning of the story, but rather exists
> as part of the whole narrative (e.g., an emotional arc showing a fall in sentiment
> throughout a story may arise from very different plot and structure combinations).
> This distinction between the emotional arc and the plot of a story is one point
> of misunderstanding in other work that has drawn criticism from the digital
> humanities community."

The corollary: the same arc shape can be produced by very different plot mechanics.
An Icarus arc does not require a particular sequence of events — it requires that the
reader's emotional experience follows that shape. Two stories with identical arc shapes
can have entirely different plots.

---

## The six emotional arcs

Using three independent methods on 1,327 Project Gutenberg fiction texts, Reagan et al.
identify six core emotional arcs:

**Rags to Riches (rise)**
Steady upward movement. Sentiment increases throughout the narrative.

**Tragedy / Riches to Rags (fall)**
Steady downward movement. Sentiment decreases throughout.

**Man in a Hole (fall-rise)**
A drop followed by a recovery. Something goes wrong; it gets resolved. The most
commonly occurring shape in the corpus. The paper notes multiple cluster variants
at different levels of variance — the shape is robust across different magnitudes
of fall and recovery.

**Icarus (rise-fall)**
An ascent followed by a descent.

**Cinderella (rise-fall-rise)**
Two phases of gain bracketing a loss.

**Oedipus (fall-rise-fall)**
A descent, partial recovery, and final descent.

---

## Download success: which arcs perform

Reagan et al. examine Project Gutenberg download counts as a proxy for success:

> "We find 'Icarus', 'Oedipus', and two sequential 'Man in a Hole' arcs are the
> three most successful emotional arcs."

The Rags to Riches and Tragedy arcs — which account for the largest share of the
corpus — have lower median downloads than Icarus, Oedipus, and Man in a Hole.
The compound form of Man in a Hole (two sequential fall-rise movements) is among
the highest-performing.

**The paper's own caveat:** "Of course, downloads are only a rough proxy for success,
and this work may provide an outline for more detailed analysis of the factors that
impact meaningful measures of success, i.e., sales or cultural influence."

---

## The Vonnegut frame

The paper's organizing intuition comes from Kurt Vonnegut's rejected master's thesis,
which he considered his greatest contribution. Vonnegut mapped stories on
"Beginning-End" and "Ill Fortune-Great Fortune" axes. In a recorded lecture:

> "There is no reason why the simple shapes of stories can't be fed into computers,
> they are beautiful shapes."

Reagan et al. apply computational sentiment analysis to test whether Vonnegut's shapes
hold across a large corpus. They do.

---

## Operational notes (project interpretation)

The following is not from the paper. It is the project's working interpretation of
how each arc tends to fail and what makes it structurally complete. Used by agents
as operational guidance, not as claims from Reagan et al.

**Rags to Riches (rise)**
Danger: it becomes a proof of concept rather than a narrative. Arrest arrives when
the accumulation becomes irreversible — when what's been gained can't be ungained,
even if it costs something.

**Tragedy / Riches to Rags (fall)**
Danger: the losses become merely accumulative — a list, not a shape. Arrest arrives
at the point of no return, not at the bottom.

**Man in a Hole (fall-rise)**
Danger: the rise returns to the starting condition rather than to something that
couldn't have existed without the hole. The rise must be contaminated by the fall
or it's a reset, not an arc.

**Icarus (rise-fall)**
Danger: the fall feels punitive rather than structural — the narrative wants to teach
a lesson rather than show a consequence. Arrest arrives when the fall has become
irreversible, not when the lesson lands.

**Cinderella (rise-fall-rise)**
Danger: the second rise undoes the second fall too neatly. Arrest arrives in the
second rise if and only if the protagonist is different from who they were at the
start of it.

**Oedipus (fall-rise-fall)**
Danger: the revelation is too legible — the audience can see it coming. Arrest arrives
at the moment of recognition, not at the consequence of it.

---

A narrative that resists these shapes is doing something structural. Note what shape
it refuses and what it proposes instead. Refusal without a counter-proposal is wandering.
