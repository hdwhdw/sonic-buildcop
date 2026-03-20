# Codebase Structure

**Analysis Date:** 2025-01-28

## Directory Layout

```
submodule-status/                    # Wrapper repository (no commits yet)
├── .planning/                       # GSD planning documents
│   └── codebase/                    # Architecture/structure analysis
└── sonic-buildimage/                # Full clone of sonic-net/sonic-buildimage (the actual project)
    ├── Makefile                     # Top-level entry: distro selection, delegates to Makefile.work
    ├── Makefile.work                # Docker slave container orchestration (758 lines)
    ├── slave.mk                     # Core build engine, runs inside container (1909 lines)
    ├── Makefile.cache               # DPKG caching framework (773 lines)
    ├── functions.sh                 # Shared shell functions (die, warn, sonic_get_version)
    ├── build_debian.sh              # Root filesystem assembly script
    ├── build_image.sh               # Final installer image assembly
    ├── build_docker.sh              # Standalone Docker image build helper
    ├── onie-mk-demo.sh              # ONIE installer packaging
    ├── onie-image.conf              # ONIE image configuration (x86_64)
    ├── onie-image-arm64.conf        # ONIE image configuration (ARM64)
    ├── onie-image-armhf.conf        # ONIE image configuration (ARMhf)
    ├── azure-pipelines.yml          # Main CI/CD pipeline definition
    ├── pytest.ini                   # Pytest configuration
    ├── .gitmodules                  # 60+ submodule definitions
    ├── rules/                       # Build target declarations (327 files)
    ├── src/                         # Source code components (100+ subdirs, mostly submodules)
    ├── dockers/                     # Docker image definitions (58 subdirs)
    ├── platform/                    # Platform/vendor build logic (23 platforms)
    ├── device/                      # Runtime device configurations (36 vendors)
    ├── files/                       # Static files, templates, image configs
    ├── scripts/                     # Build helper scripts
    ├── installer/                   # ONIE installer framework
    ├── target/                      # Build output directory (mostly empty pre-build)
    ├── sonic-slave-bookworm/        # Build container Dockerfile (Debian Bookworm)
    ├── sonic-slave-bullseye/        # Build container Dockerfile (Debian Bullseye)
    ├── sonic-slave-buster/          # Build container Dockerfile (Debian Buster)
    ├── sonic-slave-jessie/          # Build container Dockerfile (Debian Jessie)
    ├── sonic-slave-stretch/         # Build container Dockerfile (Debian Stretch)
    ├── sonic-slave-trixie/          # Build container Dockerfile (Debian Trixie)
    ├── .azure-pipelines/            # CI/CD pipeline templates
    ├── .github/                     # GitHub config (CODEOWNERS, workflows, issue templates)
    └── fsroot.docker./              # Docker filesystem overlay (build-time)
```

## Directory Purposes

**`sonic-buildimage/rules/`:**
- Purpose: Declarative build target definitions—every package, Docker image, and installer has a `.mk` + `.dep` pair here
- Contains: 327 files total. `.mk` files declare target name, source path, dependencies, and register with `SONIC_*` lists. `.dep` files declare cache dependency tracking files.
- Key files:
  - `sonic-buildimage/rules/config` — Global build configuration (usernames, passwords, feature flags, job counts)
  - `sonic-buildimage/rules/swss.mk` — SWSS package declaration
  - `sonic-buildimage/rules/docker-orchagent.mk` — Orchestration agent Docker image
  - `sonic-buildimage/rules/docker-database.mk` — Database Docker image
  - `sonic-buildimage/rules/sonic-fips.mk` — FIPS build support

**`sonic-buildimage/src/`:**
- Purpose: All SONiC component source code, primarily as git submodules
- Contains: 100+ subdirectories. Major components:
  - `src/sonic-swss/` — Switch State Service (orchagent, portsyncd, etc.)
  - `src/sonic-sairedis/` — SAI Redis integration layer
  - `src/sonic-swss-common/` — Common libraries for SWSS
  - `src/sonic-utilities/` — CLI utilities (config, show, etc.)
  - `src/sonic-config-engine/` — Configuration generation (sonic-cfggen)
  - `src/sonic-frr/` — FRRouting (BGP, OSPF, etc.)
  - `src/sonic-linux-kernel/` — Custom Linux kernel
  - `src/sonic-platform-daemons/` — Platform monitoring daemons
  - `src/sonic-gnmi/` — gNMI server
  - `src/sonic-mgmt-framework/` — Management framework
  - `src/sonic-py-common/` — Shared Python libraries
  - `src/sonic-host-services/` — Host services
  - `src/redis/`, `src/bash/`, `src/lldpd/` — Upstream packages rebuilt for SONiC

