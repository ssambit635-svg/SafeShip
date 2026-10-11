# SafeShip — Proposed Tech Stack

Status: **Day 1 recommendation, not an installed or tested environment.** Confirm this stack before implementation. Prefer one tool per job and pinned, supported versions; avoid `latest` in deployment artifacts.

## Application and local development

| Component | Choice | Why / what to learn |
| --- | --- | --- |
| Language | Python 3.12 | Keep the workload small so most effort goes into cloud operations; learn environments, dependencies, and exceptions |
| API | FastAPI + Uvicorn | Simple HTTP endpoints, input validation, and generated API documentation |
| Database | PostgreSQL 16 | Durable relational storage; learn SQL, transactions, constraints, and connections |
| Database access | Psycopg 3 with parameterized SQL | A small schema does not need an ORM; explicit SQL makes data behavior visible |
| Schema setup | Versioned SQL files + tracked, explicit migration step | Start with one orders table; avoid running migrations independently in both app slots |
| Tests | pytest + HTTPX | Endpoint tests plus integration tests against a real disposable PostgreSQL database |
| Code checks | Ruff | Fast linting and formatting with a small configuration |
| Packaging | Docker + Docker Compose v2 | Reproducible app image; local API + database startup and persistent volumes |

If JavaScript is already your stronger language, Node.js + Express is a valid alternative. The delivery architecture stays the same. Python is a proposed default, not a prerequisite for this project.

## AWS and host infrastructure

| Component | Choice | Purpose |
| --- | --- | --- |
| Infrastructure as Code | Terraform | Declare networking, EC2, ECR, IAM, S3, SSM-related configuration, and CloudWatch resources; inspect plans before applying |
| IaC state | Private encrypted S3 backend with supported state locking | Keep shared state durable and access-controlled; bootstrap the backend separately and never commit state |
| Compute | One EC2 instance, Ubuntu Server 24.04 LTS | Learn Linux directly; select instance capacity after considering both app slots, DB, and monitoring |
| Container runtime | Docker Engine + Compose v2 | Run blue/green app slots and a separate persistent PostgreSQL service |
| Reverse proxy | Host-installed Nginx | One client entry point; upstream switch plus configuration validation and graceful reload |
| Host services | systemd | Manage Nginx, boot behavior, monitoring, and scheduled operational jobs |
| Container registry | Amazon ECR | Private app image storage; tag by Git SHA and deploy by immutable digest |
| Remote administration | AWS Systems Manager / SSM Run Command | Execute approved deployments without an inbound SSH port; capture and check command status |
| AWS identities | IAM roles + GitHub OIDC | Short-lived CI credentials and a separate EC2 instance profile |
| Runtime secret | SSM Parameter Store SecureString | Store the DB secret outside Git/images; retrieve on the host with scoped permissions and no secret logging |
| Logs and monitoring | CloudWatch Agent, Logs, metrics, alarms, dashboard | Ship app/Nginx/system logs; monitor CPU, memory/disk, errors, and backup failures |
| Backup storage | Private encrypted S3 bucket | Store database dumps separately from the host, with limited access and retention rules |

OpenTofu is an alternative to Terraform, not another tool to learn in parallel. This plan selects Terraform for consistency.

### IAM separation to implement

- **GitHub deployment role:** trust only the intended repository and main-branch OIDC subject (or a carefully configured protected environment); publish to the designated ECR repository and invoke/check the approved SSM deployment target/document. No general administrator policy.
- **EC2 instance profile:** only required SSM agent access, ECR pulls, log/metric writes, secret reads, and access to the designated backup location.
- **Infrastructure provisioning identity:** separate from routine deployment; review its broader permissions and Terraform plan. OIDC is also required if infrastructure provisioning is later automated in Actions.
- An SSM deployment role can effectively control the host. Scope the command document and targets rather than treating “no SSH” as sufficient security.

## Delivery, verification, and recovery

| Component | Choice | Purpose |
| --- | --- | --- |
| CI/CD | GitHub Actions | PR checks; main-branch test/build/scan/publish/deploy workflow with concurrency control |
| Image build | Docker BuildKit / Buildx | Build a reproducible image once; promote the same scanned artifact |
| Security scan | Trivy | Scan the image and repository configuration; define a blocking severity policy and documented exceptions |
| Deployment logic | Bash + curl + Docker CLI | Transparent blue-green state machine with locking, timeouts, cleanup, and explicit rollback |
| Script checks | ShellCheck + failure-drill tests | Catch shell mistakes and prove behavior under unhealthy candidates and failed switches |
| Load test | k6 | Measure latency, error rate, and behavior during deployment; save real results |
| Backup | PostgreSQL `pg_dump` custom format + AWS CLI | Scheduled logical backups to S3; mark success only after upload succeeds |
| Restore verification | `pg_restore` into an isolated PostgreSQL database | Check schema/records and measure recovery time; successful upload alone is not proof of recoverability |

### Deployment contract

- Use fixed, loopback-bound blue/green app ports; clients can reach them only through Nginx.
- Keep database lifecycle separate from slot deployment. Never remove its volume during a release or run a blanket Compose teardown with volume deletion.
- Serialize deployments both in GitHub Actions and on the server.
- Validate readiness directly, then verify the selected version through Nginx after switching.
- Actions must wait for the SSM command outcome and fail when deployment fails—even if rollback succeeds.
- Keep at least the active and previous known-good image available; retention/cleanup must not remove rollback dependencies.
- Test host restart recovery and state reconciliation, not just the happy-path deployment.

### Monitoring and recovery definitions

- **Readiness:** can this instance serve the expected workload now, including its database dependency?
- **Release verification:** does the new version behave correctly through the real proxy path?
- **RTO (recovery time objective):** the target time to restore service. Measure actual restore/recovery duration separately; do not claim a target was achieved without testing the full defined scope.
- **RPO (recovery point objective):** the target maximum data-loss window. Backup age and successful backup frequency determine the demonstrated window; daily dumps are not point-in-time recovery.
- EC2 CPU metrics alone do not provide application errors, memory, or disk utilization. Configure log metric filters/app metrics and the CloudWatch Agent explicitly.
- CloudWatch alarms provide detection/notification. Automatic release rollback comes from the deployment checks unless a separate alarm-driven mechanism is implemented.

## Deliberately not included in the first 15 days

Kubernetes/EKS, ECS, multiple hosts/AZs, an ALB, RDS, a frontend, real payment flows, and a large observability stack. These are potential follow-ups, not requirements for proving this learning project's release and recovery behavior.

Before implementation: lock dependency versions, pin CI actions to reviewed commit SHAs, select the AWS region and compatible host/image architecture, review costs, and agree on demo access/TLS requirements. Neither credentials nor secret values belong in these documents.
