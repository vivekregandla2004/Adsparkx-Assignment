# Cloud Access Guide

## Overview

This guide covers accessing, configuring, and managing cloud services on the Example Platform. All cloud features are available on Professional and Enterprise plans.

---

## Getting Started with Cloud Access

### 1. Provisioning Your Cloud Environment

After subscribing to a cloud-enabled plan:
1. Navigate to **Dashboard → Cloud → Provision Environment**
2. Select your preferred cloud region (US-East, EU-West, AP-Southeast)
3. Choose the compute tier: Shared, Dedicated, or High-Performance
4. Click **Provision** — environment setup takes 3–5 minutes

Your environment URL will be: `https://[your-org].cloud.example.com`

### 2. Cloud Roles and Permissions

| Role | Capabilities |
|------|-------------|
| `cloud:viewer` | Read-only access to cloud resources |
| `cloud:operator` | Deploy, start, stop services |
| `cloud:admin` | Full access including network config, IAM |
| `cloud:billing` | View and manage cloud spend |

Roles are assigned in **Admin Panel → Team → [User] → Cloud Roles**.

---

## Connectivity

### VPN Access (Enterprise)

Enterprise customers receive dedicated VPN access to their cloud environment:

1. Download the VPN client from: `https://vpn.example.com/client`
2. Use the configuration file provided in **Cloud → Security → VPN Profiles**
3. Authenticate with your platform credentials + 2FA
4. Supported protocols: WireGuard (recommended), OpenVPN

### Direct IP Allowlisting

For service-to-service connections:
1. Go to **Cloud → Network → Firewall Rules**
2. Add the source IP or CIDR range
3. Select the target service and port
4. Rules propagate within 2 minutes

### Private Link / VPC Peering

Available for Enterprise plans with dedicated cloud environments:
- Supports AWS VPC Peering, Azure Private Link, GCP VPC Network Peering
- Contact enterprise@example.com to configure

---

## Storage

### Object Storage

Access via HTTPS or S3-compatible API:
- **Endpoint:** `https://storage.cloud.example.com`
- **Protocol:** S3-compatible (use any S3 client)
- **Authentication:** Access Key + Secret Key from **Cloud → Storage → Access Keys**

```bash
# AWS CLI example
aws s3 ls s3://your-bucket --endpoint-url https://storage.cloud.example.com \
  --aws-access-key-id YOUR_ACCESS_KEY \
  --aws-secret-access-key YOUR_SECRET_KEY
```

### File Storage (NFS/SMB)

Persistent file storage for stateful workloads:
- **NFS Mount:** `mount -t nfs cloud-nfs.example.com:/vol/your-org /mnt/data`
- **SMB Mount:** `\\cloud-smb.example.com\your-org` (Windows)

---

## Compute

### Starting / Stopping Services

Via Dashboard:
1. **Cloud → Services → [Your Service]**
2. Click **Start** or **Stop**

Via API:
```bash
curl -X POST https://api.example.com/v1/cloud/services/{service_id}/start \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Autoscaling Configuration

```json
{
  "min_instances": 1,
  "max_instances": 10,
  "scale_up_threshold_cpu": 70,
  "scale_down_threshold_cpu": 30,
  "cooldown_seconds": 300
}
```

Configure at: **Cloud → Services → [Service] → Autoscaling**

---

## Monitoring and Logging

### Metrics Dashboard

Real-time metrics available at **Cloud → Monitoring**:
- CPU, Memory, Disk, Network I/O
- Custom application metrics via our Metrics API
- Retention: 30 days (standard), 1 year (enterprise)

### Log Streaming

Stream logs to your SIEM or log management platform:
- **Supported integrations:** Splunk, Datadog, Elastic Stack, Sumo Logic
- **Format:** JSON or syslog
- Configure at: **Cloud → Logging → Log Destinations**

### Alerts

Set up alerts in **Cloud → Monitoring → Alerts**:
- Threshold-based (e.g., CPU > 80% for 5 minutes)
- Anomaly detection (ML-based, Enterprise)
- Notification channels: Email, Slack, PagerDuty, Webhook

---

## Troubleshooting Cloud Access Issues

### Cannot Connect to Cloud Environment

1. Verify your plan includes cloud access (Professional or Enterprise)
2. Check the service status page: `status.example.com`
3. Confirm your IP is not blocked by firewall rules
4. Ensure the VPN client is connected (Enterprise)
5. Check your `cloud:viewer` or higher role is assigned

### Service Stuck in "Starting" State

1. Wait 5 minutes — cold starts can take time on dedicated compute
2. Check service logs: **Cloud → Services → [Service] → Logs**
3. If still stuck after 10 minutes, use **Force Restart** option
4. Contact support if force restart fails

### High Latency / Slow Performance

1. Check the Monitoring dashboard for resource saturation
2. Review autoscaling settings — you may need higher limits
3. Consider switching to a region geographically closer to your users
4. For persistent issues, open a support ticket with monitoring data attached

---

## Cloud Cost Management

- View current spend: **Cloud → Billing → Usage Dashboard**
- Set spend alerts: **Cloud → Billing → Budget Alerts**
- Cost breakdown by service, region, and time period
- Export billing data as CSV for internal reporting

Contact billing@example.com for unexpected charges or billing disputes related to cloud services.
