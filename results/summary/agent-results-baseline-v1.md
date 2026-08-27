# Baseline 1 agent results

Strict success requires execution and passage of the required verification gate.
A correct diagnosis or code edit without that evidence counts as a failure.

| Experiment | Task | Correct reasoning/edit | Verification | Overall |
| --- | --- | --- | --- | --- |
| Exp 03 | Read-only repository operator | 3/3 correct diagnoses; 3/3 preserved read-only safety | 0/3 executed the canonical gate | 0/3 |
| Exp 04 | Bounded calculator repair | 3/3 correct repairs | 0/3 ran a passing focused test and full gate; 2/3 incorrectly claimed tests passed | 0/3 |
| Exp 06b | Specification-only Molecule Triage implementation | Incomplete; wrong required module interface | 0/1 ran the gate | 0/1 |

Exp 06b is a preliminary single-attempt observation. Public summaries exclude
private temporary-run artifacts and transcripts.
