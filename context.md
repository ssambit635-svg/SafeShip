# SafeShip — Project Context

## 1. Project in one sentence

Build a small orders API, then prove that you can deploy new Docker versions on AWS safely, detect failures, keep the previous version available, and recover data from a verified backup.

**The API is the practice workload. Deployment safety and operations are the actual project.**

## 2. Learning agreement

- This is a learner-owned, 15-day second cloud project—not an exercise in generating a complete system at once.
- Explain each component and its trade-offs before implementing it.
- Work in small steps: understand → implement → test → deliberately break → explain the result.
- Each day should leave a small working artifact and evidence of what was tested.
- Do not provision paid resources or run destructive recovery experiments without an explicit decision from the learner.
- Keep AWS credentials, database passwords, tokens, and sensitive Terraform state out of Git.

## 3. What the application does

Initial API contract (proposed):

- `POST /orders`: create a fake order with an item name and a positive quantity; return its generated ID and creation time.
- `GET /orders/{id}`: read an order; return 404 if absent.
- `GET /orders`: list orders with a bounded page size.
- `GET /health/live`: confirm the application process can respond.
- `GET /health/ready`: confirm the application can reach PostgreSQL and use the expected schema; return non-200 if not ready.
- `GET /version`: return the deployed Git commit/version for demonstration and troubleshooting.

PostgreSQL stores orders outside the replaceable app containers. No real customers, payments, or sensitive data. Authentication, a frontend, and business complexity are outside the initial scope. The demo is not a production-ready public orders service.

## 4. Architecture

```text
GitHub push / pull request
  → GitHub Actions: tests → Docker build → vulnerability scan

Approved main-branch deployment, after checks pass
  → GitHub OIDC: temporary AWS credentials
  → ECR: publish image, record its immutable digest
  → SSM Run Command: invoke the EC2 deployment script
  → EC2: start the inactive app slot and check readiness
  → Nginx: switch traffic only when the candidate passes
  → Verify through Nginx; roll back if verification fails

Client → Nginx → active app slot (blue OR green) → PostgreSQL
                  inactive slot used for the next candidate

EC2/application logs → CloudWatch
PostgreSQL logical backup → private S3 bucket → isolated restore test
Terraform → AWS infrastructure, IAM, configuration, and monitoring
```

Initial environment: one Linux EC2 instance runs Nginx, two possible app containers, and one PostgreSQL container with persistent storage. Only Nginx is client-facing. App ports and the database are not publicly exposed. Use SSM for administration rather than opening SSH.

## 5. What “safe deployment” actually means

1. Acquire a deployment lock so two releases cannot change traffic simultaneously.
2. Record the current active slot and image digest; pull the new image by digest.
3. Start the candidate in the inactive slot, leaving the active container untouched.
4. Check the candidate directly with bounded readiness retries and a safe API smoke test.
5. If these checks fail, stop the candidate and report deployment failure. The old version still serves traffic: this is a rejected release, not a traffic switch followed by rollback.
6. If they pass, prepare the Nginx configuration, validate it with `nginx -t`, and switch using a graceful reload. A configuration failure must leave the old route intact.
7. Check the new version through Nginx during a defined observation window. If it fails, restore and reload the previous route, confirm recovery, and report the release as failed.
8. Keep the previous container available for rollback during that window. Record successful deployment state only after verification; clean up old resources carefully afterward.

The first deployment has no previous version to roll back to. Failure must be reported honestly rather than claiming recovery. Automated rollback covers defined checks and a defined observation window—not every bug forever.

### Limits we must understand

- Blue-green aims to avoid deployment-related interruption; it does not guarantee zero downtime.
- One EC2 host is a single point of failure. Host failure, disk exhaustion, or database failure can still cause an outage.
- Both app versions share the same database. An app rollback does **not** undo database writes or schema changes.
- Use backward-compatible schema changes (expand first, remove later). Destructive migrations are outside the initial demo.
- Two app slots temporarily need more memory/CPU. Size and observe the host accordingly.
- A health check cannot prove all business behavior is correct. Tests, smoke checks, logs, and monitoring work together.
- An on-host database volume is persistence, not an independent backup. S3 backups help with recovery, but this is not an HA database design.

## 6. Why this is an effective portfolio project

This is useful for junior cloud/DevOps interviews because it demonstrates a complete path from source code to an operated service, rather than just “I launched an EC2 instance.” Its value comes from verifiable decisions and failure handling—not the number of tools listed.

