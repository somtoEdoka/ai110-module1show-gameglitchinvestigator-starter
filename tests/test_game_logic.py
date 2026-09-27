import pytest

from logic_utils import (
    check_guess,
    get_range_for_difficulty,
    is_out_of_attempts,
    next_attempt_count,
    parse_guess,
    update_score,
)


# ---------------------------------------------------------------------------
# The bug: the game declared a loss while the player still had a turn left.
#
# app.py incremented the attempt counter the moment Submit was pressed, before
# parse_guess() had decided whether the input was even a number. A blank box or
# a typo therefore burned a turn, so the player hit the attempt limit after
# fewer real guesses than the limit allowed. The two helpers below are the rule
# app.py now calls, so these tests cover the code the app actually runs.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_input", ["", "abc", "4o", "   ", None])
def test_unreadable_input_does_not_consume_an_attempt(bad_input):
    ok, _guess, err = parse_guess(bad_input)

    assert ok is False
    assert err  # the player is told what went wrong...
    assert next_attempt_count(3, ok) == 3  # ...but does not pay a turn for it


def test_valid_guess_consumes_exactly_one_attempt():
    ok, guess, err = parse_guess("42")

    assert (ok, guess, err) == (True, 42, None)
    assert next_attempt_count(3, ok) == 4


def test_game_is_not_over_while_an_attempt_remains():
    # 7 of 8 attempts used: the 8th guess is still owed to the player.
    assert is_out_of_attempts(7, 8) is False


def test_game_is_over_once_the_limit_is_reached():
    assert is_out_of_attempts(8, 8) is True


def test_typos_do_not_end_the_game_early():
    """The exact regression: junk input between guesses must not cost turns.

    Mirrors app.py's submit handler for a Hard game (5 attempts). The player
    makes four wrong guesses with a blank submit and a typo mixed in; before
    the fix those two submits pushed the counter to 6 and ended the game.
    """
    attempt_limit = 5
    secret = 33
    attempts = 0
    submissions = ["10", "", "20", "4o", "30", "40"]

    for raw in submissions:
        ok, guess, _err = parse_guess(raw)
        attempts = next_attempt_count(attempts, ok)
        if ok and check_guess(guess, secret)[0] == "Win":
            pytest.fail("test data should contain no winning guess")

    assert attempts == 4, "only the four real guesses should have been counted"
    assert is_out_of_attempts(attempts, attempt_limit) is False


def test_player_gets_the_full_attempt_limit():
    attempt_limit = 5
    attempts = 0

    for _ in range(attempt_limit):
        assert is_out_of_attempts(attempts, attempt_limit) is False
        ok, _guess, _err = parse_guess("7")
        attempts = next_attempt_count(attempts, ok)

    assert is_out_of_attempts(attempts, attempt_limit) is True


# ---------------------------------------------------------------------------
# Coverage for the functions refactored out of app.py into logic_utils.py.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "difficulty,expected",
    [
        ("Easy", (1, 20)),
        ("Normal", (1, 100)),
        ("Hard", (1, 50)),
        ("Nonsense", (1, 100)),  # falls back to the Normal range
    ],
)
def test_get_range_for_difficulty(difficulty, expected):
    assert get_range_for_difficulty(difficulty) == expected


def test_parse_guess_truncates_a_decimal():
    assert parse_guess("7.9") == (True, 7, None)


def test_parse_guess_reports_a_blank_box_and_a_non_number_differently():
    assert parse_guess("")[2] == "Enter a guess."
    assert parse_guess("abc")[2] == "That is not a number."


def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    outcome, _message = check_guess(50, 50)
    assert outcome == "Win"


def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    outcome, _message = check_guess(60, 50)
    assert outcome == "Too High"


def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    outcome, _message = check_guess(40, 50)
    assert outcome == "Too Low"


def test_check_guess_returns_a_hint_message_with_the_outcome():
    _outcome, message = check_guess(60, 50)
    assert "LOWER" in message


def test_update_score_rewards_an_early_win():
    assert update_score(current_score=0, outcome="Win", attempt_number=1) == 80


def test_update_score_floors_a_late_win_at_ten_points():
    assert update_score(current_score=0, outcome="Win", attempt_number=9) == 10


def test_update_score_penalises_a_wrong_guess():
    assert update_score(current_score=20, outcome="Too Low", attempt_number=1) == 15


def test_update_score_leaves_an_unknown_outcome_alone():
    assert update_score(current_score=20, outcome="???", attempt_number=1) == 20