**`sonic-buildimage/dockers/`:**
- Purpose: Docker container definitions for SONiC runtime services
- Contains: 58 subdirectories, each with `Dockerfile.j2`, `supervisord.conf.j2`, startup scripts, and config templates
- Key images:
  - `dockers/docker-orchagent/` — Switch orchestration (SWSS)
  - `dockers/docker-database/` — Redis database instances
  - `dockers/docker-fpm-frr/` — FRRouting (BGP, etc.)
  - `dockers/docker-snmp/` — SNMP agent
  - `dockers/docker-lldp/` — LLDP daemon
  - `dockers/docker-teamd/` — LAG/port-channel management
  - `dockers/docker-platform-monitor/` — Platform health monitoring
  - `dockers/docker-sonic-gnmi/` — gNMI telemetry
  - `dockers/docker-dhcp-relay/` — DHCP relay
  - `dockers/docker-nat/` — NAT service
  - `dockers/docker-base/` through `dockers/docker-base-trixie/` — Base images per distro
  - `dockers/docker-config-engine*/` — Configuration engine base images
  - `dockers/docker-swss-layer-*/` — SWSS dependency layer images
  - `dockers/dockerfile-macros.j2` — Shared Jinja2 macros for Dockerfiles

**`sonic-buildimage/platform/`:**
- Purpose: Vendor/ASIC-specific build-time code—syncd Docker images, kernel modules, SAI libraries
- Contains: 23 platform directories, each with its own build rules and optional submodules
- Key platforms:
  - `platform/broadcom/` — Memory Memory broadcom ASIC platforms (Memory most common)
  - `platform/mellanox/` — NVIDIA/Mellanox ASIC platforms
  - `platform/vs/` — Virtual Switch (for testing/development)
  - `platform/barefoot/` — Intel/Barefoot Tofino platforms
  - `platform/marvell-prestera/` — Marvell ASIC platforms
  - `platform/generic/` — Generic platform (no hardware-specific code)
  - `platform/pddf/` — Platform Driver Development Framework (shared abstraction)
  - `platform/template/` — Template `.mk` files for creating new platforms
  - `platform/checkout/` — Platform checkout configuration

**`sonic-buildimage/device/`:**
- Purpose: Runtime device-specific configuration files (port maps, SKU definitions, sensor configs)
- Contains: 36 vendor directories, each containing per-device-model subdirectories
- Structure per device: `device/<vendor>/<device-model>/` contains:
  - `port_config.ini` or SKU subdirectories with port mappings
  - `sai.profile` — SAI profile configuration
  - `*.config.bcm` — ASIC configuration files (Broadcom)
  - `platform_asic` — ASIC type identifier
  - `installer.conf` — Installation configuration
  - `plugins/` — Python device plugins (psuutil.py, sfputil.py, eeprom.py)
  - `default_sku` — Default SKU selection

**`sonic-buildimage/files/`:**
- Purpose: Static files, templates, and scripts embedded into the final image
- Contains: Subdirectories organized by function:
  - `files/build_templates/` — Jinja2 templates for systemd services, init configs, and image assembly (`sonic_debian_extension.j2`, `docker_image_ctl.j2`)
  - `files/image_config/` — Runtime configuration templates (50+ subdirs: syslog, systemd, interfaces, kubernetes, etc.)
  - `files/build/` — Build version files
  - `files/build_scripts/` — Build-time helper scripts
  - `files/initramfs-tools/` — Initramfs hooks and scripts
  - `files/docker/` — Docker daemon configuration
  - `files/scripts/` — Runtime helper scripts
  - `files/apt/` — APT repository configuration
  - `files/sshd/` — SSH daemon configuration
  - `files/dhcp/` — DHCP configuration

**`sonic-buildimage/scripts/`:**
- Purpose: Build automation scripts used by Makefile and CI pipelines
- Contains: 30 scripts for build infrastructure
- Key files:
  - `scripts/build_debian_base_system.sh` — Debootstrap wrapper
  - `scripts/versions_manager.py` — Dependency version management
  - `scripts/build_kvm_image.sh` — KVM virtual machine image builder
  - `scripts/prepare_docker_buildinfo.sh` — Docker build metadata preparation
  - `scripts/run_with_retry` — Retry wrapper for make commands
  - `scripts/sign_image.sh` — Image signing for secure boot
  - `scripts/signing_kernel_modules.sh` — Kernel module signing

