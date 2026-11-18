"""Run the batch simulator: book bet ramps against Kelly, and print the numbers.

Usage, from the iteration_6c folder:
    python run_ramp_comparison.py [--bankroll 10000] [--rounds 2000]
        [--sessions 50] [--seed 20261111] [--curve curve.json]

Runs the same seeded sessions four times, once per policy, on identical
shoes: half Kelly, full Kelly, Ramp A (one unit per +1 TC) and Ramp B
(the 1-2-4-8 spread). Each run prints the risk of ruin, the mean growth,
the mean max drawdown and the mean ending bankroll. The edge curve comes
from the 6a measurement (blackjack/edge_curve.py, MEASURED_EDGE_CURVE)
unless --curve gives a JSON file of [true-count centre, edge, variance]
points instead. The ramps never read the curve: they size purely off
the rounded true count, which is the point of the comparison.

A session is 2000 rounds by default, which is a long sitting at a
table. 50 sessions is enough for the risk of ruin to settle to a few
percent. The run takes about two minutes.
"""

from __future__ import annotations

import argparse
import json
import statistics

from blackjack.basic_strategy import BasicStrategy
from blackjack.edge_curve import MEASURED_EDGE_CURVE
from blackjack.kelly import KellyPolicy
from blackjack.ramp import RampPolicy
from blackjack.rules import Rules
from blackjack.simulator import SessionConfig, run_sessions


def summarize_distribution(out: dict[str, object]) -> dict[str, object]:
    """Worst and best session, average win and average loss, and the spread.

    out is one run_sessions result: a dict with a "results" list of
    SessionResult. A win is a session that ends above the starting
    bankroll, a loss one that ends below it. The average win and the
    average loss are mean growth over just those sessions, so they
    show where the mean growth comes from: bigger wins, smaller
    losses, or more wins. The growth spread is the population
    standard deviation of the per-session growth figures.
    """
    results = out["results"]
    starts = [r.starting_bankroll for r in results]
    ends = [r.ending_bankroll for r in results]
    growths = [r.growth for r in results]
    wins = [r for r in results if r.ending_bankroll > r.starting_bankroll]
    losses = [r for r in results if r.ending_bankroll < r.starting_bankroll]
    pushes = [r for r in results if r.ending_bankroll == r.starting_bankroll]
    return {
        "n": len(results),
        "worst_ending": min(ends),
        "worst_growth": min(growths),
        "best_ending": max(ends),
        "best_growth": max(growths),
        "winners": len(wins),
        "avg_win_growth": statistics.mean([r.growth for r in wins]) if wins else 0.0,
        "losers": len(losses),
        "avg_loss_growth": statistics.mean([r.growth for r in losses]) if losses else 0.0,
        "pushes": len(pushes),
        "growth_sd": statistics.pstdev(growths) if len(growths) > 1 else 0.0,
        "worst_drawdown": max(r.max_drawdown for r in results),
        "mean_ending": statistics.mean(ends),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bankroll", type=float, default=10000)
    parser.add_argument("--rounds", type=int, default=2000)
    parser.add_argument("--sessions", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20261111)
    parser.add_argument("--curve", type=str, default=None)
    args = parser.parse_args()
    if args.curve:
        with open(args.curve, encoding="utf-8") as f:
            curve = [tuple(p) for p in json.load(f)]
    else:
        curve = MEASURED_EDGE_CURVE
    if curve is None:
        raise SystemExit(
            "no edge curve: pass --curve curve.json, or set MEASURED_EDGE_CURVE "
            "in blackjack/edge_curve.py from the 6a measurement"
        )
    half_rules = Rules(
        num_decks=6,
        starting_balance=args.bankroll,
        kelly_fraction=0.5,
    )
    full_rules = Rules(
        num_decks=6,
        starting_balance=args.bankroll,
        kelly_fraction=1.0,
    )
    ramp_rules = Rules(
        num_decks=6,
        starting_balance=args.bankroll,
    )
    strategy = BasicStrategy(ramp_rules)
    session = SessionConfig(rounds=args.rounds)
    policies = (
        ("Kelly (half)", half_rules, KellyPolicy(half_rules, curve)),
        ("Kelly (full)", full_rules, KellyPolicy(full_rules, curve)),
        ("Ramp A (1/TC)", ramp_rules, RampPolicy(ramp_rules, "A")),
        ("Ramp B (1-2-4-8)", ramp_rules, RampPolicy(ramp_rules, "B")),
    )
    results = {}
    for name, rules, policy in policies:
        results[name] = run_sessions(
            rules, strategy, policy, session, args.sessions, args.seed
        )
    print(f"# {args.sessions} sessions x {args.rounds} rounds, 6 decks, "
          f"S17 DAS LS 3:2, bankroll ${args.bankroll:,.0f}, "
          f"half Kelly vs full Kelly vs Ramp A vs Ramp B, "
          f"seed {args.seed}")
    print(f"# {'policy':>16} {'risk_of_ruin':>13} {'mean_growth':>11} "
          f"{'mean_drawdown':>14} {'mean_ending':>11}")
    for name, _rules, _policy in policies:
        out = results[name]
        print(f"# {name:>16} {out['risk_of_ruin']:>13.3f} "
              f"{out['mean_growth']:>+11.3f} {out['mean_max_drawdown']:>14.1f} "
              f"{out['mean_ending_bankroll']:>11.1f}")
    print("# distribution: worst and best session, average win and loss, spread")
    print(f"# {'policy':>16} {'worst':>11} {'best':>11} "
          f"{'avg_win':>8} {'avg_loss':>8} {'growth_sd':>9} {'worst_dd':>9}")
    for name, _rules, _policy in policies:
        d = summarize_distribution(results[name])
        print(f"# {name:>16} {d['worst_growth']:>+11.1%} {d['best_growth']:>+11.1%} "
              f"{d['avg_win_growth']:>+8.1%} {d['avg_loss_growth']:>+8.1%} "
              f"{d['growth_sd']:>9.3f} {d['worst_drawdown']:>9.0f}")


if __name__ == "__main__":
    main()
