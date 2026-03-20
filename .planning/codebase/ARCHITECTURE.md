# Architecture

**Analysis Date:** 2025-01-28

## Pattern Overview

**Overall:** Multi-stage Make-based build system for constructing a complete Linux network operating system (SONiC) from source

**Key Characteristics:**
- Declarative dependency-driven build using GNU Make with Jinja2 templating
- Docker-in-Docker build environment ("sonic-slave" containers) that isolate the build from the host
- Hierarchical target system: source packages → Debian packages (.deb) → Docker images (.gz) → ONIE installer images (.bin)
- Extensive git submodule architecture—100+ submodules in `src/` and `platform/` for component source code
- Platform-specific hardware abstraction via `device/` (runtime configs) and `platform/` (build-time modules)
- Multi-distro support (Jessie through Trixie) with per-distro build environments

## Layers

**Layer 1 — Build Orchestration (Make):**
- Purpose: Top-level entry point that configures the platform, spawns the Docker build environment, and delegates to `slave.mk` inside the container
- Location: `sonic-buildimage/Makefile`, `sonic-buildimage/Makefile.work`
- Contains: Platform selection, Debian distro selection, Docker slave container launch
- Depends on: Docker, j2cli (Jinja2 CLI), host system tools
- Used by: CI pipelines (`azure-pipelines.yml`), developers running `make`

**Layer 2 — Build Engine (slave.mk + Makefile.cache):**
- Purpose: Core build logic that compiles all targets inside the sonic-slave Docker container
- Location: `sonic-buildimage/slave.mk` (1909 lines), `sonic-buildimage/Makefile.cache` (773 lines)
- Contains: Build rules for SONIC_MAKE_DEBS, SONIC_DPKG_DEBS, SONIC_PYTHON_WHEELS, SONIC_DOCKER_IMAGES, SONIC_INSTALLERS; caching framework; dependency resolution
- Depends on: `rules/*.mk` for per-target declarations, `src/` for source code
- Used by: `Makefile.work` which invokes it inside the build container

**Layer 3 — Target Declarations (rules/):**
- Purpose: Declare each build target (package/docker/installer), its dependencies, paths, and metadata
- Location: `sonic-buildimage/rules/` (327 files: `*.mk` for declarations, `*.dep` for cache dependency tracking)
- Contains: Per-component `.mk` files (e.g., `rules/swss.mk`, `rules/docker-orchagent.mk`) and `.dep` files for cache hash computation
- Depends on: Nothing (pure declarations)
- Used by: `slave.mk` includes all `.mk` files to populate target lists

**Layer 4 — Source Components (src/):**
- Purpose: Source code for all SONiC software components, mostly as git submodules
- Location: `sonic-buildimage/src/` (100+ subdirectories)
- Contains: Git submodules for sonic-swss, sonic-sairedis, sonic-utilities, sonic-frr, sonic-platform-daemons, etc.; also some inline source packages (redis, bash, etc.)
- Depends on: External git repositories (defined in `.gitmodules`)
- Used by: Build rules in `rules/*.mk` reference `$(SRC_PATH)/component-name`

**Layer 5 — Docker Image Definitions (dockers/):**
- Purpose: Define the Docker images that run as containers on the SONiC switch
- Location: `sonic-buildimage/dockers/` (58 subdirectories)
- Contains: `Dockerfile.j2` (Jinja2-templated Dockerfiles), `supervisord.conf.j2`, startup scripts, config templates
- Depends on: Debian packages built from `src/`, base Docker images (docker-base-*, docker-config-engine-*, docker-swss-layer-*)
- Used by: `slave.mk` docker build rules, final installer image

**Layer 6 — Platform Abstraction (platform/ + device/):**
- Purpose: Hardware-specific build logic (platform/) and runtime configuration (device/)
- Location: `sonic-buildimage/platform/` (23 vendors), `sonic-buildimage/device/` (36 vendors)
- Contains: Platform-specific syncd Docker images, SAI library builds, kernel modules, device port configs, SKU definitions
- Depends on: Vendor-specific submodules, SAI headers
- Used by: Installer build selects platform via `PLATFORM` variable

