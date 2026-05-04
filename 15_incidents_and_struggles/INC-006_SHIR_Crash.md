# INC-006: Windows Update Rebooted SHIR
**Severity**: P2 | **Status**: Closed
**Author**: Arjun Patel (DE-002)

**What Happened**:
Hospital IT enabled automatic Windows Updates on the VM hosting the SHIR. The VM rebooted at 02:00 AM, right in the middle of our pipeline run.
Pipeline failed. 6-hour gap in patient data.

**Resolution**:
We requested IT to disable auto-updates on the SHIR node. Set up ADF retry logic (3 retries, 5 min interval) on the Copy Activity.