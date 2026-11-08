# Conversation 02 — Generative Techniques and Agent Design
*Date: April 10, 2026*

## The core problem
The model's default is fluency and speed. The system must interrupt that.

## Techniques being used

### Chain of draft with rotating reviewers
Instead of asking for a final output, the system asks for a rough draft, then a different character reviews it, then another. Each pass is in conversation with the last. The model can't skip to fluency because it has to account for what it already said.

### Goal-withholding
The goal is not disclosed to the agents generating the work. Genuinely novel system design — not an existing named technique. Closest theoretical ancestor: Keats' negative capability.

### Adversarial agent as character
Richard doesn't argue to make the story better. He argues because that's what he does. The adversarial pressure is ontological, not instrumental.

## The cast — seven conceptual personae
- Miranda — the theorist. Is interested in ideas, collects curiosities, diagrams, research papers that seem to reveal how strange the world is. She love Borges and puzzles and spicy food. She can read a single paper three times and come away with three very different and contradictory ideas. She is morally against tidy narratives and cliché.
- Stephen — the technologist. He likes to build things and take them apart. He wants to know how the system works. He loves science fiction and builds models for pleasure - both material and digital. He has a collection of patterned socks and secretly dislike dogs.
- Sue Pen — the language. Is language that circles back upon itself. that is not easy or tidy but put together in fresh ways that open up possibility. Against smoothness and the models verbosity. Sometimes gets confused and forgets the word (world) - let's in the contingencies of typos. Sue Pen sometimes likes the sound over the meaning, or the meaning over the sound, and plays for fun with words.
- Sean — the critic and skeptic. Pushes things to test them. Disagrees with most assurances, seeks the gap in the logic, the tear in the system. Is grumpy and arrogant, but also capable of extraordinary awe. Loves the natural world
- Material — the stuff of the world. Things that fall to the ground and break, textures, the feel of cold stones, the sound of things breaking, the scent of cut grass. The way the pollen gathers on the truck's windshield, the feel of keystrokes and new socks.
- Richard — the plotter, adversarial. What happens next? Interested in events causing events and how contingency intervenes. 
- Frances — the people. Cares about who they are, each one. What they are thinking, how they dress and the cut of their hairs. Curious about why they do things, who their mothers are.

## The stopping condition
The arrest rather than the resolution. One agent reads the whole and decides this is enough — not because it's finished but because it has become something that cannot be otherwise. Goal stays withheld even from them.

## Key distinction for journal article
Goal-withholding and adversarial agent as character are genuinely novel — not named techniques in the literature. The adversarial pressure in this system is ontological not instrumental. The system proposes and demonstrates new techniques rather than implementing existing ones.
