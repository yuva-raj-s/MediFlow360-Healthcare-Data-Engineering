# INC-002: SHIR Connection Timeout
**Severity**: P3 | **Status**: Closed
**Author**: Suresh Kumar (OPS-001)

**What Happened**:
ADF Pipeline `PL_Ingest_Patients` failed to connect to MySQL HIS via the Self-Hosted IR. Error: `SocketException: Connection timed out`.
IT Infrastructure had applied a network security group patch that closed outbound port 443 from the SHIR VM.

**Resolution**:
IT Infra whitelisted the ADF Azure URLs on the firewall.