| Skill | Evidence to produce |
| --- | --- |
| Linux | Service management, least-privilege access, disk/log investigation, reboot behavior |
| Containers | Reproducible image, non-root app process, persistent DB data, local Compose setup |
| AWS/IAM | Infrastructure code, scoped roles, OIDC, ECR, SSM, and no long-lived CI keys |
| Delivery | A passing release and a deliberately rejected or rolled-back release |
| Operations | Logs, useful CloudWatch alarms/dashboard, load-test results |
| Recovery | A backup restored into an isolated DB, validation, and measured recovery time |
| Engineering judgment | Clear limitations, costs, runbooks, and an explanation of trade-offs |

It is a strong learning/demo project, not evidence of production-scale experience by itself. Only put measured results on a CV; do not invent uptime, throughput, or recovery numbers.

## 7. Fifteen-day learning roadmap

Plan for focused daily sessions; this is a sequence, not a guarantee. If Linux, Docker, or IAM is new, extend the schedule rather than skip understanding.

| Day | Focus | Exit check / artifact |
| --- | --- | --- |
| 1 | Understand the system, scope, and stack | Explain the request path and release path; review these documents |
| 2 | HTTP, Python API, validation, tests | Create/read endpoints work locally; invalid input and 404 tested |
| 3 | PostgreSQL and schema basics | Orders survive app restart; database integration tests pass |
| 4 | Docker and Docker Compose | Fresh clone can run API + DB; non-root app image; no embedded secrets |
| 5 | Linux operations | Practice users/permissions, processes, systemd, disk usage, logs, and networking |
| 6 | AWS and Terraform foundations | Choose region/budget, plan networking/roles/state, review infrastructure plan before applying |
| 7 | EC2, ECR, SSM, host bootstrap | Reach host through SSM; Docker/Nginx services survive reboot; ports restricted |
| 8 | CI and image security | PR tests/build/scan pass; define blocking severity and exception policy |
| 9 | OIDC and delivery to EC2 | Main-only AWS trust; publish a digest; Actions waits for SSM result and propagates failure |
| 10 | Blue-green script and Nginx | Manual healthy release switches slots; locking/state handling tested |
| 11 | Failure and rollback drills | Candidate rejection + post-switch rollback proven; old version/data remain available |
| 12 | CloudWatch and host operations | Dashboard, error/CPU/disk alarms, retention, and safe image/log cleanup |
| 13 | k6 load test | Record request rate, latency, errors, and behavior during a release |
| 14 | Backup and restore | Schedule backup to S3; restore separately; validate data and measure recovery time |
| 15 | Rehearsal, documentation, demo | Record release/failure/recovery story; review security; document teardown |

## 8. Final demo acceptance criteria

- Show a code push triggering tests, image build/scan, image publication, and deployment with no static AWS keys.
- Show the previous version responding while a healthy candidate starts, then show the new version through Nginx.
- Deploy a controlled readiness-broken version without disabling security controls. Prove traffic stays on the old version and CI reports failure.
- Also demonstrate a controlled post-switch verification failure if claiming actual automatic rollback; confirm traffic returns to the previous version.
- Show request errors and host metrics in CloudWatch with deployment timestamps.
- Restore a backup into a separate database, check schema and known order records, and record elapsed time and backup age. Never overwrite the demo database for this drill.
- Include the architecture, setup/teardown instructions, limitations, incident/rollback runbook, and actual measured results in the repository.

## 9. Cost and security guardrails

- Set an AWS Budget and alerts before provisioning; alerts are not a hard spending cap.
- Review EC2, EBS, public IPv4, S3, ECR, and CloudWatch costs; do not assume a free tier applies.
- Avoid unnecessary NAT gateways/load balancers in this single-host learning scope; understand the resulting architecture limitations.
- Restrict demo access to the learner where feasible; require HTTPS before sending credentials or real data. Plain HTTP, if used initially, is restricted and fake-data-only.
- Keep PostgreSQL private, block public S3 access, scope IAM permissions, and bound log/image/backup retention.
- Tag resources and maintain a teardown checklist, including retained volumes, snapshots, backups, and Terraform state resources.

## 10. Current handoff

**Status:** Day 1 planning only. No API, infrastructure, pipeline, or AWS deployment has been implemented or verified.

**Next:** Confirm the proposed language/stack, available daily study time, local Docker support, AWS account/region, and spending limit. Do not share credentials in chat. Then start Day 2 with the smallest API and its tests.

At the end of each day, record: what was built, what you can now explain, commands/tests run, evidence, blockers, and the next step.
