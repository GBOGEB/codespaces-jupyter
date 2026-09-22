# W289 lossless handover - QPS authority-guard P1 repair

Repository: GBOGEB/codespaces-jupyter

## Why W289 exists

W288 PR #5 merged at d589aaad01ddbf37f8020a448cd847539583bb23
before its final requested Codex review completed. That review subsequently
raised material P1 finding 4074272043 against merged code.

The issue was not the reproduced QPS count calculation. The issue was that the
workload receipt hard-coded no-authority / zero-credit values rather than
rejecting source-backed fixtures that contradicted those guards. That could make
the exact-v0.5 regeneration and zero-credit conditions compensating.

## Repair

W289 changes only the bounded proof/control layer:

- validate baseline authority_transfer=false;
- validate baseline formal_credit_delta=0 and baseline status=PASS;
- validate expected state=EXPECTED_NOT_YET_CREDITED;
- validate expected authority_transfer=false;
- validate formal, engineering, negotiation and compliance credit deltas are 0;
- require the controlled exact-v0.5 regeneration promotion gate verbatim;
- emit authority and credit values from the validated fixture;
- persist guard_validation in workload_receipt.json;
- make CI assert guard_validation and all zero-credit/no-authority fields;
- expose guard validation in the real QPS notebook before calculation.

The QPS expected calculation remains unchanged. The exact source v0.5 workbook
binary regeneration gate in GBOGEB/cryoplant-project remains separate and
unsatisfied by this runtime proof.

## P2 follow-up

Codex review of exact head 01f864e2e9becaeb616706990c75010d96ae9c61
raised P2 finding 4074342402: Python treats False == 0, so a JSON boolean could
incorrectly satisfy a zero-credit check. The repair now defines numeric zero as
an int or float that is not bool and equals zero. The baseline formal-credit
field, all expected credit fields, and CI receipt verification use that strict
check.

The earlier exact-head proof remains historical evidence for the P1 repair, but
3PC Prove is reset until the P2-repaired final head is recertified.

## Exact next gate

Open the W289 repair PR, obtain exact-head qps-project-workload-proof and generic
runtime proof, then request final review. Require the project workflow to show:
more than zero executed notebook cells on both runs, equal notebook outputs,
PASS_REPRODUCED_EXPECTED_V06_CALCULATION_NOT_PROMOTION, and
guard_validation.all_non_compensating_guards_passed=true.

Merge only after the material P1 is repaired and the exact-head proof is green.
Then emit the MissionControl closure receipt.

No authority transfer. All formal, engineering, negotiation and compliance
credit deltas remain zero.
