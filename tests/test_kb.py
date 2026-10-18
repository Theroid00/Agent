"""T-KB: official IDs, active objects, mitigation edges and provenance."""

from copy import deepcopy
import pytest
from cyberagents.attack_kb import parse_bundle, verify_catalog, save_kb, load_kb


def test_extracts_mitre_reference_and_optional_fields(attack_bundle):
    kb = parse_bundle(attack_bundle, source_ref="fixture")
    record = kb["techniques"]["T1110.001"]
    assert record["name"] == "Password Guessing"
    assert record["tactics"] == ["credential-access"]
    assert record["platforms"] == ["Linux"]
    assert record["description"] == "Repeated SSH password attempts."
    assert record.get("detection", "") == ""
    assert kb["source_ref"] == "fixture"


@pytest.mark.parametrize("flag", ["revoked", "x_mitre_deprecated"])
def test_excludes_inactive_techniques(attack_bundle, flag):
    attack_bundle["objects"][0][flag] = True
    kb = parse_bundle(attack_bundle, source_ref="fixture")
    assert kb["techniques"] == {}
    assert kb["mitigations"] == {}


def test_mitigation_map_uses_mitigates_edges(attack_bundle):
    kb = parse_bundle(attack_bundle, source_ref="fixture")
    assert kb["mitigations"]["T1110.001"] == [{"id": "M1032", "name": "Multi-factor Authentication"}]


@pytest.mark.parametrize("object_index,flag", [(1, "revoked"), (1, "x_mitre_deprecated"),
                                              (2, "revoked"), (2, "x_mitre_deprecated")])
def test_drops_inactive_mitigations_and_edges(attack_bundle, object_index, flag):
    attack_bundle["objects"][object_index][flag] = True
    kb = parse_bundle(attack_bundle, source_ref="fixture")
    assert not kb["mitigations"].get("T1110.001")


def test_missing_official_reference_is_not_invented(attack_bundle):
    attack_bundle["objects"][0]["external_references"] = []
    assert parse_bundle(attack_bundle, source_ref="fixture")["techniques"] == {}


def test_unknown_relationship_target_is_ignored(attack_bundle):
    attack_bundle["objects"][2]["target_ref"] = "attack-pattern--absent"
    assert not parse_bundle(attack_bundle, source_ref="fixture")["mitigations"].get("T1110.001")


def test_duplicate_official_ids_are_rejected(attack_bundle):
    duplicate = deepcopy(attack_bundle["objects"][0])
    duplicate["id"] = "attack-pattern--duplicate"
    attack_bundle["objects"].append(duplicate)
    with pytest.raises(ValueError, match="T1110.001"):
        parse_bundle(attack_bundle, source_ref="fixture")


def test_catalog_checks_id_and_expected_name(attack_bundle):
    kb = parse_bundle(attack_bundle, source_ref="fixture")
    verify_catalog(kb, {"T1110.001": "Password Guessing"})
    with pytest.raises(ValueError, match="T1110.001"):
        verify_catalog(kb, {"T1110.001": "Incorrect name"})
    with pytest.raises(ValueError, match="T1046"):
        verify_catalog(kb, {"T1046": "Network Service Discovery"})


def test_saved_kb_preserves_records_and_source(attack_bundle, tmp_path):
    kb = parse_bundle(attack_bundle, source_ref="fixture")
    path = tmp_path / "attack_kb.json"
    save_kb(kb, path)
    assert load_kb(path) == kb


def test_modern_detection_strategy_links_resolve_active_analytics(attack_bundle):
    strategy = {'type': 'x-mitre-detection-strategy', 'id': 'x-mitre-detection-strategy--sample',
                'name': 'Authentication monitoring', 'x_mitre_analytic_refs': ['x-mitre-analytic--sample']}
    analytic = {'type': 'x-mitre-analytic', 'id': 'x-mitre-analytic--sample',
                'name': 'Repeated failures', 'description': 'Monitor rapid authentication failures.'}
    relation = {'type': 'relationship', 'id': 'relationship--detect', 'relationship_type': 'detects',
                'source_ref': strategy['id'], 'target_ref': attack_bundle['objects'][0]['id']}
    attack_bundle['objects'].extend([strategy, analytic, relation])
    kb = parse_bundle(attack_bundle, source_ref='fixture')
    assert 'Monitor rapid authentication failures.' in kb['techniques']['T1110.001']['detection']
    analytic['x_mitre_deprecated'] = True
    kb = parse_bundle(attack_bundle, source_ref='fixture')
    assert 'Monitor rapid authentication failures.' not in kb['techniques']['T1110.001']['detection']