**Layer 7 — Image Assembly (build_debian.sh + build_image.sh):**
- Purpose: Assemble the final bootable SONiC image from Docker images and Debian root filesystem
- Location: `sonic-buildimage/build_debian.sh` (root filesystem), `sonic-buildimage/build_image.sh` (ONIE installer), `sonic-buildimage/onie-mk-demo.sh`
- Contains: Debian chroot construction, package installation, Docker image embedding, ONIE/Aboot installer generation
- Depends on: All built Debian packages, Docker images, kernel, initramfs
- Used by: `slave.mk` installer targets

**Layer 8 — Installer & Deployment (installer/):**
- Purpose: Self-extracting installer that runs on target switch hardware
- Location: `sonic-buildimage/installer/install.sh`, `sonic-buildimage/installer/sharch_body.sh`
- Contains: ONIE-compatible install script, platform detection, partition management
- Depends on: Assembled filesystem squashfs + Docker images tarball
- Used by: End users flashing SONiC onto switches

## Data Flow

**Full Build Pipeline:**

1. Developer runs `make configure PLATFORM=<vendor>` → writes `.platform` and `.arch` files
2. `make target` invokes `Makefile` → `Makefile.work` → builds sonic-slave Docker image from `sonic-slave-<distro>/Dockerfile.j2`
3. `Makefile.work` launches sonic-slave container with source tree mounted, runs `make -f slave.mk` inside it
4. `slave.mk` resolves dependency graph: sources → `.deb` packages → Docker images → installer `.bin`
5. Each `.deb` target: `src/<component>/` compiled via `dpkg-buildpackage` or custom `Makefile`, output to `target/debs/<distro>/`
6. Each Docker image: `dockers/<name>/Dockerfile.j2` rendered with j2, built with `docker build`, saved as `.gz` to `target/`
7. Installer: `build_debian.sh` creates Debian root filesystem in `fsroot/`, `build_image.sh` packages everything into ONIE `.bin`

**Caching Flow:**

1. Each target has a `.dep` file in `rules/` declaring its dependency files
2. `Makefile.cache` computes SHA hashes of all dependency files (source, makefiles, configs)
3. Before building, checks cache (local or remote) for matching hash
4. After building, saves result to cache for future reuse

**Target Registration Pattern:**

1. Component rule file (e.g., `rules/swss.mk`) defines: `SWSS = swss_1.0.0_$(CONFIGURED_ARCH).deb`
2. Sets `$(SWSS)_SRC_PATH`, `$(SWSS)_DEPENDS`, `$(SWSS)_RDEPENDS`
3. Registers with: `SONIC_DPKG_DEBS += $(SWSS)`
4. `slave.mk` auto-generates build rule from the registration category

