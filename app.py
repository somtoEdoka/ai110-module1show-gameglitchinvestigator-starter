import random
import streamlit as st

# FIX: Moved all pure game logic into logic_utils.py (AI proposed the split
# in agent mode, I reviewed the diff and kept the call sites here unchanged).
from logic_utils import (
    get_range_for_difficulty,
    parse_guess,
    check_guess,
    update_score,
    next_attempt_count,
    is_out_of_attempts,
)

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

# FIX: Attempts used to start at 1, so players were given one fewer real
# guess than the sidebar promised. AI suggested starting the counter at 0;
# I verified by checking "Attempts left" matched attempt_limit on a fresh game.
if "attempts" not in st.session_state:
    st.session_state.attempts = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

if "difficulty" not in st.session_state:
    st.session_state.difficulty = difficulty

# FIX: Switching difficulty mid-game left the old secret/score/history in
# place while the sidebar showed the new range and attempt limit. AI proposed
# detecting the difficulty change and resetting state the same way New Game
# does; verified by starting on Normal, switching to Easy, and confirming a
# fresh secret in the new range plus a cleared score/history.
# Changing difficulty changes the range and the attempt limit, so the game in
# progress no longer makes sense against them. Start a fresh one.
if st.session_state.difficulty != difficulty:
    st.session_state.difficulty = difficulty
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []

st.subheader("Make a guess")

# Filled in at the end of the run so it reflects this run's guess instead of
# the count from before it.
status_box = st.empty()
debug_box = st.container()


def render_status():
    # FIX: This message used to hardcode "between 1 and 100" regardless of
    # difficulty, so Easy/Hard players were told the wrong range. AI
    # suggested interpolating the low/high computed above; verified by
    # switching to Easy and confirming the message says "1 and 20".
    status_box.info(
        f"Guess a number between {low} and {high}. "
        f"Attempts left: {attempt_limit - st.session_state.attempts}"
    )
    with debug_box:
        with st.expander("Developer Debug Info"):
            st.write("Secret:", st.session_state.secret)
            st.write("Attempts:", st.session_state.attempts)
            st.write("Score:", st.session_state.score)
            st.write("Difficulty:", difficulty)
            st.write("History:", st.session_state.history)

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

# FIX: "New Game" only used to reset attempts/secret, leaving the old score,
# status, and history on screen. AI suggested resetting all five fields
# together; I verified by winning a round, clicking New Game, and confirming
# score/history/status all went back to their starting values.
if new_game:
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    render_status()
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    ok, guess_int, err = parse_guess(raw_guess)

    # FIX: The attempt counter used to increment before checking whether the
    # input even parsed, so a blank submit or typo burned a real turn and the
    # game could end early. AI suggested extracting next_attempt_count() so
    # only a successful parse counts; verified with the pytest cases in
    # tests/test_game_logic.py (test_typos_do_not_end_the_game_early, etc.)
    # and by typing junk into the box in the running app and watching
    # "Attempts left" stay put.
    st.session_state.attempts = next_attempt_count(st.session_state.attempts, ok)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(err)
    else:
        st.session_state.history.append(guess_int)

        # FIX: This used to stringify the secret on every other attempt
        # (attempts % 2 == 0), which pushed check_guess() into its
        # string-comparison fallback and produced hints that looked random.
        # AI suggested always passing the raw int secret; verified by
        # submitting guesses on 10+ consecutive attempts and confirming the
        # hint direction was consistent every time.
        outcome, message = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            # FIX: Extracted the off-by-one-prone `attempts >= attempt_limit`
            # check into is_out_of_attempts() alongside next_attempt_count()
            # so the "out of turns" rule lives in one tested place; verified
            # via test_game_is_over_once_the_limit_is_reached in
            # tests/test_game_logic.py.
            if is_out_of_attempts(st.session_state.attempts, attempt_limit):
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

render_status()

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
