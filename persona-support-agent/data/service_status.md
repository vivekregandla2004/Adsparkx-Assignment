# Service Status and Incident Management Guide

## Overview

This document explains how to check service status, understand incident severity levels, and what to expect during outages or degraded performance.

---

## Checking Service Status

### Status Page

Real-time service status is available at: **https://status.example.com**

The status page shows the health of all platform components:
- **API Gateway** — Core API availability
- **Authentication Service** — Login and token issuance
- **Cloud Services** — Compute, storage, networking
- **Web Dashboard** — Browser-based UI
- **Webhook Delivery** — Outbound event delivery
- **Email Notifications** — System email delivery
- **Third-Party Integrations** — Slack, Salesforce, etc.

### Status Indicators

| Status | Meaning |
|--------|---------|
| 🟢 Operational | All systems running normally |
| 🟡 Degraded Performance | Service works but slower than normal |
| 🟠 Partial Outage | Some users or regions affected |
| 🔴 Major Outage | Service unavailable for most users |
| 🔧 Under Maintenance | Planned maintenance in progress |

### Subscribe to Status Notifications

1. Visit `https://status.example.com`
2. Click **Subscribe to Updates**
3. Choose: Email, SMS, Slack webhook, RSS feed
4. Select which components to monitor
5. You will receive notifications when status changes

---

## Incident Severity Levels

### SEV-1 (Critical)
- **Definition:** Complete service unavailability affecting all or most users
- **Response time:** 15 minutes
- **Resolution target:** 4 hours
- **Communication:** Status page updated every 30 minutes; email notifications sent
- **Examples:** Authentication down, API Gateway not responding, data loss

### SEV-2 (High)
- **Definition:** Significant degradation affecting many users or a critical feature
- **Response time:** 30 minutes
- **Resolution target:** 8 hours
- **Communication:** Status page updated every hour
- **Examples:** Slow API responses (>10s), some integrations failing, partial cloud unavailability

### SEV-3 (Medium)
- **Definition:** Limited degradation affecting a subset of users or non-critical features
- **Response time:** 2 hours
- **Resolution target:** 24 hours
- **Communication:** Status page updated when significant changes occur
- **Examples:** One region slow, specific integration degraded, minor UI bugs

### SEV-4 (Low)
- **Definition:** Minor cosmetic or non-functional issues with minimal user impact
- **Response time:** Next business day
- **Resolution target:** 72 hours
- **Examples:** UI display issues, minor documentation errors, non-critical feature bugs

---

## Planned Maintenance

### Maintenance Windows

Planned maintenance typically occurs during:
- **US/CA customers:** Sundays, 2:00 AM – 6:00 AM EST
- **EU customers:** Sundays, 2:00 AM – 6:00 AM CET
- **AP customers:** Sundays, 2:00 AM – 6:00 AM JST

### Maintenance Notifications

You will receive email notifications:
- **72 hours before** major maintenance (>1 hour impact)
- **24 hours before** minor maintenance (<30 minute impact)
- **Immediate notification** if maintenance extends beyond the scheduled window

### Emergency Maintenance

Unplanned emergency maintenance may occur to:
- Apply critical security patches
- Prevent imminent data loss
- Resolve an ongoing SEV-1 incident

Emergency maintenance notifications are sent via email and posted to the status page as soon as possible.

---

## Service Level Agreements (SLA)

| Plan | Uptime Guarantee | Compensation |
|------|-----------------|-------------|
| Starter | No SLA | No credit |
| Professional | 99.9% (8.7 hours downtime/year) | Service credits |
| Enterprise | 99.99% (52 minutes downtime/year) | Service credits + financial |

### SLA Calculation

```
Uptime % = ((Total Minutes - Downtime Minutes) / Total Minutes) × 100
```

Scheduled maintenance windows are excluded from SLA calculations.

---

## Reporting an Issue

If you observe an issue not reflected on the status page:

1. Visit `https://status.example.com/report`
2. Describe the issue: component affected, error message, time of occurrence
3. Our monitoring team reviews reports and will update the status page within 15 minutes if confirmed

Or contact support directly at support@example.com.

---

## Post-Incident Reports (PIR)

After any SEV-1 or SEV-2 incident, we publish a Post-Incident Report within 5 business days. PIRs include:
- Timeline of events
- Root cause analysis
- Impact scope
- Steps taken to resolve
- Preventative measures for the future

PIRs are published at `https://status.example.com/incidents`.
