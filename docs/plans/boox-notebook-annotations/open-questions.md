# boox-notebook-annotations: open questions after T-46 answers

Questions the plan (docs/plans/boox-notebook-annotations/plan.md) and the 18 answers leave undecided.
The implementation plan (docs/plans/boox-notebook-annotations/implementation.md) builds the Recommended
option of each unless answered otherwise.

## OQ1. Which conversation does the board's rendered text belong to?

Today the board has one notebook and Send goes to the "current" conversation; "New conversation" exists.
With text runs, line ids and ops bound to one conversation's spec, switching conversation is undefined.

- A. One notebook per conversation: switching or creating a conversation swaps the board to that
  conversation's notebook (a new conversation starts empty). (Recommended)
- B. One board notebook; starting a new conversation clears the board (old text readable in Documents).
- C. One board notebook; text from an older conversation stays but becomes read-only ink-like text and
  new ops on it are refused.

Blocks: P4 (Tasks 4.1, 4.7). P5a and P6 inherit it.

## OQ2. Revert to vN (Q15 B): what happens to handwriting consumed by the later versions?

Q6 hides transcribed ink with no toggle. Reverting removes text that versions after N added; the ink it
came from is hidden.

- A. Un-hide it: ink consumed by runs that the revert removes becomes visible ink again (re-sendable).
  (Recommended)
- B. Keep it hidden: the reverted text and its ink are gone from the board.
- C. Ask on each revert (dialog: "restore my handwriting too?").

Blocks: P4 (Task 4.4, 4.7).

## OQ3. With freehand recognition (Q12 C), what happens to margin ink that is not part of an insert?

Q12 C adds freehand loops and arrows to the tool shapes; it does not say whether other margin ink is
ignored (Q12 A) or forwarded (Q12 B).

- A. Forward it as ordinary ink; the translator applies it under the annotated-spec rule. (Recommended)
- B. Ignore it (not sent to the translator, stays on the board).
- C. Ignore it and show a small "not understood" mark next to it.

Blocks: P2 (Task 2.5 prompt text), P5a (Task 5.2).

## OQ4. Row shift (Q16 A) pushes text or ink past the last row of the page: where does it go?

- A. The overflowing rows move to a new page inserted right after this page. (Recommended)
- B. They cascade onto the next existing page, shifting its rows too (creating a page at the end only).
- C. Nothing moves past the foot: the last run is shown truncated with a marker (Q16 B behaviour on
  overflow only).

Blocks: P4 (Task 4.4).

## OQ5. Hand-off with images (Q10 B) when the spec references more than 8 images

The orchestrator takes at most 8 attachments per message; a spec may hold more region images.

- A. Attach the first 8 in document order and list the rest by name in the hand-off text. (Recommended)
- B. Split into several hand-off messages of at most 8 images each.
- C. Refuse the hand-off with an error naming the limit.

Blocks: P2 (Task 2.8).

## OQ6. Spec lines with no board origin (not from a segment, a kept line or an op)

For example text the translator adds from a typed feedback message, or a line split it made itself.

- A. Place it on a new row right after the run of the previous source line, shifting rows below.
  (Recommended)
- B. Do not show it on the board (visible in Documents only).
- C. Append it after the last run of the last page.

Blocks: P4 (Task 4.4).

## OQ7. Where does the user trigger "Revert to vN" (Q15 B)?

- A. In the Documents version picker: "Revert to this version" on an older version, with a confirm
  dialog; the board re-renders. (Recommended)
- B. In the board's page popup: "Revert to version..." with a version list.
- C. Both.

Blocks: P4 (Task 4.7).
