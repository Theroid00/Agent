# External Reconnaissance, Compromise, Privilege Escalation, and Data Exfiltration

Synthetic-data demonstration; recommendations only.

Severity: critical | Confidence: 0.95

Linked chain of activity showing scanning, brute force, successful login, root shell, and outbound transfer originating from source IP 203.0.113.75 against ssh-srv.

## Timeline

- 2026-10-16T20:37:10Z: T1595.001 — Sequential port connection attempts from external IP 203.0.113.75 against ssh-srv.
- 2026-10-16T20:47:10Z: T1110.001 — Password guessing attempts against the deploy account from external IP 203.0.113.75.
- 2026-10-16T20:52:10Z: T1078 — Successful SSH authentication for user deploy from external IP 203.0.113.75.
- 2026-10-16T20:54:10Z: T1548.003 — User deploy invoked root shell via sudo for privilege escalation.
- 2026-10-16T21:07:10Z: T1041 — Large data transfer from ssh-srv to external IP on non-standard port 4444.

## Recommended actions

- P1: Isolate host from network (target: ssh-srv)

```text
ip link set eth0 down
```

- P1: Block attacker IP (target: 203.0.113.75)

```text
iptables -A INPUT -s 203.0.113.75 -j DROP
```

- P1: Terminate active sessions for user deploy (target: deploy)

```text
pkill -u deploy
```


## ATT&CK mitigations

- M1056 Pre-compromise → T1595.001
- M1051 Update Software → T1110.001
- M1032 Multi-factor Authentication → T1110.001
- M1027 Password Policies → T1110.001
- M1036 Account Use Policies → T1110.001
- M1027 Password Policies → T1078
- M1018 User Account Management → T1078
- M1026 Privileged Account Management → T1078
- M1032 Multi-factor Authentication → T1078
- M1013 Application Developer Guidance → T1078
- M1017 User Training → T1078
- M1015 Active Directory Configuration → T1078
- M1036 Account Use Policies → T1078
- M1022 Restrict File and Directory Permissions → T1548.003
- M1028 Operating System Configuration → T1548.003
- M1026 Privileged Account Management → T1548.003
- M1031 Network Intrusion Prevention → T1041
- M1057 Data Loss Prevention → T1041

Evaluation: this incident covers 5 of the A6 stages.
