"""T-EVAL: hand-computed perfect/bad scores before evaluator implementation."""
import pytest
from cyberagents.evaluate import evaluate


def golden():
    truth = {'scenarios': [
        {'scenario_id': 'A1', 'type': 'attack', 'line_ids': ['a1'], 'accepted_techniques': ['T1110.001'], 'stages': None},
        {'scenario_id': 'A6', 'type': 'attack', 'line_ids': [f'e{i}' for i in range(1, 6)],
         'stages': [{'stage': i, 'line_ids': [f'e{i}'], 'accepted_techniques': [tid]}
                    for i, tid in enumerate(['T1046', 'T1110.001', 'T1078', 'T1548.003', 'T1048'], 1)]},
        {'scenario_id': 'B1', 'type': 'benign', 'line_ids': ['b1'], 'stages': None}]}
    kb = {'techniques': {tid: {} for tid in ['T1110.001', 'T1046', 'T1078', 'T1548.003', 'T1048']}, 'mitigations': {}}
    output = {'system': 'S3', 'seed': 42,
              'findings': [{'finding_id': 'f1', 'evidence_line_ids': ['a1']}] + [
                  {'finding_id': f'f6{i}', 'evidence_line_ids': [f'e{i}']} for i in range(1, 6)],
              'mappings': [], 'incidents': [{'incident_id': 'i1', 'finding_ids': ['f1'], 'kill_chain': []},
                                          {'incident_id': 'i6', 'finding_ids': [f'f6{i}' for i in range(1, 6)], 'kill_chain': []}],
              'retrieval_log': {}}
    for finding, tid in zip(output['findings'], ['T1110.001', 'T1046', 'T1110.001', 'T1078', 'T1548.003', 'T1048']):
        fid = finding['finding_id']
        output['mappings'].append({'finding_id': fid, 'techniques': [{'technique_id': tid, 'is_primary': True}]})
        output['retrieval_log'][fid] = [tid]
        output['incidents'][0 if fid == 'f1' else 1]['kill_chain'].append({'finding_id': fid, 'technique_id': tid})
    return truth, kb, output


def test_perfect_output_has_perfect_scores_and_one_correlated_chain():
    truth, kb, output = golden()
    metrics = evaluate(output, truth, kb)
    assert metrics['detection_recall'] == 1
    assert metrics['incident_precision'] == 1
    assert metrics['false_positives'] == 0
    assert metrics['mapping_accuracy'] == 1
    assert metrics['a6_stages'] == 5 and metrics['a6_correlated'] is True
    assert metrics['hallucination_rate'] == 0 and metrics['invalid_evidence_rate'] == 0


def test_bad_output_matches_hand_computed_scores():
    # Two attacks: one detected; one true and one false incident; zero correct mappings.
    # Evidence refs: a1, missing, b1 -> one invalid out of three. One invented ID.
    truth, kb, output = golden()
    output.update(findings=[{'finding_id': 'f1', 'evidence_line_ids': ['a1', 'missing']},
                            {'finding_id': 'fb', 'evidence_line_ids': ['b1']}],
                  mappings=[{'finding_id': 'f1', 'techniques': [{'technique_id': 'T9999', 'is_primary': True}]}],
                  incidents=[{'incident_id': 'i1', 'finding_ids': ['f1'], 'kill_chain': [{'finding_id': 'f1', 'technique_id': 'T9999'}]},
                             {'incident_id': 'ib', 'finding_ids': ['fb'], 'kill_chain': []}], retrieval_log={})
    metrics = evaluate(output, truth, kb)
    assert metrics['detection_recall'] == .5
    assert metrics['incident_precision'] == .5
    assert metrics['false_positives'] == 1
    assert metrics['mapping_accuracy'] == 0
    assert metrics['a6_stages'] == 0 and metrics['a6_correlated'] is False
    assert metrics['hallucination_rate'] == 1
    assert metrics['invalid_evidence_rate'] == pytest.approx(1 / 3)


def test_background_evidence_is_a_false_positive_and_s0_mapping_is_na():
    truth, kb, output = golden()
    output['system'] = 'S0'
    output['findings'].append({'finding_id': 'noise', 'evidence_line_ids': ['noise:1']})
    output['incidents'].append({'incident_id': 'noise', 'finding_ids': ['noise'], 'kill_chain': []})
    metrics = evaluate(output, truth, kb, valid_line_ids={'a1', 'b1', 'noise:1', *[f'e{i}' for i in range(1, 6)]})
    assert metrics['false_positives'] == 1
    assert metrics['invalid_evidence_rate'] == 0
    assert metrics['mapping_accuracy'] is None


def test_benign_case_false_positives_are_separate_from_background():
    truth, kb, output = golden()
    output['findings'] += [{'finding_id': 'b', 'evidence_line_ids': ['b1']},
                           {'finding_id': 'noise', 'evidence_line_ids': ['noise:1']}]
    output['incidents'] += [{'incident_id': 'b', 'finding_ids': ['b'], 'kill_chain': []},
                            {'incident_id': 'noise', 'finding_ids': ['noise'], 'kill_chain': []}]
    metrics = evaluate(output, truth, kb, valid_line_ids={'a1', 'b1', 'noise:1', *[f'e{i}' for i in range(1, 6)]})
    assert metrics['false_positives'] == 2
    assert metrics['benign_case_false_positives'] == 1
    assert metrics['background_false_positives'] == 1
