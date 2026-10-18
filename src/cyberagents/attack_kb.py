"""Pinned MITRE STIX parsing, active technique catalog and mitigation edges."""

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen
from .config import CONFIG, CATALOG


def _active(obj):
    return not obj.get("revoked", False) and not obj.get("x_mitre_deprecated", False)


def _external_id(obj):
    return next((r.get("external_id") for r in obj.get("external_references", [])
                 if r.get("source_name") == "mitre-attack"), None)


def parse_bundle(bundle, *, source_ref):
    if bundle.get("type") != "bundle" or not isinstance(bundle.get("objects"), list):
        raise ValueError("Expected a STIX bundle with an objects list")
    objects = {o["id"]: o for o in bundle["objects"] if "id" in o and _active(o)}
    techniques, mitigations = {}, {}
    for obj in objects.values():
        identifier = _external_id(obj)
        if obj["type"] != "attack-pattern" or not identifier:
            continue
        if identifier in techniques:
            raise ValueError(f"Duplicate ATT&CK ID: {identifier}")
        techniques[identifier] = {
            "id": identifier, "name": obj["name"], "description": obj.get("description", ""),
            "tactics": [p["phase_name"] for p in obj.get("kill_chain_phases", [])
                        if p.get("kill_chain_name") == "mitre-attack"],
            "platforms": obj.get("x_mitre_platforms", []),
            "detection": obj.get("x_mitre_detection", ""),
        }
    for rel in objects.values():
        if rel['type'] == 'relationship' and rel.get('relationship_type') == 'detects':
            strategy, target = objects.get(rel.get('source_ref')), objects.get(rel.get('target_ref'))
            tid = _external_id(target) if target else None
            if strategy and strategy['type'] == 'x-mitre-detection-strategy' and tid in techniques:
                parts = [strategy.get('name', ''), strategy.get('description', '')]
                for reference in strategy.get('x_mitre_analytic_refs', []):
                    analytic = objects.get(reference)
                    if analytic and analytic['type'] == 'x-mitre-analytic':
                        parts.extend([analytic.get('name', ''), analytic.get('description', '')])
                techniques[tid]['detection'] += '\n' + '\n'.join(part for part in parts if part)
        if rel["type"] != "relationship" or rel.get("relationship_type") != "mitigates":
            continue
        source, target = objects.get(rel.get("source_ref")), objects.get(rel.get("target_ref"))
        if not source or not target or source["type"] != "course-of-action":
            continue
        tid, mid = _external_id(target), _external_id(source)
        if tid in techniques and mid and mid.startswith("M"):
            record = {"id": mid, "name": source["name"]}
            if record not in mitigations.setdefault(tid, []):
                mitigations[tid].append(record)
    return {"source_ref": source_ref, "techniques": techniques, "mitigations": mitigations}


def verify_catalog(kb, expected_names=CATALOG):
    errors = [f"{tid}: expected {name!r}" for tid, name in expected_names.items()
              if kb["techniques"].get(tid, {}).get("name") != name]
    if errors:
        raise ValueError("Catalog verification failed: " + "; ".join(errors))


def save_kb(kb, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(kb, indent=2, sort_keys=True))


def load_kb(path):
    return json.loads(Path(path).read_text())


def build_kb():
    path = Path(CONFIG["paths"]["cache"]) / "attack/enterprise-attack.json"
    pin = CONFIG["attack"]
    if not path.exists():
        url = f"https://raw.githubusercontent.com/mitre/cti/{pin['commit']}/enterprise-attack/enterprise-attack.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(url, timeout=60) as response:
            raw = response.read()
        if hashlib.sha256(raw).hexdigest() != pin["sha256"]:
            raise ValueError("ATT&CK download checksum mismatch")
        path.write_bytes(raw)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin["sha256"]:
        raise ValueError("ATT&CK cache checksum mismatch; remove the corrupt cached download")
    kb = parse_bundle(json.loads(raw), source_ref=pin["commit"])
    verify_catalog(kb)
    save_kb(kb, Path(CONFIG["paths"]["out"]) / "attack_kb.json")
    return kb