**`sonic-buildimage/installer/`:**
- Purpose: ONIE-compatible self-extracting installer framework
- Contains: `install.sh` (main installer), `sharch_body.sh` (self-extracting archive header), `default_platform.conf`, `tests/`
- Key files:
  - `sonic-buildimage/installer/install.sh` — Detects install environment (ONIE/sonic/build), partitions disk, extracts image

**`sonic-buildimage/target/`:**
- Purpose: Build output directory (populated during build)
- Contains: `vcache/` (version cache), `versions/` (version tracking)
- Generated: Yes — all build artifacts land here
- Committed: Only `vcache/` and `versions/` subdirectories

**`sonic-buildimage/sonic-slave-*/`:**
- Purpose: Dockerfiles for the build environment containers, one per Debian version
- Contains: `Dockerfile.j2` (main, Jinja2-templated), `Dockerfile.user.j2` (user layer)
- Key directories:
  - `sonic-buildimage/sonic-slave-bookworm/` — Current primary build environment
  - `sonic-buildimage/sonic-slave-trixie/` — Newest build environment

**`sonic-buildimage/.azure-pipelines/`:**
- Purpose: Azure DevOps CI/CD pipeline templates and configuration
- Contains: 35 YAML template files for build jobs, test scheduling, caching, and Docker slave management
- Key files:
  - `.azure-pipelines/azure-pipelines-build.yml` — Main build template
  - `.azure-pipelines/build-template.yml` — Reusable build step template
  - `.azure-pipelines/run-test-template.yml` — Test execution template
  - `.azure-pipelines/official-build.yml` — Official release build pipeline

**`sonic-buildimage/.github/`:**
- Purpose: GitHub repository configuration
- Contains: `CODEOWNERS`, issue/PR templates, `workflows/` (9 GitHub Actions: automerge, CodeQL, labeler, cherry-pick, semgrep)

## Key File Locations

**Entry Points:**
- `sonic-buildimage/Makefile`: Top-level build entry — `make configure`, `make target`
- `sonic-buildimage/Makefile.work`: Docker slave container launch
- `sonic-buildimage/slave.mk`: Core build engine (inside container)
- `sonic-buildimage/azure-pipelines.yml`: CI/CD entry point

**Configuration:**
- `sonic-buildimage/rules/config`: Master build configuration (feature flags, credentials, job counts)
- `sonic-buildimage/onie-image.conf`: ONIE installer image settings
- `sonic-buildimage/.platform`: Selected platform (generated by `make configure`)
- `sonic-buildimage/.arch`: Selected architecture (generated by `make configure`)
- `sonic-buildimage/.gitmodules`: All submodule URL/path definitions

**Core Logic:**
- `sonic-buildimage/slave.mk`: All build target rules and dependency resolution
- `sonic-buildimage/Makefile.cache`: Caching framework (hash computation, cache load/save)
- `sonic-buildimage/build_debian.sh`: Root filesystem construction
- `sonic-buildimage/build_image.sh`: Final image assembly
- `sonic-buildimage/functions.sh`: Shared shell utilities

**Templates:**
- `sonic-buildimage/dockers/dockerfile-macros.j2`: Shared Dockerfile Jinja2 macros
- `sonic-buildimage/files/build_templates/sonic_debian_extension.j2`: Main image extension template
- `sonic-buildimage/files/build_templates/docker_image_ctl.j2`: Docker container lifecycle management

**Testing:**
- `sonic-buildimage/pytest.ini`: Root pytest configuration
- `sonic-buildimage/installer/tests/`: Installer test suite
- `sonic-buildimage/platform/vs/tests/`: Virtual switch platform tests

## Naming Conventions

**Files:**
- Rule files: `<component-name>.mk` / `<component-name>.dep` (e.g., `rules/swss.mk`, `rules/swss.dep`)
- Docker rules: `docker-<service-name>.mk` (e.g., `rules/docker-orchagent.mk`)
- Dockerfile templates: `Dockerfile.j2` (always Jinja2-templated)
- Config templates: `<name>.j2` (Jinja2), `<name>.conf` (static config)
- Shell scripts: `<verb>_<noun>.sh` (e.g., `build_debian.sh`, `build_image.sh`)
- Platform images: `sonic-<platform>.bin` (e.g., `sonic-vs.bin`)

