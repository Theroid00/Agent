# Compromise of SSH Server via Brute Force, Privilege Escalation, and Data Exfiltration

Synthetic-data demonstration; recommendations only.

Severity: critical | Confidence: 0.95

Incident inc-001 details a critical compromise of the SSH server (ssh-src / 10.0.0.10) originating from external IP 203.0.113.75. The attack began with port reconnaissance (T1595.001), followed by brute-force authentication against the deploy user (T1110), unauthorized privilege escalation via sudo to obtain a root shell (T1548.003), and subsequent data exfiltration of approximately 150MB over a non-standard port 4444 to an external destination (T1041). Targeted containment, thorough investigation, and strict preventive controls are required.

## Timeline

- 2026-10-16T20:37:10Z: T1595.001 — External port scanning activity targeting the SSH server from source IP 203.0.113.75.
- 2026-10-16T20:47:10Z: T1110 — Brute-force password guessing leading to successful SSH authentication for the deploy user from 203.0.113.75.
- 2026-10-16T20:54:10Z: T1548.003 — Post-exploitation root shell escalation via sudo by the deploy user.
- 2026-10-16T21:07:10Z: T1041 — Outbound data transfer exfiltrating 150MB of data to external IP 198.51.100.200 on port 4444.

## Recommended actions

- P1: Block attacker IP address on perimeter firewall (target: 203.0.113.75)

```text
iptables -A INPUT -s 203.0.113.75 -j DROP
```

- P1: Isolate compromised host from internal network (target: ssh-srv (10.0.0.10))

```text
ip link set eth0 down
```

- P1: Terminate active sessions and disable compromised deploy user account temporarily (target: deploy)

```text
pkill -u deploy && usermod -L deploy
```


## ATT&CK mitigations

- M1056 Pre-compromise → T1595.001
- M1018 User Account Management → T1110
- M1036 Account Use Policies → T1110
- M1032 Multi-factor Authentication → T1110
- M1027 Password Policies → T1110
- M1022 Restrict File and Directory Permissions → T1548.003
- M1028 Operating System Configuration → T1548.003
- M1026 Privileged Account Management → T1548.003
- M1031 Network Intrusion Prevention → T1041
- M1057 Data Loss Prevention → T1041

Evaluation: this incident covers 5 of the A6 stages.
