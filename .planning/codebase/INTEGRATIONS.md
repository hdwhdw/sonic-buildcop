# External Integrations

**Analysis Date:** 2025-07-17

## Overview

This is a build system repository (SONiC buildimage). It does not directly call external APIs at runtime. Instead, it **builds** a network operating system whose components integrate with various external services and protocols. Integrations fall into two categories:

1. **Build-time integrations** — services used during the build process (CI/CD, package registries, Docker registries)
2. **Runtime integrations** — services/protocols embedded in the built SONiC images

## Build-Time APIs & External Services

**Azure DevOps Pipelines:**
- Primary CI/CD system for building and testing SONiC images
- Pipeline config: `sonic-buildimage/azure-pipelines.yml`
- Pipeline templates: `sonic-buildimage/.azure-pipelines/` (~30+ YAML files)
- Agent pools: `sonicso1ES-amd64`, `sonicso1ES-arm64`, `sonicso1ES-armhf`, `sonictest`, `sonic-ubuntu-1c`
- Pipeline name pattern: `$(TeamProject)_$(Build.DefinitionName)_$(SourceBranchName)_$(Date:yyyyMMdd)$(Rev:.r)`
- Triggers: Push to `master` or `202???` branches; PRs to same branches
- External repo reference: `sonic-net/sonic-mgmt` (GitHub, for test templates)

**GitHub Actions:**
- Secondary CI for security scanning and repository management
- Workflows: `sonic-buildimage/.github/workflows/`
  - `semgrep.yml` — Semgrep static analysis (runs on `ubuntu-latest` with `returntocorp/semgrep` container)
  - `codeql-analysis.yml` — GitHub CodeQL scanning (Python language)
  - `automerge.yml`, `automerge_scan.yml` — Automated PR merging
  - `label.yml` — Automated labeling
  - `pr_cherrypick_prestep.yml`, `pr_cherrypick_poststep.yml` — Cherry-pick automation
  - `protect-file.yml` — File protection

**Docker Container Registry:**
- Configurable via `DEFAULT_CONTAINER_REGISTRY` variable
- Used in all `Dockerfile.j2` templates (e.g., `sonic-buildimage/sonic-slave-bookworm/Dockerfile.j2`)
- Base images: `debian:bookworm`, `debian:trixie`, `multiarch/qemu-user-static`
- Push script: `sonic-buildimage/push_docker.sh` — pushes built images to configured registry with `docker login`
- Accepts `REGISTRY_SERVER`, `REGISTRY_PORT`, `REGISTRY_USERNAME`, `REGISTRY_PASSWD` parameters

**Debian Package Repositories:**
- Standard Debian mirrors for bookworm/trixie/bullseye/buster package installation
- Configured per-architecture: `sonic-buildimage/sonic-slave-*/sources.list.*`
- pip.conf for Python packages: `sonic-buildimage/sonic-slave-*/pip.conf`

**GitHub Repositories (Submodules):**
- 48+ git submodules pulled from `github.com/sonic-net/`, `github.com/p4lang/`, `github.com/Mellanox/`, `github.com/Marvell-switching/`, etc.
- Full list: `sonic-buildimage/.gitmodules`
- Key submodule URLs:
  - `https://github.com/sonic-net/sonic-swss-common`
  - `https://github.com/sonic-net/sonic-swss`
  - `https://github.com/sonic-net/sonic-sairedis`
  - `https://github.com/sonic-net/sonic-frr.git` (branch: `frr-10.4.1`)
  - `https://github.com/sonic-net/sonic-utilities`
  - `https://github.com/sonic-net/sonic-gnmi.git`
  - `https://github.com/sonic-net/sonic-linux-kernel`

**Elastictest (Test Infrastructure):**
- Variable group: `SONiC-Elastictest` (referenced in `sonic-buildimage/azure-pipelines.yml`, Test stage)
- Used for KVM-based PR testing
- Test templates from `sonic-net/sonic-mgmt` repository

## Data Storage (Runtime — Built into SONiC Images)

**Databases:**
- **Redis** — Central data store for all SONiC state
  - Container: `sonic-buildimage/dockers/docker-database/`
  - Config template: `sonic-buildimage/dockers/docker-database/database_config.json.j2`
  - Multi-database config: `sonic-buildimage/dockers/docker-database/multi_database_config.json.j2`
  - Default port: `6379` (chassis instances: `6381 + DPU_ID`)
  - Configured with 100 databases, keyspace notifications enabled (`AKE`), Unix socket at `redis.sock`
  - Multiple logical databases: APPL_DB, ASIC_DB, CONFIG_DB, STATE_DB, COUNTERS_DB, CHASSIS_APP_DB, etc.
  - Client libraries: `redis-py` (Python), `go-redis` (Go), `hiredis` (C), `swss-common` crate (Rust)
  - Init script: `sonic-buildimage/dockers/docker-database/docker-database-init.sh`
  - Supports chassis/VoQ topology with `redis_chassis` instances

