"""Pydantic contracts for batched agent outputs and saved system runs."""

from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Finding(Contract):
    finding_id: str
    cluster_ids: list[str]
    verdict: Literal['malicious', 'suspicious', 'benign']
    summary: str
    evidence_line_ids: list[str] = Field(max_length=10)
    src_ips: list[str]
    users: list[str]
    hosts: list[str]
    reasoning: str
    status: Literal['validated', 'unvalidated'] = 'validated'


class TechniqueChoice(Contract):
    technique_id: str = Field(pattern=r'^T\d{4}(?:\.\d{3})?$')
    name: str
    tactic: str
    is_primary: bool
    justification: str


class MappedFinding(Contract):
    finding_id: str
    techniques: list[TechniqueChoice] = Field(max_length=3)
    mapping_confidence: float = Field(ge=0, le=1)
    status: Literal['validated', 'unvalidated'] = 'validated'


class KillChainStep(Contract):
    order: int = Field(ge=1)
    ts_utc: AwareDatetime
    finding_id: str
    technique_id: str = Field(pattern=r'^T\d{4}(?:\.\d{3})?$')
    description: str


class Incident(Contract):
    incident_id: str
    finding_ids: list[str]
    title: str
    severity: Literal['low', 'medium', 'high', 'critical']
    confidence: float = Field(ge=0, le=1)
    attacker_ips: list[str]
    affected_assets: list[str]
    kill_chain: list[KillChainStep]
    rationale: str
    status: Literal['validated', 'unvalidated'] = 'validated'


class Action(Contract):
    action: str
    target: str
    priority: Literal['P1', 'P2', 'P3']
    example_command: str | None = None


class MitigationRef(Contract):
    mitigation_id: str = Field(pattern=r'^M\d{4}$')
    name: str
    for_technique_id: str = Field(pattern=r'^T\d{4}(?:\.\d{3})?$')


class ResponsePlan(Contract):
    incident_id: str
    executive_summary: str
    immediate_actions: list[Action]
    mitigations: list[MitigationRef]
    investigation_steps: list[str]
    prevention: list[str]
    status: Literal['validated', 'unvalidated'] = 'validated'


class FindingList(Contract):
    findings: list[Finding]


class MappedFindingList(Contract):
    mappings: list[MappedFinding]


class IncidentList(Contract):
    incidents: list[Incident]


class ResponsePlanList(Contract):
    plans: list[ResponsePlan]


class AnalysisOutput(Contract):
    findings: list[Finding]
    mappings: list[MappedFinding]
    incidents: list[Incident]
    plans: list[ResponsePlan]
