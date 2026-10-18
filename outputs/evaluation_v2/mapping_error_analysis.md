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
