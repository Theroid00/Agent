# Compromise of SSH Server via Port Scan, Credential Access, Privilege Escalation, and Data Exfiltration

Synthetic-data demonstration; recommendations only.

Severity: critical | Confidence: 1.0

Critical multi-stage compromise of the SSH server originating from external IP 203.0.113.130, involving port scanning, credential guessing, successful SSH access using the 'deploy' account, privilege escalation to root via sudo, and data exfiltration to an external IP.

## Timeline

- 2026-10-16T20:43:06Z: T1595.001 — External source IP 203.0.113.130 performed sequential port scanning against the SSH server.
- 2026-10-16T20:53:06Z: T1110.001 — Initial failed password attempts from external IP 203.0.113.130 for user deploy.
- 2026-10-16T20:58:06Z: T1021.004 — Successful SSH session established after credential failures from an external IP address.
- 2026-10-16T21:00:06Z: T1548.003 — User deploy spawned /bin/bash as root via sudo following an externally sourced login session.
- 2026-10-16T21:13:06Z: T1041 — Large outbound transfer of 150,000,000 bytes to external suspicious IP 198.51.100.200 on port 4444.

## Recommended actions

- P1: Isolate SSH server and block attacker IP (target: 203.0.113.130)

```text
iptables -A INPUT -s 203.0.113.130 -j DROP
```

- P1: Block outbound exfiltration destination (target: 198.51.100.200)

```text
iptables -A OUTPUT -d 198.51.100.200 -j DROP
```

- P1: Terminate active compromised sessions (target: ssh-srv)

```text
pkill -u deploy
```


## ATT&CK mitigations

- M1056 Pre-compromise → T1595.001
- M1051 Update Software → T1110.001
- M1032 Multi-factor Authentication → T1110.001
- M1027 Password Policies → T1110.001
- M1036 Account Use Policies → T1110.001
- M1042 Disable or Remove Feature or Program → T1021.004
- M1032 Multi-factor Authentication → T1021.004
- M1018 User Account Management → T1021.004
- M1022 Restrict File and Directory Permissions → T1548.003
- M1028 Operating System Configuration → T1548.003
- M1026 Privileged Account Management → T1548.003
- M1031 Network Intrusion Prevention → T1041
- M1057 Data Loss Prevention → T1041

Evaluation: this incident covers 5 of the A6 stages.