**File Storage:**
- Local filesystem only (embedded Linux)
- SquashFS root filesystem: `fs.squashfs`
- Docker filesystem: `dockerfs.tar.gz`
- Configuration stored at `/etc/sonic/` on target device

**Caching (Build-time):**
- DPKG caching framework: `sonic-buildimage/Makefile.cache`
- Methods: `none`, `cache`, `rcache` (read-cache), `wcache` (write-cache), `rwcache` (read-write)
- Cache source configurable via `SONIC_DPKG_CACHE_SOURCE`

## Runtime Network Protocols & Interfaces

**gNMI (gRPC Network Management Interface):**
- Implementation: `sonic-buildimage/src/sonic-gnmi/` (Go)
- Docker container: `sonic-buildimage/dockers/docker-sonic-gnmi/`
- Dependencies: `github.com/openconfig/gnmi v0.14.1`, `github.com/openconfig/gnoi v0.3.0`, `github.com/openconfig/gnsi v1.9.0`
- Supports: gNMI Get/Set/Subscribe, gNOI operations, gNSI security
- Config options: `ENABLE_TRANSLIB_WRITE`, `ENABLE_NATIVE_WRITE`, `ENABLE_DIALOUT`

**SNMP:**
- Container: `sonic-buildimage/dockers/docker-snmp/`
- Agent: `sonic-buildimage/src/sonic-snmpagent/` (Python, wrapping Net-SNMP from `sonic-buildimage/src/snmpd/`)
- Dependencies: `hiredis`, `pyyaml`, `smbus` (installed in Dockerfile)

**REST API:**
- Container: `sonic-buildimage/dockers/docker-sonic-restapi/`
- Source: `sonic-buildimage/src/sonic-restapi/` (C++ with Makefile)
- Feature flag: `INCLUDE_RESTAPI`

**BGP/Routing (FRRouting):**
- Container: `sonic-buildimage/dockers/docker-fpm-frr/`
- Source: `sonic-buildimage/src/sonic-frr/frr/` (submodule, branch `frr-10.4.1`)
- Protocols: BGP, OSPF, IS-IS, MPLS, EVPN, etc.
- Traffic steering scripts: `sonic-buildimage/dockers/docker-fpm-frr/TSA`, `TSB`, `TSC`

**BMP (BGP Monitoring Protocol):**
- Container: `sonic-buildimage/dockers/docker-sonic-bmp/`
- Source: `sonic-buildimage/src/sonic-bmp/`

**LLDP (Link Layer Discovery Protocol):**
- Container: `sonic-buildimage/dockers/docker-lldp/`
- Source: `sonic-buildimage/src/lldpd/`

**DHCP:**
- Relay container: `sonic-buildimage/dockers/docker-dhcp-relay/`
- Server container: `sonic-buildimage/dockers/docker-dhcp-server/`
- Monitor: `sonic-buildimage/src/dhcpmon/`
- Relay source: `sonic-buildimage/src/dhcprelay/`

**sFlow:**
- Source: `sonic-buildimage/src/sflow/`
- Container: `sonic-buildimage/dockers/docker-sflow/`

**STP (Spanning Tree Protocol):**
- Source: `sonic-buildimage/src/sonic-stp/`
- Container: `sonic-buildimage/dockers/docker-stp/`

**RADIUS/TACACS+ Authentication:**
- RADIUS: `sonic-buildimage/src/radius/`
- TACACS+: `sonic-buildimage/src/tacacs/`

**MACsec:**
- Container: `sonic-buildimage/dockers/docker-macsec/`
- WPA Supplicant: `sonic-buildimage/src/wpasupplicant/`

**NAT:**
- Container: `sonic-buildimage/dockers/docker-nat/`

**P4Runtime:**
- Container: `sonic-buildimage/dockers/docker-sonic-p4rt/`
- Source: `sonic-buildimage/src/sonic-p4rt/`

## OpenTelemetry / Observability

**OpenTelemetry:**
- Container: `sonic-buildimage/dockers/docker-sonic-otel/`
- Files: `Dockerfile.j2`, `otel.sh`, `start.sh`, `supervisord.conf`

**Telemetry (Legacy):**
- Container: `sonic-buildimage/dockers/docker-sonic-telemetry/` (separate from gNMI)
- Sidecar: `sonic-buildimage/dockers/docker-telemetry-sidecar/`
- Watchdog: `sonic-buildimage/dockers/docker-telemetry-watchdog/`

**Event Daemon:**
- Container: `sonic-buildimage/dockers/docker-eventd/`
- Source: `sonic-buildimage/src/sonic-eventd/`

**System Health:**
- Source: `sonic-buildimage/src/system-health/`

## Authentication & Identity (Runtime)

**Auth Providers:**
- Local Linux user authentication (default)
- RADIUS: `sonic-buildimage/src/radius/`
- TACACS+: `sonic-buildimage/src/tacacs/`
- 802.1X / PAC (Port Access Control): `sonic-buildimage/src/sonic-pac/`
- WPA Supplicant (MACsec): `sonic-buildimage/src/wpasupplicant/`

