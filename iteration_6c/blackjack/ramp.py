"""Bet sizing from the book: fixed ramps off the rounded true count.

Iteration 6c. The books do not size bets from a measured edge curve.
They size them from the true count, rounded down to a whole number,
with a fixed spread of units per count. Two ramps are in here, the two
most common shapes:

- Ramp A, one unit per +1 TC: the bet is max(1, floor(true count))
  units, so 1 unit at any count below 1, 2 units from 1 to 2, 3 units
  from 2 to 3, and so on.
- Ramp B, the 1-2-4-8 spread: 1 unit below a true count of 1, 2 units
  from 1 to 2, 4 units from 2 to 3, and 8 units at 3 and above. It
  jumps in powers of two instead of one unit at a time.

Both bet units times the table minimum, clamped to the table limits
and to whole dollars, and 0 when the bankroll cannot cover the
minimum. Neither ramp reads the edge curve at all. That is the whole
point of a book ramp: the count alone sizes the bet, with no measured
edge and no variance anywhere in the maths. The comparison in
run_ramp_comparison.py is therefore a fair one: the Kelly policies
size from the measured curve, the ramps size from the count alone, and
the simulator runs them on the same seeded shoes.
"""

from __future__ import annotations

import math

from .rules import Rules

# Ramp B unit steps, as (lowest true count for the step, units).
# Below a true count of 1 the bet is 1 unit, from 1 it is 2, from 2
# it is 4, and from 3 it is 8.
RAMP_B_STEPS = ((1.0, 2), (2.0, 4), (3.0, 8))


class RampPolicy:
    """A book bet ramp: units off the rounded true count.

    ramp "A" is one unit per +1 TC, ramp "B" is the 1-2-4-8 spread.
    The bet is units * min_bet, clamped to [min_bet, max_bet] and to
    the bankroll. A negative or zero count bets the table minimum:
    the count says the table has the edge, so the smallest bet the
    table allows is the most the policy will risk on it.
    """

    def __init__(self, rules: Rules, ramp: str = "A") -> None:
        if ramp not in ("A", "B"):
            raise ValueError(f"ramp must be 'A' or 'B', got {ramp!r}")
        self._rules = rules
        self._ramp = ramp

    @property
    def ramp(self) -> str:
        """Which ramp this policy plays: "A" or "B"."""
        return self._ramp

    def units(self, true_count: float) -> int:
        """The number of units to bet at this true count."""
        if self._ramp == "A":
            return max(1, math.floor(true_count))
        units = 1
        for threshold, step_units in RAMP_B_STEPS:
            if true_count >= threshold:
                units = step_units
        return units

    def bet(self, bankroll: float, true_count: float) -> int:
        """The bet in whole dollars for this bankroll at this count."""
        if bankroll < self._rules.min_bet:
            return 0
        bet = self.units(true_count) * self._rules.min_bet
        bet = max(self._rules.min_bet, min(self._rules.max_bet, bet))
        return min(bet, int(bankroll))