**State Management:**
- Build state tracked via file timestamps (Make's native mechanism)
- Platform selection persisted in `.platform` and `.arch` files in project root
- Cache state via SHA hash files in `target/vcache/`
- Docker image state via saved `.gz` tarballs in `target/`

## Key Abstractions

**Target Categories (slave.mk):**
- Purpose: Classify build targets by their build method
- Categories: `SONIC_MAKE_DEBS` (custom Makefile), `SONIC_DPKG_DEBS` (dpkg-buildpackage), `SONIC_PYTHON_WHEELS` (Python setup.py), `SONIC_DOCKER_IMAGES` (Docker build), `SONIC_SIMPLE_DOCKER_IMAGES`, `SONIC_INSTALLERS` (final images)
- Pattern: Each category has a generic build rule in `slave.mk` that iterates over registered targets

**Rule Files (rules/*.mk + rules/*.dep):**
- Purpose: Declare a target's identity, dependencies, and build configuration
- Examples: `sonic-buildimage/rules/swss.mk`, `sonic-buildimage/rules/docker-orchagent.mk`, `sonic-buildimage/rules/docker-database.mk`
- Pattern: Set Make variables using `$(TARGET)_PROPERTY = value` convention, then append to a `SONIC_*` list

**Dockerfile Templates (dockers/*/Dockerfile.j2):**
- Purpose: Templated Dockerfiles using Jinja2 for conditional architecture support and dynamic package lists
- Examples: `sonic-buildimage/dockers/docker-orchagent/Dockerfile.j2`, `sonic-buildimage/dockers/docker-database/Dockerfile.j2`
- Pattern: `{% from "dockers/dockerfile-macros.j2" import ... %}` for shared macros; `ARG docker_container_name`; conditional `{% if %}` blocks for arch-specific packages

**Sonic-Slave Build Containers:**
- Purpose: Reproducible build environment Docker images per Debian version
- Examples: `sonic-buildimage/sonic-slave-bookworm/Dockerfile.j2`, `sonic-buildimage/sonic-slave-trixie/Dockerfile.j2`
- Pattern: Jinja2-templated Dockerfile that installs all build dependencies; `Dockerfile.user.j2` adds user-specific layer

**Platform Modules:**
- Purpose: Vendor-specific hardware abstraction (kernel modules, platform APIs, syncd variants)
- Examples: `sonic-buildimage/platform/broadcom/`, `sonic-buildimage/platform/mellanox/`, `sonic-buildimage/platform/vs/`
- Pattern: Each platform directory contains its own `rules.mk`, `docker-syncd-*.mk`, and optional submodules

## Entry Points

**`sonic-buildimage/Makefile`:**
- Location: `sonic-buildimage/Makefile` (132 lines)
- Triggers: `make <target>`, `make configure PLATFORM=<name>`
- Responsibilities: Selects Debian distros to build, delegates to `Makefile.work` with `BLDENV` set

**`sonic-buildimage/Makefile.work`:**
- Location: `sonic-buildimage/Makefile.work` (758 lines)
- Triggers: Called by `Makefile` with `BLDENV` environment variable
- Responsibilities: Builds sonic-slave Docker image, launches build container, invokes `slave.mk` inside it

**`sonic-buildimage/slave.mk`:**
- Location: `sonic-buildimage/slave.mk` (1909 lines)
- Triggers: Invoked by `make -f slave.mk` inside the sonic-slave container
- Responsibilities: Master build engine—includes all rules, resolves dependencies, builds all target types

**`sonic-buildimage/build_debian.sh`:**
- Location: `sonic-buildimage/build_debian.sh` (~700 lines)
- Triggers: Called by `slave.mk` installer targets
- Responsibilities: Creates Debian root filesystem via debootstrap, installs packages, configures system

**`sonic-buildimage/build_image.sh`:**
- Location: `sonic-buildimage/build_image.sh`
- Triggers: Called by `slave.mk` after `build_debian.sh`
- Responsibilities: Packages rootfs + Docker images into ONIE-compatible installer binary

**`sonic-buildimage/azure-pipelines.yml`:**
- Location: `sonic-buildimage/azure-pipelines.yml`
- Triggers: Git push to master/release branches, pull requests
- Responsibilities: CI/CD pipeline orchestration, delegates to templates in `.azure-pipelines/`

## Error Handling

**Strategy:** Bash `set -e` (exit on error) throughout shell scripts; Make's built-in error propagation

**Patterns:**
- Shell scripts use `set -x -e` for debug output and fail-fast: `sonic-buildimage/build_debian.sh`, `sonic-buildimage/build_image.sh`
- `functions.sh` provides `die()` (print + exit 1) and `warn()` (print to stderr)
- `scripts/run_with_retry` wraps make invocations with retry logic for transient failures
- Build logs captured per-target via `$(LOG)` macro in `slave.mk`

## Cross-Cutting Concerns

**Logging:**
- Build log per target, controlled by `BUILD_LOG_TIMESTAMP` setting in `sonic-buildimage/rules/config`
- `$(LOG)` macro in `slave.mk` redirects stdout/stderr to target-specific log files
- `scripts/process_log.sh` for log post-processing

**Validation:**
- `sonic-buildimage/check_install.py` validates package installation
- `sonic-buildimage/pytest.ini` configures pytest for Python component tests
- `sonic-buildimage/installer/tests/` contains installer test infrastructure

**Authentication/Security:**
- Secure boot signing via `scripts/sign_image.sh`, `scripts/signing_kernel_modules.sh`
- FIPS support toggled by `INCLUDE_FIPS` / `ENABLE_FIPS` build flags
- Default credentials configured in `sonic-buildimage/rules/config` (`DEFAULT_USERNAME`, `DEFAULT_PASSWORD`)

**Version Management:**
- `sonic-buildimage/scripts/versions_manager.py` manages dependency version pinning
- `sonic-buildimage/files/build/versions/` contains version lock files
- `functions.sh::sonic_get_version()` derives image version from git tags/branch

---

*Architecture analysis: 2025-01-28*