**Default Credentials:**
- Username: `admin` (configured in `sonic-buildimage/rules/config` as `DEFAULT_USERNAME`)
- Password: `YourPaSsWoRd` (configured in `sonic-buildimage/rules/config` as `DEFAULT_PASSWORD`)
- Password change enforcement: `CHANGE_DEFAULT_PASSWORD` flag (default: `n`)

## Hardware Abstraction / Vendor Integrations

**SAI (Switch Abstraction Interface):**
- `sonic-buildimage/src/sonic-sairedis/` — Redis-backed SAI implementation
- `sonic-buildimage/src/dash-sai/` — DASH (Disaggregated API for SONiC Hosts) SAI

**Platform Vendor Support:**
- Broadcom: `sonic-buildimage/platform/broadcom/`
- Mellanox/NVIDIA: `sonic-buildimage/platform/mellanox/`
- NVIDIA Bluefield: `sonic-buildimage/platform/nvidia-bluefield/`
- Marvell Prestera: `sonic-buildimage/platform/marvell-prestera/`
- Marvell Teralynx: `sonic-buildimage/platform/marvell-teralynx/`
- Barefoot/Intel: `sonic-buildimage/platform/barefoot/`
- Centec: `sonic-buildimage/platform/centec/`
- Pensando: `sonic-buildimage/platform/pensando/`
- Nokia VS: `sonic-buildimage/platform/nokia-vs/`
- VPP: `sonic-buildimage/platform/vpp/`
- Virtual Switch (VS): `sonic-buildimage/platform/vs/` (testing)
- AlpineVS: `sonic-buildimage/platform/alpinevs/`

**Device Vendors (37+):**
- `sonic-buildimage/device/` contains per-vendor configurations for: Accton, Arista, Broadcom, Celestica, Dell, Delta, Facebook, Juniper, Marvell, Mellanox, Nokia, NVIDIA, Quanta, Supermicro, Wistron, and many more.

## Zero Touch Provisioning (ZTP)

- Source: `sonic-buildimage/src/sonic-ztp/`
- Feature flag: `ENABLE_ZTP`
- Purpose: Automatic device provisioning on first boot

## Kubernetes Integration (Optional)

- Feature flags: `INCLUDE_KUBERNETES`, `INCLUDE_KUBERNETES_MASTER`
- Referenced in: `sonic-buildimage/Makefile.work`
- Container management: `sonic-buildimage/src/sonic-ctrmgrd/` (Python), `sonic-buildimage/src/sonic-ctrmgrd-rs/` (Rust)

## D-Bus Integration

- Used by gNMI server for host service interaction
- Go dependency: `github.com/godbus/dbus/v5 v5.1.0` (in `sonic-buildimage/src/sonic-gnmi/go.mod`)

## CI/CD & Deployment

**Primary CI:**
- **Azure DevOps Pipelines** — Full build and test pipeline
  - Config: `sonic-buildimage/azure-pipelines.yml`
  - Build stages: BuildVS (virtual switch), Build (hardware platforms), Test (KVM tests)
  - Hardware platforms built: broadcom, mellanox, marvell-prestera (arm64/armhf), nvidia-bluefield, aspeed, vpp
  - Test stage uses `SONiC-Elastictest` variable group and KVM-based testing via `sonic-mgmt`

**Secondary CI:**
- **GitHub Actions** — Security scanning (Semgrep, CodeQL), PR automation
  - Config: `sonic-buildimage/.github/workflows/`

**Deployment:**
- ONIE installer images for bare-metal switches
- Docker images pushed to configurable registry via `sonic-buildimage/push_docker.sh`
- Image naming: `docker-{component}.gz` (compressed Docker images)
- Installer payload: SquashFS filesystem in ONIE-compatible format

## Environment Configuration

**Required build-time variables:**
- `PLATFORM` - Target platform (broadcom, mellanox, vs, etc.)
- `USERNAME` / `PASSWORD` - Admin credentials for built images
- `BUILD_NUMBER` - CI build number
- `DEFAULT_CONTAINER_REGISTRY` - Docker base image registry (optional)

**Optional feature flags (set via make variables):**
- `ENABLE_ZTP`, `ENABLE_SYNCD_RPC`, `ENABLE_FIPS`, `INCLUDE_KUBERNETES`, `INCLUDE_MUX`, `INCLUDE_RESTAPI`, `INSTALL_DEBUG_TOOLS`, `ENABLE_ASAN`

**Secrets:**
- Docker registry credentials passed as arguments to `sonic-buildimage/push_docker.sh`
- Azure DevOps pipeline variable groups manage CI secrets
- No `.env` files present in repository

## Webhooks & Callbacks

**Incoming:**
- GitHub webhooks trigger Azure DevOps and GitHub Actions pipelines on push/PR events

**Outgoing:**
- None detected in the build system itself
- Runtime SONiC supports gNMI dial-out telemetry (`ENABLE_DIALOUT` flag)

---

*Integration audit: 2025-07-17*
