# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").
Hints are random 
New game does not initialize
Attempt count is wrong

**Bug Reproduction Log**

| Input | Expected Behavior | Actual Behavior | Console Output / Error |
|-------|-------------------|-----------------|------------------------|
| Enter guess '100` and click Submit | UI displays hint: "Go Lower " | UI displays a random hint  | *None* |
| Click the "New Game" button | Game state resets | UI remains frozen with previous game's state; no reset occurs | none |
*/

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?

I used Claude Code (in agent mode, inside VS Code) as my main coding assistant for this project.

- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).

**Correct suggestion:** The attempt counter was incrementing the instant Submit was pressed, before `parse_guess()` had even decided whether the text box held a real number. That meant a blank submit or a typo silently burned a turn, so players could hit "Out of attempts" after fewer real guesses than the sidebar promised. I asked the AI to fix the attempt-count bug, and it suggested extracting two small, named functions into `logic_utils.py` — `next_attempt_count(attempts, parse_ok)` (only increments when the input actually parsed) and `is_out_of_attempts(attempts, attempt_limit)` — and calling them from `app.py`'s submit handler instead of the old inline `attempts += 1` / `attempts >= attempt_limit`. I verified this was correct two ways: (1) I asked the AI to write pytest cases for it (`test_typos_do_not_end_the_game_early`, `test_player_gets_the_full_attempt_limit` in `tests/test_game_logic.py`), which pass; and (2) I ran the app, deliberately submitted a blank box and a typo ("4o") mixed in with real guesses, and confirmed "Attempts left" only dropped on the real guesses.

- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.

**Suggestion not accepted as written:** `check_guess()` has a `try/except TypeError` fallback branch that stringifies the guess and compares it against the secret with `>` when a direct numeric comparison fails. When I asked the AI to explain why this branch existed, it described it as a safe fallback for "when the secret isn't a number." I didn't accept that explanation as written, because when I tested it directly with `check_guess(9, "10")`, it returned `"Too High"` instead of the correct `"Too Low"` — string comparison is lexicographic, so `"9" > "10"` is `True` even though `9 < 10` numerically. So the "fallback" isn't actually safe; it just produces wrong hints silently instead of crashing. I verified this by calling the function directly in a Python shell with mismatched-length numbers and watching it give the wrong direction. The real fix (already applied elsewhere in `app.py`) was to stop ever passing a stringified secret into `check_guess()` in the first place, so this branch is never exercised in practice — but I kept the branch as-is rather than having the AI rewrite the comparison logic, since fixing the call site removed the only path that reached it and reworking dead-but-still-reachable fallback code felt out of scope for this pass.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?

For each bug in the reproduction log, I re-ran the exact steps that triggered it and confirmed the new behavior, then wrote or ran a pytest case that pins the fix so a future change can't silently reintroduce it. I only considered a bug "fixed" once both the manual repro and the automated test agreed.

- Describe at least one test you ran (manual or using pytest) and what it showed you about your code.

I ran `python -m pytest tests/ -v`, which reported 24 tests passing. Two examples: `test_guess_too_high`/`test_guess_too_low` in `tests/test_game_logic.py` confirmed `check_guess()` now returns the right outcome *and* the right hint wording (catching the backwards-hint bug), and `test_typos_do_not_end_the_game_early` simulated a Hard-difficulty game with blank and typo submissions mixed into real guesses, asserting the attempt counter only advanced on the real ones. Before the fix, this test would have failed because `next_attempt_count` didn't exist yet and attempts incremented unconditionally in `app.py`. I also manually ran `streamlit run app.py`, switched difficulty mid-game, and clicked New Game to confirm the session-state resets (score/status/history/secret), since those live in `app.py`'s Streamlit code and aren't covered by the logic_utils pytest suite.

- Did AI help you design or understand any tests? How?

Yes — I asked the AI to generate `tests/test_game_logic.py` targeting the specific bugs we'd just fixed (the attempt-count bug and the earlier hint/reset bugs), and it explained why the original three tests were failing (`check_guess()` returns a `(outcome, message)` tuple, not a bare string, so `assert result == "Win"` was comparing a tuple to a string and always failing) before rewriting them to unpack the tuple correctly. That explanation is what led me to catch and fix the broken assertions rather than just leaving three red tests in the suite.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
