"""Iteration 6c: book bet ramps against Kelly.

The ramps size the bet from the rounded true count alone, with no
measured edge and no variance anywhere in the maths. The tests check
the sizing exactly at every step boundary, the table limits, the
bankroll floor, and that the sizing ignores the Kelly machinery
entirely. A small smoke test proves the simulator runs a RampPolicy
and reproduces itself exactly on a fixed seed.
"""

import pytest

from blackjack.ramp import RampPolicy
from blackjack.rules import Rules
from blackjack.simulator import SessionConfig, run_sessions
from blackjack.basic_strategy import BasicStrategy
from run_ramp_comparison import summarize_distribution


# ---- Ramp A: one unit per +1 TC ------------------------------------------


def test_ramp_a_units_at_the_boundaries():
    rules = Rules(num_decks=6)
    policy = RampPolicy(rules, "A")
    assert policy.bet(10000, -5.0) == 10  # negative count: the minimum
    assert policy.bet(10000, -0.1) == 10
    assert policy.bet(10000, 0.0) == 10
    assert policy.bet(10000, 0.9) == 10  # floor(0.9) is 0, so 1 unit
    assert policy.bet(10000, 1.0) == 10  # 1 unit, not 2: the count is 1
    assert policy.bet(10000, 1.9) == 10  # floor(1.9) is 1
    assert policy.bet(10000, 2.0) == 20
    assert policy.bet(10000, 2.9) == 20
    assert policy.bet(10000, 3.0) == 30
    assert policy.bet(10000, 10.0) == 100


def test_ramp_a_units_method():
    policy = RampPolicy(Rules(num_decks=6), "A")
    assert policy.units(-2.0) == 1
    assert policy.units(0.5) == 1
    assert policy.units(4.7) == 4


# ---- Ramp B: the 1-2-4-8 spread ------------------------------------------


def test_ramp_b_units_at_the_boundaries():
    rules = Rules(num_decks=6)
    policy = RampPolicy(rules, "B")
    assert policy.bet(10000, -5.0) == 10  # negative count: the minimum
    assert policy.bet(10000, -0.1) == 10
    assert policy.bet(10000, 0.0) == 10
    assert policy.bet(10000, 0.9) == 10  # below 1: 1 unit
    assert policy.bet(10000, 1.0) == 20  # from 1: 2 units
    assert policy.bet(10000, 1.9) == 20
    assert policy.bet(10000, 2.0) == 40  # from 2: 4 units
    assert policy.bet(10000, 2.9) == 40
    assert policy.bet(10000, 3.0) == 80  # from 3: 8 units
    assert policy.bet(10000, 10.0) == 80  # capped at 8 units, not more


def test_ramp_b_units_method():
    policy = RampPolicy(Rules(num_decks=6), "B")
    assert policy.units(0.99) == 1
    assert policy.units(1.0) == 2
    assert policy.units(2.99) == 4
    assert policy.units(3.0) == 8
    assert policy.units(99.0) == 8


def test_ramp_b_jumps_faster_than_ramp_a():
    # At a true count of 3 the spread bets 8 units where one unit per
    # count bets 3, and at a count of 1 it bets 2 where the other bets
    # 1. The spread is the aggressive ramp at every count above 1.
    rules = Rules(num_decks=6)
    a = RampPolicy(rules, "A")
    b = RampPolicy(rules, "B")
    assert b.bet(10000, 1.0) > a.bet(10000, 1.0)
    assert b.bet(10000, 2.0) > a.bet(10000, 2.0)
    assert b.bet(10000, 3.0) > a.bet(10000, 3.0)
    assert b.bet(10000, 0.5) == a.bet(10000, 0.5)  # both the minimum


# ---- limits ---------------------------------------------------------------


def test_ramp_bet_respects_the_table_limits():
    # A huge count on a table with a $50 maximum bets $50, not the
    # $100 the ramp would size, and the minimum still holds at a
    # negative count.
    rules = Rules(num_decks=6, max_bet=50)
    a = RampPolicy(rules, "A")
    b = RampPolicy(rules, "B")
    assert a.bet(1_000_000, 10.0) == 50  # 10 units would be $100
    assert b.bet(1_000_000, 3.0) == 50  # 8 units would be $80
    assert a.bet(1_000_000, -2.0) == rules.min_bet
    assert b.bet(1_000_000, -2.0) == rules.min_bet


