# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

### What the game is

**The Impossible Guesser** is a Streamlit number-guessing game. The app picks a
secret number inside a range set by the difficulty in the sidebar (Easy = 1–20
with 6 attempts, Normal = 1–100 with 8 attempts, Hard = 1–50 with 5 attempts).
You type a guess, press **Submit Guess**, and the game answers with a
higher/lower hint, updates your score, and counts the attempt. You win by
naming the secret before the attempts run out. A "Developer Debug Info"
expander shows the secret, attempts, score, difficulty, and guess history so
the behavior can be checked while playing.

### Bugs found

| # | Bug | How it showed up |
|---|-----|------------------|
| 1 | **The secret number reset on every submit.** `random.randint()` ran on every script rerun instead of once per game, so the answer changed each time Submit was clicked. | The game was unwinnable; the debug panel showed a different secret after every click. |
| 2 | **The hints were backwards.** `check_guess()` returned "Go HIGHER" for a guess above the secret and vice versa. | Following the hints walked you away from the answer. |
| 3 | **The secret was stringified on every other attempt.** `app.py` passed `str(secret)` when `attempts % 2 == 0`, which dropped `check_guess()` into its lexicographic string-comparison fallback. | Hints looked random rather than merely reversed — e.g. guessing 9 against `"10"` reports "Too High", because `"9" > "10"` is true for strings. |
| 4 | **Attempts started at 1.** The counter was initialized to `1` instead of `0`. | "Attempts left" was one short of what the sidebar promised. |
| 5 | **Bad input burned a turn.** The counter incremented the instant Submit was pressed, before `parse_guess()` decided whether the box held a number. | A blank submit or a typo like `4o` cost a real attempt and could end the game early. |
| 6 | **"New Game" did not fully reset.** It reset only the secret and attempts. | Score, win/lose status, and guess history carried over from the previous round. |
| 7 | **Changing difficulty mid-game left stale state.** The old secret, score, and history survived the switch. | The sidebar advertised the new range and attempt limit while the secret was still drawn from the old one. |
| 8 | **The prompt hardcoded "between 1 and 100".** The status message ignored the selected difficulty. | Easy and Hard players were told the wrong range. |

### Fixes applied

- **Persisted game state.** Every mutable value (`secret`, `attempts`, `score`,
  `status`, `history`) is seeded into `st.session_state` behind an
  `if "key" not in st.session_state` guard, so a rerun reads the existing game
  instead of starting a new one (bug 1).
- **Corrected the hint direction** in `check_guess()`, so a guess above the
  secret returns `("Too High", "Go LOWER!")` and a guess below returns
  `("Too Low", "Go HIGHER!")` (bug 2).
- **Stopped stringifying the secret.** `app.py` always passes the raw `int`
  secret to `check_guess()`, so the string-comparison fallback is never
  reached in practice (bug 3).
- **Refactored the logic out of `app.py` into `logic_utils.py`** —
  `get_range_for_difficulty()`, `parse_guess()`, `check_guess()`,
  `next_attempt_count()`, `is_out_of_attempts()`, and `update_score()` are now
  pure functions with no Streamlit dependency, which is what makes them
  testable.
- **Made an attempt cost a turn only on a real guess.**
  `next_attempt_count(attempts, parse_ok)` increments only when the input
  parsed, and `is_out_of_attempts(attempts, attempt_limit)` owns the
  end-of-game check in one place. The counter also starts at `0`
  (bugs 4 and 5).
- **Made the resets complete.** "New Game" and a mid-game difficulty change
  both clear all five state fields and draw a fresh secret from the current
  range (bugs 6 and 7).
- **Interpolated the live range** into the status message so it matches the
  selected difficulty (bug 8).

## 📸 Demo Walkthrough

A full Normal game (range 1–100, 8 attempts). The secret for this run was
**57**, read from the Developer Debug Info expander.

1. **Start the app** with `python -m streamlit run app.py`. The status box
   reads *"Guess a number between 1 and 100. Attempts left: 8"* — the range
   and the attempt count both match the Normal difficulty in the sidebar.
2. **User enters a guess of 40.** The game returns **"Too Low → Go HIGHER!"**,
   which is the correct direction. Attempts left drops to 7 and the score
   moves to **−5** (a wrong guess costs 5 points).
3. **User enters a guess of 70 → "Too High → Go LOWER!"**. Attempts left drops
   to 6 and the score updates to **0**. The secret in the debug panel is still
   57 — it did not change between submissions, which is the state bug staying
   fixed.
