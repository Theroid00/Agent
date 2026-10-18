# Frozen V2 evaluation on Windows

Development seed: 42; fresh held-out seeds: [812399, 876694].

Freeze decision: D38; commit: a2e4246126737d9f124380ed949081dacca0bece.

Source/configuration SHA256: `d6ab1afbe2917d6f187c59be3551859dbf19cb022e955eeb64c3f4612facd1a0`.

## Per-seed measured results

| system | seed | detection_recall | incident_precision | false_positives | benign_case_false_positives | mapping_accuracy | a6_stages | nonexistent_technique_ids | unretrieved_technique_ids | invalid_evidence_refs | runtime_s | llm_calls | tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | 42 | 1.0 | 0.45 | 11 | 5 | n/a | 2 | 0 | n/a | 0 | 1.702999999979511 | 0 | 0 |
| S1 | 42 | 0.3333333333333333 | 1.0 | 0 | 0 | 0.6 | 4 | 0 | n/a | 0 | 1.7040000000270084 | 0 | 0 |
| S3 | 42 | 1.0 | 1.0 | 0 | 0 | 0.9 | 5 | 0 | 0.0 | 0 | 78.375 | 0 | 0 |
| S0 | 812399 | 1.0 | 0.34615384615384615 | 17 | 5 | n/a | 2 | 0 | n/a | 0 | 1.875 | 0 | 0 |
| S1 | 812399 | 0.3333333333333333 | 1.0 | 0 | 0 | 0.6666666666666666 | 5 | 1 | n/a | 0 | 13.938000000081956 | 1 | 26418 |
| S3 | 812399 | 1.0 | 1.0 | 0 | 0 | 0.9 | 5 | 0 | 0.0 | 0 | 129.4529999999795 | 4 | 111057 |
| S0 | 876694 | 1.0 | 0.32142857142857145 | 19 | 5 | n/a | 2 | 0 | n/a | 0 | 1.875 | 0 | 0 |
| S1 | 876694 | 0.5 | 1.0 | 0 | 0 | 0.6666666666666666 | 4 | 1 | n/a | 0 | 14.047000000020489 | 1 | 26876 |
| S3 | 876694 | 1.0 | 1.0 | 0 | 0 | 0.7 | 4 | 0 | 0.0 | 0 | 132.6720000000205 | 5 | 111514 |

## Held-out means (development excluded)

| system | detection_recall | false_positives | mapping_accuracy | hallucination_rate | runtime_s |
| --- | --- | --- | --- | --- | --- |
| S0 | 1.0 | 18.0 | n/a | 0.0 | 1.875 |
| S1 | 0.41666666666666663 | 0.0 | 0.6666666666666666 | 0.11805555555555555 | 13.992500000051223 |
| S3 | 1.0 | 0.0 | 0.8 | 0.0 | 131.0625 |

## S3 target checks

| seed | split | recall_target | benign_fp_target | mapping_target | a6_four_stages | grounding_target | runtime_target | coverage_complete |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 42 | development | True | True | True | True | True | True | True |
| 812399 | held-out | True | True | True | True | True | True | True |
| 876694 | held-out | True | True | False | True | True | True | True |

## Errors

| system | seed | kind | item | matched_scenario | cause |
| --- | --- | --- | --- | --- | --- |
| S0 | 42 | false_positive | s0-i1 | B4 | Benign/background evidence retained as an incident |
| S0 | 42 | false_positive | s0-i6 | __background__ | Benign/background evidence retained as an incident |
| S0 | 42 | false_positive | s0-i10 | __background__ | Benign/background evidence retained as an incident |
| S0 | 42 | false_positive | s0-i11 | B1 | Benign/background evidence retained as an incident |
| S0 | 42 | false_positive | s0-i12 | B3 | Benign/background evidence retained as an incident |
| S0 | 42 | false_positive | s0-i14 | B2 | Benign/background evidence retained as an incident |
| S0 | 42 | false_positive | s0-i15 | __background__ | Benign/background evidence retained as an incident |
| S0 | 42 | false_positive | s0-i17 | __background__ | Benign/background evidence retained as an incident |
| S0 | 42 | false_positive | s0-i18 | __background__ | Benign/background evidence retained as an incident |
| S0 | 42 | false_positive | s0-i19 | __background__ | Benign/background evidence retained as an incident |
| S0 | 42 | false_positive | s0-i20 | B5 | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i1 | B4 | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i9 | B1 | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i10 | __background__ | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i11 | __background__ | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i12 | __background__ | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i13 | B3 | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i15 | __background__ | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i16 | __background__ | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i17 | B2 | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i19 | __background__ | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i20 | __background__ | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i21 | __background__ | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i22 | __background__ | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i23 | __background__ | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i24 | __background__ | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i25 | __background__ | Benign/background evidence retained as an incident |
| S0 | 812399 | false_positive | s0-i26 | B5 | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i1 | B4 | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i6 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i10 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i11 | B1 | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i12 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i13 | B3 | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i15 | B2 | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i16 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i18 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i19 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i20 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i21 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i22 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i23 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i24 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i25 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i26 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i27 | __background__ | Benign/background evidence retained as an incident |
| S0 | 876694 | false_positive | s0-i28 | B5 | Benign/background evidence retained as an incident |
| S1 | 42 | miss | A1 | A1 | Analyst dismissal/correlation |
| S1 | 42 | miss | A2 | A2 | Analyst dismissal/correlation |
| S1 | 42 | miss | A3 | A3 | Analyst dismissal/correlation |
| S1 | 42 | miss | A5 | A5 | Analyst dismissal/correlation |
| S1 | 812399 | miss | A1 | A1 | Analyst dismissal/correlation |
| S1 | 812399 | miss | A2 | A2 | Analyst dismissal/correlation |
| S1 | 812399 | miss | A3 | A3 | Analyst dismissal/correlation |
| S1 | 812399 | miss | A5 | A5 | Analyst dismissal/correlation |
| S1 | 876694 | miss | A1 | A1 | Analyst dismissal/correlation |
| S1 | 876694 | miss | A3 | A3 | Analyst dismissal/correlation |
| S1 | 876694 | miss | A5 | A5 | Analyst dismissal/correlation |