def test_ramp_bet_never_exceeds_the_bankroll():
    # A $25 bankroll facing a $100 ramp bet bets $25, and a bankroll
    # under the minimum bets nothing at all.
    rules = Rules(num_decks=6)
    a = RampPolicy(rules, "A")
    b = RampPolicy(rules, "B")
    assert a.bet(25, 10.0) == 25
    assert b.bet(25, 3.0) == 25
    assert a.bet(5, 10.0) == 0
    assert b.bet(5, 10.0) == 0


def test_ramp_policy_ignores_the_kelly_fraction():
    # The ramp takes no edge curve and no variance, so the Kelly
    # fraction must not move it: the same count bets the same amount
    # under half Kelly rules and full Kelly rules.
    half = RampPolicy(Rules(num_decks=6, kelly_fraction=0.5), "A")
    full = RampPolicy(Rules(num_decks=6, kelly_fraction=1.0), "A")
    for tc in (-2.0, 0.0, 1.5, 3.0, 8.0):
        assert half.bet(10000, tc) == full.bet(10000, tc)


def test_ramp_policy_rejects_an_unknown_ramp():
    with pytest.raises(ValueError):
        RampPolicy(Rules(num_decks=6), "C")


# ---- the simulator with a ramp --------------------------------------------


def test_simulator_runs_a_ramp_policy_and_reproduces_itself():
    # A few short sessions with Ramp A: the run finishes, the bankroll
    # moves, and the same seed gives the same bankroll path back.
    # Both policies run the same seeds, so the comparison is paired:
    # they face the same cards, and only the bet sizing differs.
    rules = Rules(num_decks=6, starting_balance=10000)
    strategy = BasicStrategy(rules)
    session = SessionConfig(rounds=100)
    a = run_sessions(rules, strategy, RampPolicy(rules, "A"), session, 3, seed=42)
    b = run_sessions(rules, strategy, RampPolicy(rules, "A"), session, 3, seed=42)
    assert a["n"] == 3
    assert a["mean_ending_bankroll"] == b["mean_ending_bankroll"]
    assert a["mean_growth"] == b["mean_growth"]
    assert a["mean_max_drawdown"] == b["mean_max_drawdown"]
    assert a["risk_of_ruin"] == b["risk_of_ruin"]
    for first, second in zip(a["results"], b["results"]):
        assert first.bankroll_history == second.bankroll_history
        assert first.ending_bankroll == second.ending_bankroll
    c = run_sessions(rules, strategy, RampPolicy(rules, "B"), session, 3, seed=42)
    assert all(r.rounds_played == 100 for r in c["results"])
    assert 0.0 <= c["risk_of_ruin"] <= 1.0
    assert -1.0 < c["mean_growth"] < 1.0


# ---- the distribution summary ---------------------------------------------


def test_distribution_summary_adds_up_and_reproduces():
    # A few short sessions with Ramp B, summarised: the winners, the
    # losers and the pushes add up to the session count, the worst
    # session is at or below the mean and the best at or above it, the
    # average win is not negative and the average loss is not
    # positive, and the same seed gives the same summary back.
    rules = Rules(num_decks=6, starting_balance=10000)
    strategy = BasicStrategy(rules)
    session = SessionConfig(rounds=100)
    first = run_sessions(rules, strategy, RampPolicy(rules, "B"), session, 3, seed=42)
    second = run_sessions(rules, strategy, RampPolicy(rules, "B"), session, 3, seed=42)
    a = summarize_distribution(first)
    b = summarize_distribution(second)
    assert a == b
    assert a["n"] == 3
    assert a["winners"] + a["losers"] + a["pushes"] == 3
    assert a["worst_ending"] <= a["mean_ending"] <= a["best_ending"]
    assert a["worst_growth"] <= first["mean_growth"] <= a["best_growth"]
    assert a["avg_win_growth"] >= 0.0
    assert a["avg_loss_growth"] <= 0.0
    assert a["growth_sd"] >= 0.0
    assert a["worst_drawdown"] >= first["mean_max_drawdown"]