4. **User submits an empty box** (or a typo such as `4o`). The game shows
   *"Enter a guess."* and **nothing else moves**: attempts left stays at 6 and
   the score stays at 0, because unreadable input is not a guess.
5. **User enters a guess of 55 → "Too Low → Go HIGHER!"**. Attempts left 5,
   score **−5**. The hints have now bracketed the answer between 55 and 70.
6. **Score updates correctly after each guess** — it moves only on real
   guesses, and each step above matches what `update_score()` returns for that
   outcome and attempt number.
7. **User enters a guess of 57 → "🎉 Correct!"**, balloons, and *"You won! The
   secret was 57. Final score: 45"* — a 4th-attempt win adds 50 points to the
   running score.
8. **The game ends after the correct guess.** The board locks with *"You
   already won. Start a new game to play again."* until New Game is pressed.
9. **User clicks "New Game"** and every field resets together: a fresh secret
   in 1–100, attempts back to 8, score back to 0, and an empty history — not
   just a new number with the old score still on screen.

**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🧪 Test Results

Challenge 1 — Advanced Edge-Case Testing. Command: `python -m pytest tests/ -v`

```
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\black\AppData\Local\Programs\Python\Python310\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\black\OneDrive\Desktop\Class Projects\ai110-module1show-gameglitchinvestigator-starter
plugins: anyio-4.14.2
collecting ... collected 24 items

tests/test_game_logic.py::test_unreadable_input_does_not_consume_an_attempt[] PASSED [  4%]
tests/test_game_logic.py::test_unreadable_input_does_not_consume_an_attempt[abc] PASSED [  8%]
tests/test_game_logic.py::test_unreadable_input_does_not_consume_an_attempt[4o] PASSED [ 12%]
tests/test_game_logic.py::test_unreadable_input_does_not_consume_an_attempt[   ] PASSED [ 16%]
tests/test_game_logic.py::test_unreadable_input_does_not_consume_an_attempt[None] PASSED [ 20%]
tests/test_game_logic.py::test_valid_guess_consumes_exactly_one_attempt PASSED [ 25%]
tests/test_game_logic.py::test_game_is_not_over_while_an_attempt_remains PASSED [ 29%]
tests/test_game_logic.py::test_game_is_over_once_the_limit_is_reached PASSED [ 33%]
tests/test_game_logic.py::test_typos_do_not_end_the_game_early PASSED    [ 37%]
tests/test_game_logic.py::test_player_gets_the_full_attempt_limit PASSED [ 41%]
tests/test_game_logic.py::test_get_range_for_difficulty[Easy-expected0] PASSED [ 45%]
tests/test_game_logic.py::test_get_range_for_difficulty[Normal-expected1] PASSED [ 50%]
tests/test_game_logic.py::test_get_range_for_difficulty[Hard-expected2] PASSED [ 54%]
tests/test_game_logic.py::test_get_range_for_difficulty[Nonsense-expected3] PASSED [ 58%]
tests/test_game_logic.py::test_parse_guess_truncates_a_decimal PASSED    [ 62%]
tests/test_game_logic.py::test_parse_guess_reports_a_blank_box_and_a_non_number_differently PASSED [ 66%]
tests/test_game_logic.py::test_winning_guess PASSED                      [ 70%]
tests/test_game_logic.py::test_guess_too_high PASSED                     [ 75%]
tests/test_game_logic.py::test_guess_too_low PASSED                      [ 79%]
tests/test_game_logic.py::test_check_guess_returns_a_hint_message_with_the_outcome PASSED [ 83%]
tests/test_game_logic.py::test_update_score_rewards_an_early_win PASSED  [ 87%]
tests/test_game_logic.py::test_update_score_floors_a_late_win_at_ten_points PASSED [ 91%]
tests/test_game_logic.py::test_update_score_penalises_a_wrong_guess PASSED [ 95%]
tests/test_game_logic.py::test_update_score_leaves_an_unknown_outcome_alone PASSED [100%]

============================= 24 passed in 0.09s ==============================
```

Edge cases covered beyond the three starter tests: empty input, non-numeric
input (`abc`), a near-miss typo (`4o`), whitespace-only input, `None`, a
decimal that truncates (`7.9` → `7`), the exact boundary between "one attempt
left" and "out of attempts", an unknown difficulty falling back to the Normal
range, and the 10-point score floor on a very late win.

## 🚀 Stretch Features

- [ ] [If you choose to complete Challenge 4, describe the Enhanced UI changes here — a screenshot is optional]