## Limits and reproducibility

These are unseen draws from the same fixed synthetic generator, not real-world validation or new attack families. Mapping accuracy is conditional on detected scenarios/stages; compare recall alongside it. Development and held-out data are reported separately. Prompts, models, thresholds, evaluator and scenarios were fixed before held-out generation. No tuning or replacement seeds followed exposure. Existing identical provider responses may be reused; live-call counts and runtime are reported without claiming an uncached speedup. A zero hallucination score for both systems is a tie, not evidence that S3 beats S1. All response actions are recommendations. Original D33 and V2 development artifacts remain preserved.


## Outcome and remaining semantic mapping errors

All nine S0/S1/S3 runs completed. S3 detects all six attacks with no false positives on both fresh seeds, but does not meet every target: seed 876694 has mapping accuracy 0.7, below the 0.8 per-seed target. The held-out mean is 0.8; it must not be presented as every seed passing. Notebook verification reports `82 passed, 1 deselected, 26 warnings in 51.35s` and all eight code cells completed.

| Fresh seed | S3 recall | S3 mapping accuracy | S3 false positives | A6 evidence stages |
|---|---|---|---|---|
| 812399 | 1.0 | 0.9 | 0 | 5 |
| 876694 | 1.0 | 0.7 | 0 | 4 |

On fresh seed 812399, finding `f-c008` describes an external port scan, while its primary technique is `T1595.002` (Vulnerability Scanning). The fixed A3 scenario accepts `T1046` or `T1595.001`. The saved run therefore has mapping accuracy 0.9 even though recall is 1.0 and grounding violations are zero.

This distinguishes valid, retrieved IDs from correct interpretation of observed behavior. The error is preserved in `S3_seed812399.json`; neither the accepted mappings nor the frozen system was changed after exposure. Passing the aggregate mapping target does not make every mapping correct.

On seed 876694, findings `f003` and `f009` describe port scans but choose the broader `T1595` (Active Scanning); the fixed accepted port-scan mappings are `T1046` or `T1595.001`. Finding `f004` combines failed and successful SSH authentication with primary `T1110` and secondary `T1133`; the successful-session stage instead accepts `T1078` or `T1021.004`. These are semantic mapping errors, not nonexistent or unretrieved IDs. The initial scan is a separate incident (`inc-002`), while `inc-003` joins authentication, privilege escalation and outbound transfer.

The unchanged evaluator's A6 metric measures stage evidence overlap within an incident, not the number of correct explicit technique steps. Seed 876694 has four such stages in its best-correlated incident; it does not present the entire five-stage chain together. Mapping accuracy separately penalizes incorrect primary choices.

Held-out S0 averages 18 false positives versus S3's 0. Held-out S1 averages detection_recall 0.41666666666666663 and mapping_accuracy 0.6666666666666666 versus S3's 1.0 and 0.8. S1 has one nonexistent technique ID on each fresh seed; S3 has zero nonexistent/unretrieved IDs and zero invalid evidence references. These results concern draws from the same synthetic generator, not real-world validation.

The comparison charts average all three declared seeds, including development; use held_out_summary.csv for fresh-data-only means. P19/P20 record the unresolved semantic errors. No tuning or held-out rerun followed exposure.

