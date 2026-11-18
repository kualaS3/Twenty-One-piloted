## Iteration 6c

Iterations 6a and 6b measured the edge and built the Kelly bet sizing. This iteration asks the question the books ask instead: what if you ignore the measured edge entirely and size your bets off the rounded true count, the way most blackjack books teach it.

The books do not carry an edge curve to the table. They carry a ramp: a fixed number of units per true count. Two ramps are in here, the two most common shapes. Ramp A is one unit per +1 true count: 1 unit below a count of 1, 2 units from 1 to 2, 3 units from 2 to 3, and so on. Ramp B is the 1-2-4-8 spread: 1 unit below a count of 1, 2 units from 1 to 2, 4 units from 2 to 3, and 8 units at 3 and above. Both bet units times the table minimum, clamped to the table limits and to whole dollars, and both bet the table minimum whenever the count is at or below zero. Neither ramp reads the edge curve at all. That is the whole point of a book ramp: the count alone sizes the bet, with no measured edge and no variance anywhere in the maths.

The comparison runs all four policies on the same seeded shoes, so they face the same cards and only the bet sizing differs: half Kelly, full Kelly, Ramp A and Ramp B. The simulator, the Kelly policies, the edge curve and basic strategy are unchanged from 6b. Only the ramp policy and the comparison script are new.

- **The theory, before the numbers.** Full Kelly maximises the long-run growth of the bankroll by construction, so no sizing rule can beat it on growth. That is a theorem, not a prediction. The live questions are the ones around it: does a ramp beat half Kelly on growth, and how do the four compare on ruin and drawdown. A ramp that grows almost as fast as full Kelly with a smaller drawdown is interesting even though it loses on growth, because drawdown is what ends a session early in practice, and because a ramp needs no curve at all to run.

- **The ramp policy.** `blackjack/ramp.py` holds `RampPolicy`, with the same `bet(bankroll, true_count)` interface as the Kelly policies. The constructor takes the rules and a ramp letter, "A" or "B", and nothing else. There is no curve argument to pass, which is the test that the policy really does ignore the edge: the same count bets the same amount under half-Kelly rules and full-Kelly rules. Ramp A floors the true count and takes at least 1 unit. Ramp B steps through 1, 2, 4 and 8 units at counts of 1, 2 and 3. Both clamp to the table limits and to the bankroll, and both return 0 when the bankroll cannot cover the table minimum.

- **The comparison run.** `run_ramp_comparison.py` runs 50 sessions of 2000 rounds on a $10,000 bankroll, six decks, S17, double after split, late surrender, 3:2, seed 20261111, the same config as the 6b sample run. The run takes about 25 seconds and reproduces exactly on a repeat with the same seed.

  | Policy | Risk of ruin | Mean growth | Mean max drawdown | Mean ending bankroll |
  |---|---|---|---|---|
  | Kelly (half) | 0.000 | +0.019 | $1023.3 | $10190.8 |
  | Kelly (full) | 0.000 | +0.045 | $1852.4 | $10449.2 |
  | Ramp A (1/TC) | 0.000 | +0.018 | $888.1 | $10183.7 |
  | Ramp B (1-2-4-8) | 0.000 | +0.039 | $1432.7 | $10387.3 |

  The half-Kelly row matches the 6b sample run exactly, which is the check that the comparison is running the same game. Full Kelly wins on growth, as the theory says it must: +4.5% over 2000 rounds, against +3.9% for Ramp B, +1.9% for half Kelly and +1.8% for Ramp A. No ramp beats full Kelly on growth, and if one had, that would have been a reason to distrust the simulator rather than celebrate the ramp.

  The interesting answers are the two in the middle. Ramp B beats half Kelly on growth by about double (+3.9% against +1.9%) while drawing down less than full Kelly ($1433 against $1852). It is most of full Kelly's growth with less of its swing, and it does it with no edge curve at all. Ramp A is the quiet one: it ties half Kelly on growth (+1.8% against +1.9%) with the smallest drawdown of the four ($888), because it bets the table minimum on most rounds and only steps up when the count is genuinely good.

  The means hide how different the sessions feel, so here is the spread. Worst and best are the worst and best single session out of the 50, average win and average loss are the mean growth over just the winning and just the losing sessions, and the spread is the standard deviation of the per-session growth.

  | Policy | Worst session | Best session | Avg win (n) | Avg loss (n) | Growth spread |
  |---|---|---|---|---|---|
  | Kelly (half) | $8,231 (-17.7%) | $12,324 (+23.2%) | +8.1% (28) | -6.0% (22) | 0.089 |
  | Kelly (full) | $7,314 (-26.9%) | $13,674 (+36.7%) | +16.0% (28) | -10.1% (22) | 0.161 |
  | Ramp A (1/TC) | $7,930 (-20.7%) | $11,965 (+19.6%) | +7.1% (30) | -6.0% (20) | 0.081 |
  | Ramp B (1-2-4-8) | $7,755 (-22.5%) | $12,725 (+27.2%) | +13.0% (27) | -6.8% (23) | 0.122 |

  Full Kelly does not win more often: it wins 28 sessions out of 50, exactly the same as half Kelly. It wins bigger and loses bigger, with an average win of +16.0% against half Kelly's +8.1% and an average loss of -10.1% against -6.0%. The growth edge comes entirely from the size of the wins and losses, not from their frequency, and the worst full-Kelly session loses $917 more than the worst half-Kelly one. Ramp B is the interesting middle again: its average win of +13.0% is most of full Kelly's +16.0%, while its average loss of -6.8% is close to half Kelly's -6.0%. Ramp A wins the most sessions (30 of 50) and loses the fewest (20), with the tightest spread of the four, which is what a minimum-bet-most-of-the-time ramp should look like.

  Two honest caveats. First, the half-Kelly and Ramp A growth numbers are a tenth of a percent apart, which is inside the noise of a 50-session batch: that tie could flip on another seed batch, so read it as "about the same", not "Ramp A is worse". Second, ruin does not separate anyone here. All four are 0.000 from $10,000 over 2000 rounds, the same as in 6b. The ruin numbers would separate at a smaller bankroll or a longer session, and this run says nothing about that.

- **How to run it.** Build the C helper first (`python build.py`, needs gcc or cc) -- the tests need it, the simulator does not. Run the comparison with `python run_ramp_comparison.py` (about 25 seconds). The old 6b script is still here: `python run_simulation.py` runs half Kelly against flat $10. The tests run with `pytest tests/` (160 passed, 2 skipped, about 80 seconds). The skipped tests are the 6a TC-0 anchor and the every-bucket total-variance check, both gated behind AOH_SLOW=1.

- **What changed, file by file.** `blackjack/ramp.py`: `RampPolicy` (ramps "A" and "B"), `RAMP_B_STEPS`, and the `units` helper. `run_ramp_comparison.py`: the four-policy comparison script, plus the distribution summary (worst and best session, average win and loss, growth spread). `tests/test_iteration6c.py`: the ramp sizing at every step boundary, the table limits, the bankroll floor, the proof that the sizing ignores the Kelly fraction, a small smoke test that the simulator runs a RampPolicy and reproduces itself exactly, and a distribution summary test. Everything else is the 6b code, unchanged.

Still not in: one player only.
