"""Central settings; benchmark thresholds change only with a decision entry."""

CONFIG = {
    "system_revision": "coverage-v2",
    "correlation": {"max_gap_min": 60},
    "dev_seed": 42, "held_out_seeds": [7, 2026], "date": "2026-10-17",
    "llm": {"provider": "gemini", "model": "gemini-3.5-flash-lite", "temperature": 0,
            "fallback_model": "llama-3.3-70b-versatile", "min_interval_s": 15,
            "max_retries": 2, "max_tokens": 24000},
    "embed_model": "BAAI/bge-small-en-v1.5",
    "embedding_threads": 1,
    "embed_revision": "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a",
    "attack": {"commit": "50be388e93819a5d20e71cbaaeccfda157abc846",
               "sha256": "66f3fe3f07ef1a2de0bd2fe4b3e8a9ea06c1d0bb2c46171bdbb57c7f7b666524"},
    "rag": {"k_tool": 5, "k_pre": 8, "description_chars": 1200, "detection_chars": 1200,
            "document_format": "clean-description-detection-v2", "query_prefix": "Represent this sentence for searching relevant passages: ",
            "hybrid": True, "rrf_k": 60},
    "rules": {"auth_fail_n": 3, "auth_fail_window_min": 10,
              "spray_users_n": 5, "spray_window_min": 30,
              "scan_ports_n": 15, "scan_window_min": 5,
              "egress_bytes": 100_000_000, "egress_window_min": 60,
              "success_after_fail_window_min": 60},
    "background": {"auth": 3000, "web": 8000, "fw": 10000},
    "auth_background_fail_probability": 0.004,
    "cluster_sample_lines": 10, "max_validation_retries": 1,
    "paths": {"out": "outputs", "cache": ".cache", "index": ".cache/attack_index"},
}

CATALOG = {
    "T1110": "Brute Force", "T1110.001": "Password Guessing", "T1110.003": "Password Spraying",
    "T1046": "Network Service Discovery", "T1595.001": "Scanning IP Blocks",
    "T1190": "Exploit Public-Facing Application", "T1083": "File and Directory Discovery",
    "T1078": "Valid Accounts", "T1021.004": "SSH", "T1548.003": "Sudo and Sudo Caching",
    "T1548": "Abuse Elevation Control Mechanism", "T1048": "Exfiltration Over Alternative Protocol",
    "T1041": "Exfiltration Over C2 Channel",
}

RETRIEVAL_QUERIES = [
    ("many failed SSH password attempts from one IP", {"T1110", "T1110.001"}),
    ("one IP trying many different usernames", {"T1110", "T1110.003"}),
    ("connection attempts to many ports on a host", {"T1046", "T1595.001"}),
    ("SQL injection payload in web request", {"T1190"}),
    ("sudo to root shell after login", {"T1548.003", "T1548"}),
    ("large outbound data transfer to external server", {"T1048", "T1041"}),
]
