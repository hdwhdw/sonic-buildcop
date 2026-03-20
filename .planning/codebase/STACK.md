# Technology Stack

**Analysis Date:** 2025-07-17

## Overview

This repository (`submodule-status`) contains a single subdirectory `sonic-buildimage/`, which is a clone/checkout of the [SONiC](https://github.com/sonic-net/sonic-buildimage) (Software for Open Networking in the Cloud) build image repository. SONiC is a Linux-based network operating system for data center switches, maintained by Microsoft and the sonic-net community under the Apache 2.0 license.

The repository is fundamentally a **build system** — it orchestrates compilation of ~100+ software components into Docker containers and ONIE-compatible installer images for bare-metal network switches.

## Languages

**Primary:**
- **Bash/Shell** - Build system orchestration, image assembly, Docker build scripts. The backbone of the entire build pipeline.
  - Key files: `sonic-buildimage/build_debian.sh`, `sonic-buildimage/build_docker.sh`, `sonic-buildimage/build_image.sh`, `sonic-buildimage/functions.sh`
- **GNU Make** - Build dependency management and parallel build orchestration.
  - Key files: `sonic-buildimage/Makefile`, `sonic-buildimage/Makefile.work`, `sonic-buildimage/slave.mk`, `sonic-buildimage/Makefile.cache`
  - Rules directory: `sonic-buildimage/rules/` (~200+ `.mk` and `.dep` files)
- **Python 3** - Configuration engine, utilities, platform daemons, management tools, test scripts.
  - Key packages: `sonic-buildimage/src/sonic-config-engine/`, `sonic-buildimage/src/sonic-utilities/`, `sonic-buildimage/src/sonic-py-common/`, `sonic-buildimage/src/sonic-platform-daemons/`, `sonic-buildimage/src/sonic-host-services/`
  - Build tooling: `sonic-buildimage/scripts/versions_manager.py`, `sonic-buildimage/check_install.py`

**Secondary:**
- **C/C++** - Core networking daemons and switch abstraction layer (compiled from submodules).
  - Key packages with `configure.ac`: `sonic-buildimage/src/sonic-swss-common/`, `sonic-buildimage/src/sonic-swss/`, `sonic-buildimage/src/sonic-sairedis/`, `sonic-buildimage/src/iccpd/`, `sonic-buildimage/src/sonic-stp/`, `sonic-buildimage/src/sonic-sysmgr/`
- **Go 1.19** - gNMI server/telemetry agent.
  - Key package: `sonic-buildimage/src/sonic-gnmi/` (see `sonic-buildimage/src/sonic-gnmi/go.mod`)
- **Rust (Edition 2021)** - Newer system services being added to SONiC.
  - Workspaces: `sonic-buildimage/src/sonic-swss-common/Cargo.toml`, `sonic-buildimage/src/sonic-swss/Cargo.toml`, `sonic-buildimage/src/sonic-dash-ha/Cargo.toml`, `sonic-buildimage/src/sonic-host-services/Cargo.toml`, `sonic-buildimage/src/sonic-nettools/Cargo.toml`, `sonic-buildimage/src/sonic-ctrmgrd-rs/Cargo.toml`, `sonic-buildimage/src/sonic-rs-common/Cargo.toml`, `sonic-buildimage/src/syslog-counter/Cargo.toml`, `sonic-buildimage/src/sonic-supervisord-utilities-rs/Cargo.toml`
- **Jinja2 Templates (`.j2`)** - Dockerfile generation, configuration file rendering. Used extensively throughout `sonic-buildimage/dockers/` and `sonic-buildimage/device/`.

## Runtime

**Target Environment:**
- **Debian GNU/Linux** - Target OS base for SONiC images
  - Primary: Debian Trixie (13) and Bookworm (12)
  - Legacy: Bullseye (11), Buster (10), Stretch (9), Jessie (8)
  - Config: `sonic-buildimage/Makefile` sets `NOBOOKWORM ?= 0`, `NOTRIXIE ?= 0` (both enabled by default)

**Linux Kernel:**
- Version: `6.12.41+deb13` (configured in `sonic-buildimage/build_debian.sh`)

**Container Runtime:**
- Docker CE `5:28.5.2-1~debian.13` with containerd.io `1.7.28-2~debian.13` (configured in `sonic-buildimage/build_debian.sh`)

**Build Environment:**
- Docker-in-Docker ("sonic-slave" container) — the build runs inside a Docker container that itself builds Docker images.
- Slave Dockerfiles per Debian release: `sonic-buildimage/sonic-slave-bookworm/Dockerfile.j2`, `sonic-buildimage/sonic-slave-trixie/Dockerfile.j2`, etc.

**Architectures:**
- `amd64` (primary)
- `arm64` (via cross-compilation or native builds)
- `armhf` (via cross-compilation or native builds)
- Cross-compilation support via QEMU user-static emulation

**Package Manager:**
- **dpkg/apt** - Debian package management (primary output format is `.deb` packages)
- **pip** - Python package management
- Python wheels built for distribution: target path `target/python-wheels/`

## Frameworks

**Core:**
- **GNU Make** - Primary build orchestration (`sonic-buildimage/Makefile`, `sonic-buildimage/Makefile.work`, `sonic-buildimage/slave.mk`)
- **Jinja2/jinjanate (j2cli)** - Template rendering for Dockerfiles, configuration files, and supervisord configs
- **ONIE (Open Network Install Environment)** - Network switch installer framework (`sonic-buildimage/onie-image.conf`, `sonic-buildimage/onie-mk-demo.sh`)
- **supervisord** - Process management within Docker containers (used in all service containers)

**Testing:**
- **pytest** - Python test framework (config: `sonic-buildimage/pytest.ini`)
- **pexpect** - Used for integration testing of VM images (`sonic-buildimage/check_install.py`, `sonic-buildimage/install_sonic.py`)
- **PTF (Packet Test Framework)** - Network packet testing (`sonic-buildimage/src/ptf-py3/`)
- **scapy** - Packet crafting and testing (`sonic-buildimage/src/scapy/`)

**Build/Dev:**
- **dpkg-buildpackage** - Debian package building
- **Docker** - Container image building (58+ Docker images in `sonic-buildimage/dockers/`)
- **jinjanate/j2cli** - Jinja2 CLI for template rendering (`sonic-buildimage/scripts/j2cli`)
- **Semgrep** - Static analysis security scanning (`.github/workflows/semgrep.yml`)
- **CodeQL** - GitHub code scanning for Python (`.github/workflows/codeql-analysis.yml`)

**Networking/Routing Frameworks (within built images):**
- **FRRouting (FRR) 10.4.1** - BGP/OSPF/routing protocols (`sonic-buildimage/src/sonic-frr/`)
- **SAI (Switch Abstraction Interface)** - Hardware abstraction via `sonic-buildimage/src/sonic-sairedis/`
- **SWSS (Switch State Service)** - SONiC switch state orchestration (`sonic-buildimage/src/sonic-swss/`)

## Key Dependencies

**Critical (built from source as submodules):**
- `sonic-swss-common` - Common library for Switch State Service (`sonic-buildimage/src/sonic-swss-common/`)
- `sonic-swss` - Switch State Service / orchagent (`sonic-buildimage/src/sonic-swss/`)
- `sonic-sairedis` - SAI Redis integration (`sonic-buildimage/src/sonic-sairedis/`)
- `sonic-frr` (FRRouting 10.4.1) - Routing protocol suite (`sonic-buildimage/src/sonic-frr/`)
- `sonic-utilities` - CLI tools for SONiC management (`sonic-buildimage/src/sonic-utilities/`)
- `sonic-config-engine` - Configuration generation (`sonic-buildimage/src/sonic-config-engine/`)
- `sonic-gnmi` - gNMI/telemetry server (`sonic-buildimage/src/sonic-gnmi/`)
- `sonic-linux-kernel` - Custom Linux kernel (`sonic-buildimage/src/sonic-linux-kernel/`)

**Infrastructure:**
- **Redis** - Central datastore for SONiC's database architecture (built from `sonic-buildimage/src/redis/`, container `sonic-buildimage/dockers/docker-database/`)
- **LLDP** - Link Layer Discovery Protocol daemon (`sonic-buildimage/src/lldpd/`)
- **Net-SNMP** - SNMP agent (`sonic-buildimage/src/snmpd/`)
- **libyang / libyang3** - YANG data modeling library (`sonic-buildimage/src/libyang/`, `sonic-buildimage/src/libyang3/`)
- **gRPC / Protobuf** - RPC framework for gNMI and telemetry (`sonic-buildimage/src/grpc/`, `sonic-buildimage/src/protobuf/`)
- **Thrift** - RPC framework for SAI RPC mode (`sonic-buildimage/src/thrift/`, `sonic-buildimage/src/thrift_0_14_1/`)

**Python Libraries (in setup.py files):**
- `Jinja2>=2.10` - Template rendering
- `PyYAML>=6.0.1` - YAML parsing
- `netaddr==0.8.0` - Network address manipulation
- `lxml>=4.9.1` - XML processing
- `bitarray==2.8.1` - Bit array operations
- `click` - CLI framework
- `tabulate` - CLI table formatting
- `pyroute2` - Linux networking library
- `pexpect` - Process interaction/testing

**Go Dependencies (sonic-gnmi):**
- `github.com/openconfig/gnmi v0.14.1` - gNMI protocol
- `github.com/openconfig/gnoi v0.3.0` - gNOI protocol
- `github.com/openconfig/gnsi v1.9.0` - gNSI protocol
- `github.com/go-redis/redis/v7` - Redis client
- `github.com/redis/go-redis/v9` - Redis client (v9)
- `github.com/godbus/dbus/v5` - D-Bus integration
- `github.com/golang/protobuf` - Protocol Buffers

**Rust Dependencies (from various Cargo.toml):**
- `swss-common` (internal) - SONiC common library bindings
- `clap 4.0` - CLI argument parsing
- `nix 0.27` - Unix system call wrappers
- `tracing 0.1` - Structured logging
- `thiserror 1` - Error handling

## Configuration

**Build Configuration:**
- `sonic-buildimage/rules/config` - Master build configuration (build jobs, passwords, feature flags)
- `sonic-buildimage/Makefile` - Top-level build entry point with Debian version toggles
- `sonic-buildimage/Makefile.work` - Docker slave container setup and build parameter passing
- `sonic-buildimage/slave.mk` - Inner build rules (~88K lines), package build recipes
- `sonic-buildimage/Makefile.cache` - DPKG caching framework (~37K lines)

**Platform Configuration:**
- `sonic-buildimage/onie-image.conf` - ONIE installer configuration (x86_64 default, 32GB partition)
- `sonic-buildimage/onie-image-arm64.conf` - ARM64 ONIE configuration
- `sonic-buildimage/onie-image-armhf.conf` - ARMhf ONIE configuration
- `sonic-buildimage/device/` - Per-vendor/per-platform device configurations (37+ vendors)

**Version Management:**
- `sonic-buildimage/scripts/versions_manager.py` - Freezes/manages dependency versions
- `sonic-buildimage/files/build/versions/` - Pinned versions for reproducible builds

**Key Build Parameters (from `rules/config` and `Makefile.work`):**
- `PLATFORM` - Target hardware platform (broadcom, mellanox, vs, etc.)
- `SONIC_BUILD_JOBS` - Parallel build jobs (auto-calculated: `min(nproc/4, ram_gb/8)`, capped at 8)
- `USERNAME` / `PASSWORD` - Default admin credentials for built images (default: `admin` / `YourPaSsWoRd`)
- `ENABLE_ZTP` - Zero Touch Provisioning
- `ENABLE_SYNCD_RPC` - RPC-based syncd builds for testing
- `INCLUDE_KUBERNETES` - Optional Kubernetes support
- `ENABLE_FIPS` - FIPS compliance mode
- `KERNEL_PROCURE_METHOD` - Build or download kernel packages
- `SONIC_DPKG_CACHE_METHOD` - Build caching (none, cache, rcache, wcache, rwcache)

## Platform Requirements

**Development (Build Host):**
- Linux (Debian/Ubuntu recommended)
- Docker installed (user must be in docker group; root/sudo not supported)
- `j2` / `jinjanate` CLI tool (Jinja2 template rendering)
- ~32GB+ RAM recommended (build parallelism scales by `ram_gb/8`)
- Significant disk space (full build generates dozens of Docker images and hundreds of .deb packages)

**Production (Target):**
- Bare-metal network switches with ONIE bootloader
- Supported ASICs: Broadcom, Mellanox/NVIDIA, Marvell, Barefoot/Intel, Centec, Pensando, and others
- Or: Virtual switch (VS) platform for testing/development
- 32GB+ storage (default ONIE partition size)

---

*Stack analysis: 2025-07-17*
