def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess, secret):
    """
    Compare guess to secret and return (outcome, message).

    outcome examples: "Win", "Too High", "Too Low"
    """
    # FIX: The hint text used to be swapped (a guess above the secret said
    # "Go HIGHER"). AI suggested swapping the two message strings; I verified
    # by unit test (tests/test_game_logic.py::test_guess_too_high) and by
    # guessing above/below the secret in the running app.
    if guess == secret:
        return "Win", "🎉 Correct!"

    try:
        if guess > secret:
            return "Too High", "📉 Go LOWER!"
        else:
            return "Too Low", "📈 Go HIGHER!"
    except TypeError:
        g = str(guess)
        if g == secret:
            return "Win", "🎉 Correct!"
        if g > secret:
            return "Too High", "📉 Go LOWER!"
        return "Too Low", "📈 Go HIGHER!"


# FIX: Extracted from app.py's submit handler, which incremented attempts
# unconditionally and compared with a bare `>=` inline. AI proposed pulling
# both rules into named, testable functions so the "an attempt is only spent
# on a real guess" rule can't drift out of sync between call sites; verified
# with tests/test_game_logic.py (test_typos_do_not_end_the_game_early,
# test_game_is_over_once_the_limit_is_reached).
def next_attempt_count(attempts: int, parse_ok: bool) -> int:
    """
    Attempts used after a submission.

    An attempt is spent only when the input parsed into a real guess. A blank
    box or a typo is not a guess, so it must not cost the player a turn.
    """
    if parse_ok:
        return attempts + 1
    return attempts


def is_out_of_attempts(attempts: int, attempt_limit: int) -> bool:
    """
    True once every allowed attempt has been used.

    The player keeps playing while attempts < attempt_limit, so the guess that
    brings the count up to the limit is still a legal guess.
    """
    return attempts >= attempt_limit


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score
