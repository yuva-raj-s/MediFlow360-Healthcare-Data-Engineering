# LOG-002 — Azure Cost Overrun: The Forgotten Cluster
**Log ID**: LOG-002 | **Date**: 2024-02-17/18 | **Author**: Sneha Iyer (PM-001)
**Status**: ✅ Resolved + Policy enforced

---

## What Happened

On Friday, February 16, Arjun was debugging the claims API pagination issue on the Databricks Community Edition cluster. He ran several large test jobs late in the evening (~18:30 IST) and forgot to terminate the cluster before logging off for the weekend.

The Community Edition cluster continued running with his session active. Over Saturday and Sunday, the free credit meter consumed **$47.23 USD** of the Azure $200 trial balance — leaving only **$152.77** for the remaining 4+ months of the project.

The overrun was discovered Monday morning by Suresh during his routine Azure Cost Management check.

---

## Timeline

| Time | Event |
|------|-------|
| Fri 16 Feb 18:30 | Arjun finishes debugging, logs off Teams without terminating cluster |
| Fri 16 Feb 18:32 | Cluster continues running (no auto-terminate configured at this point) |
| Sat 17 Feb | $22.50 consumed |
| Sun 18 Feb | $24.73 consumed |
| Mon 19 Feb 09:05 | Suresh opens Azure Cost Management, sees $47 spike |
| Mon 19 Feb 09:10 | Suresh terminates cluster, messages Arjun |
| Mon 19 Feb 09:30 | Emergency team standup called by Sneha |

---

## Arjun's Response (Teams, Monday morning)

> **Arjun Patel** [09:11]: *"oh no. oh no no no. I'm so sorry. I was in a rush Friday evening. I didn't check."*

> **Priya Sharma** [09:12]: *"Arjun it's okay. This is why we need auto-terminate. We'll fix the process."*

> **Suresh Kumar** [09:15]: *"I'm setting auto-terminate NOW for all clusters. 30 minutes idle timeout. Non-negotiable from today."*

> **Sneha Iyer** [09:20]: *"We have $152 left. We need to be very careful. I'm setting a $130 budget alert as our early warning."*

---

## Financial Impact

| Item | Cost |
|------|------|
| Remaining credit before incident | $199.47 |
| Consumed over weekend | $47.23 |
| Remaining after incident | $152.24 |
| Original projected spend to go-live | $85.00 |
| Revised projected spend (post incident) | $85.00 |
| Safety margin remaining | $67.24 |

*Note: Despite the scare, the project remains within budget. The auto-terminate policy effectively prevents recurrence.*

---

## Resolution

### Immediate (OPS-001, Feb 19)
- Set auto-terminate: **30 minutes idle** on ALL clusters (non-negotiable)
- Set Azure Budget Alert at **$130** (warning) and **$175** (critical)

### Policy Added to Onboarding Guide
```
MANDATORY CLUSTER POLICY (added to 04_onboarding/Databricks_Community_Setup.md):
- Auto-terminate: 30 min (always enabled)
- Before logging off: Confirm cluster shows "Terminated" status
- Friday evenings: Suresh does cluster audit at 19:00 IST
- Weekend check: OPS-001 checks Azure Cost Management every Saturday morning
```

### Team Communication
Sneha sent a blameless post-mortem summary to the full team. Arjun was NOT penalised — the process gap was the root cause, not individual negligence.

---

## Lessons Learned
1. **Auto-terminate is not optional** — it should be set at cluster creation, enforced in onboarding
2. **Cost alerts must be set up on Day 1** — not "when we remember to"
3. **Blameless culture**: the incident was handled professionally; no blame, just process fixes

---
*MRHS Confidential | LOG-002 Cost Overrun Log | 2024-02-19*