**Directories:**
- Source components: `src/sonic-<name>/` or `src/<upstream-name>/` (e.g., `src/sonic-swss/`, `src/redis/`)
- Docker images: `dockers/docker-<service-name>/` (e.g., `dockers/docker-orchagent/`)
- Platform vendors: `platform/<vendor>/` (e.g., `platform/broadcom/`)
- Device configs: `device/<vendor>/<arch>-<model>-r<revision>/` (e.g., `device/broadcom/x86_64-bcm_xlr-r0/`)
- Build environments: `sonic-slave-<debian-codename>/` (e.g., `sonic-slave-bookworm/`)

**Make Variables:**
- Target names: `UPPER_SNAKE_CASE` (e.g., `DOCKER_ORCHAGENT`, `SWSS`, `SONIC_ONE_IMAGE`)
- Target properties: `$(TARGET)_PROPERTY` (e.g., `$(SWSS)_SRC_PATH`, `$(DOCKER_ORCHAGENT)_DEPENDS`)
- Target lists: `SONIC_<CATEGORY>` (e.g., `SONIC_DPKG_DEBS`, `SONIC_DOCKER_IMAGES`, `SONIC_INSTALLERS`)

## Where to Add New Code

**New SONiC Service/Daemon:**
1. Source code: Add submodule to `sonic-buildimage/src/sonic-<name>/`
2. Register in `.gitmodules`
3. Package rule: Create `sonic-buildimage/rules/<name>.mk` and `sonic-buildimage/rules/<name>.dep`
4. Docker definition: Create `sonic-buildimage/dockers/docker-<name>/` with `Dockerfile.j2`, `supervisord.conf.j2`
5. Docker rule: Create `sonic-buildimage/rules/docker-<name>.mk` and `sonic-buildimage/rules/docker-<name>.dep`
6. Service template: Add `sonic-buildimage/files/build_templates/<name>.service.j2`
7. Register in installer: Add to `$(SONIC_ONE_IMAGE)_DOCKERS` in platform's `one-image.mk`

**New Platform Support:**
1. Platform build code: Create `sonic-buildimage/platform/<vendor>/` with `rules.mk`, `docker-syncd-<vendor>.mk`
2. Device configs: Create `sonic-buildimage/device/<vendor>/<device-model>/` with port configs, SAI profiles
3. Platform installer config: Add `platform/<vendor>/platform.conf`
4. Installer image: Create `sonic-buildimage/platform/<vendor>/one-image.mk`

**New Build Rule for Existing Package:**
- Create `sonic-buildimage/rules/<package>.mk` following existing patterns
- Create corresponding `sonic-buildimage/rules/<package>.dep`
- Register target with appropriate `SONIC_*` list (SONIC_DPKG_DEBS, SONIC_MAKE_DEBS, or SONIC_PYTHON_WHEELS)

**New Build Script:**
- Add to `sonic-buildimage/scripts/`
- Follow naming: `<verb>_<noun>.sh`

**New Image Configuration:**
- Runtime configs: Add to `sonic-buildimage/files/image_config/<feature>/`
- Build templates: Add to `sonic-buildimage/files/build_templates/`

**New CI Pipeline:**
- Add template to `sonic-buildimage/.azure-pipelines/`
- Reference from `sonic-buildimage/azure-pipelines.yml`

## Special Directories

**`sonic-buildimage/target/`:**
- Purpose: All build outputs (debs, wheels, Docker images, installer binaries)
- Generated: Yes — populated entirely during build
- Committed: Only `target/vcache/` and `target/versions/` are committed
- Subdirectory structure (at build time): `target/debs/<distro>/`, `target/files/<distro>/`, `target/python-debs/<distro>/`, `target/python-wheels/<distro>/`

**`sonic-buildimage/fsroot.docker./`:**
- Purpose: Docker filesystem overlay workspace used during build
- Generated: Partially (populated during build)
- Committed: Directory exists but is essentially empty

**`sonic-buildimage/src/` (submodules):**
- Purpose: Component source code
- Generated: No — git submodules that must be initialized with `git submodule update --init`
- Committed: Submodule references only (SHA pointers in parent repo)

---

*Structure analysis: 2025-01-28*
