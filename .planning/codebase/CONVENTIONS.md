# Coding Conventions

**Analysis Date:** 2025-07-17

## Overview

This is the SONiC build image repository (`sonic-buildimage/`), a large multi-language monorepo for building the SONiC (Software for Open Networking in the Cloud) network operating system. It contains ~100+ subprojects under `src/`, platform vendor modules under `platform/`, Docker container definitions under `dockers/`, and build infrastructure in Makefiles and shell scripts.

## Languages

**Primary:** Python 3 — used for daemons, CLI tools, platform APIs, config engines, tests
**Secondary:** Bash — build scripts, installer scripts, image assembly
**Tertiary:** C/C++ — low-level platform drivers and SAI adapters (mostly in submodules)
**Emerging:** Rust — newer components like `src/sonic-dash-ha/`, `src/sonic-host-services/crates/`, `src/sonic-swss-common/crates/`

## Naming Patterns

**Python Files:**
- Use `snake_case.py` for all Python source files
- Test files use `test_<module>.py` prefix convention (pytest standard): `test_sfp.py`, `test_bgp.py`, `test_dhcp_cfggen.py`
- Some older test files in `src/sonic-utilities/tests/` use `<module>_test.py` suffix convention: `acl_loader_test.py`, `config_snmp_test.py`, `bgp_commands_test.py`
- Both naming patterns coexist — use whichever is already established in the specific subproject

**Python Modules/Packages:**
- Use `snake_case` for directory names: `sonic_platform/`, `dhcp_utilities/`, `bgpcfgd/`
- Daemon entry points typically named `<daemon_name>.py` or in `__main__.py`

**Python Functions:**
- Use `snake_case` consistently: `get_config_db_table()`, `validate_actions()`, `load_rules_from_file()`
- Private methods use single underscore prefix: `_get_error_description_dict()`, `_parse_port_map_alias()`
- Test functions: `test_<description>()` — e.g., `test_sfp_index()`, `test_config_snmp_community_add_new_community_ro()`

**Python Classes:**
- Use `PascalCase`: `AclLoader`, `BGPPeerGroupMgr`, `DhcpServCfgGenerator`, `ContainerConfigDaemon`
- Abbreviations stay uppercase in class names: `BGPPeerMgrBase`, `DVSDatabase`

**Python Variables/Constants:**
- Constants use `UPPER_SNAKE_CASE`: `SYSLOG_IDENTIFIER`, `DEFAULT_REDIS_PORT`, `FEATURE_TABLE`
- Instance variables use `snake_case`: `self.cfg_mgr`, `self.constants`, `self.table_name`
- DB table names as constants: `SWITCH_CAPABILITY = "SWITCH_CAPABILITY|switch"`

**Shell Scripts:**
- Use `snake_case.sh` or `kebab-case.sh`: `build_debian.sh`, `onie-mk-demo.sh`
- Variables use `UPPER_SNAKE_CASE`: `FILESYSTEM_ROOT`, `CONFIGURED_ARCH`, `DOCKER_VERSION`

**Rust Code:**
- Standard Rust conventions: `snake_case` functions, `PascalCase` types, `SCREAMING_SNAKE_CASE` constants
- Test files in `tests/` directory with `test_` prefix or descriptive names: `echo.rs`, `kvstore.rs`

**Makefile Targets:**
- Use lowercase with hyphens or dots: targets defined in `Makefile`, `Makefile.work`, `slave.mk`
- Build rules in individual `rules/` files per package

## Code Style

**Formatting:**
- No global auto-formatter enforced across the entire repo
- `src/sonic-utilities/` uses flake8 via pre-commit with `--max-line-length=120` (see `src/sonic-utilities/.pre-commit-config.yaml`)
- `src/sonic-dash-ha/` uses `rustfmt` for Rust code via pre-commit (see `src/sonic-dash-ha/.pre-commit-config.yaml`)
- Platform vendor code (e.g., `platform/barefoot/`, `platform/broadcom/`) uses pylint (`.pylintrc` present)
- Most Python code uses 4-space indentation (PEP 8 standard)

**Linting:**
- flake8 is the primary Python linter where used, with `--max-line-length=120`
- No project-wide `.flake8` or `.pylintrc` at the repo root
- Some subprojects have their own: `src/sonic-frr/frr/.flake8`, `src/sonic-frr/frr/.pylintrc`

## Import Organization

**Python Import Order (observed pattern):**
1. Standard library imports (`os`, `sys`, `json`, `subprocess`, `unittest`)
2. Third-party imports (`click`, `pytest`, `jinja2`, `netaddr`, `redis`)
3. SONiC common library imports (`sonic_py_common`, `swsscommon`, `sonic_yang`)
4. Local/relative imports

**Common Path Manipulation Pattern:**
```python
# Extremely common in test files — add module paths manually
test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)
sys.path.insert(0, test_path)
```
This pattern appears in nearly every test file across the repo. Use it when writing new tests.

**No Path Aliases:** The project does not use `pyproject.toml` path aliases or import mapping. Imports are resolved via `sys.path` manipulation and `setup.py` package installation.

## Error Handling

**Python Patterns:**

1. **Syslog-based logging for daemons** — Daemons use `syslog` directly or via wrapper functions:
   ```python
   # src/sonic-bgpcfgd/bgpcfgd/log.py
   import syslog
   def log_err(msg):
       syslog.syslog(syslog.LOG_ERR, msg)
   def log_info(msg):
       syslog.syslog(syslog.LOG_INFO, msg)
   ```

2. **sonic_py_common.logger for containerized daemons:**
   ```python
   # src/sonic-containercfgd/containercfgd/containercfgd.py
   from sonic_py_common import daemon_base, logger
   SYSLOG_IDENTIFIER = "containercfgd"
   logger = logger.Logger(SYSLOG_IDENTIFIER)
   ```

3. **Try/except with logging** — Errors are caught, logged, and either returned False or re-raised:
   ```python
   try:
       policy = self.policy_template.render(**kwargs)
   except jinja2.TemplateError as e:
       log_err("Can't render policy template name: '%s': %s" % (name, str(e)))
       return False
   ```

4. **SystemExit for CLI tools** — CLI commands use `sys.exit()` with specific error codes:
   ```python
   # Different exit codes for different error types in sonic-utilities
   sys.exit(1)  # general error
   sys.exit(2)  # validation error
   sys.exit(3)  # conflict/already exists
   ```

5. **Boolean return for handler success/failure:**
   ```python
   def set_handler(self, key, data):
       # Return True on success, False to retry later
       return True
   ```

**Shell Script Patterns:**
- Use `set -e` (exit on error) at the top of build scripts
- Often combined with `set -x` for debug output: `set -x -e`
- Variable validation with conditional exit:
  ```bash
  [ -n "$USERNAME" ] || { echo "Error: no or empty USERNAME"; exit 1; }
  ```

## Logging

**Framework:** `syslog` (Python stdlib) or `sonic_py_common.logger`

**Patterns:**
- Every daemon defines a `SYSLOG_IDENTIFIER` constant matching the daemon name
- Use severity-specific functions: `log_debug()`, `log_info()`, `log_notice()`, `log_warn()`, `log_err()`, `log_crit()`
- Debug logging is gated by a global debug flag in some modules (see `src/sonic-bgpcfgd/bgpcfgd/vars.py`)
- Log messages use `%` string formatting (older code) or f-strings (newer code)

## Comments

**When to Comment:**
- Docstrings on classes and public methods using triple-quote format
- Inline comments for non-obvious logic
- License headers on files from specific vendors (NVIDIA/Mellanox, Nexthop, etc.)

**Docstring Style:**
```python
def get_config_db_table(self, table_name):
    """
    Get table from config_db.
    Args:
        table_name: Name of table want to get.
    Return:
        Table objects.
    """
```
This is a simplified Google-style docstring (not strict reST or NumPy format).

## Function Design

**Size:** Functions tend to be moderate (20-80 lines). Some handler functions are larger.

**Parameters:** Prefer keyword arguments for complex constructors. Use `**kwargs` for template rendering.

**Return Values:**
- Boolean returns for success/failure in handlers
- Tuples `(status, output)` for command execution results
- Dictionaries for configuration data

## Module Design

**Exports:** No `__all__` convention enforced. Imports are explicit.

**Barrel Files:** Not used. Each module is imported directly by path.

**Plugin/Manager Pattern:** Used extensively in `bgpcfgd`:
- Base `Manager` class in `src/sonic-bgpcfgd/bgpcfgd/manager.py`
- Concrete managers: `managers_bgp.py`, `managers_intf.py`, `managers_prefix_list.py`
- Each manager implements `set_handler()` and `del_handler()`

**Decorator-based Registration:**
```python
# src/sonic-containercfgd/containercfgd/containercfgd.py
@containercfgd.config_handler('MockTable')
class MockHandler:
    def handle_config(self, table, key, data):
        pass
```

## CLI Convention (Click Framework)

The `src/sonic-utilities/` project uses Click for CLI commands:
- Commands organized in submodules: `config/main.py`, `show/main.py`
- Nested command groups: `config.config.commands["snmp"].commands["community"].commands["add"]`
- Database object passed via Click `obj` parameter: `runner.invoke(config_cmd, args, obj=db)`
- Tests use `click.testing.CliRunner` to invoke commands

## Environment Variable Convention

**Unit Test Control:**
- `UTILITIES_UNIT_TESTING` — set to `"1"` for single-ASIC, `"2"` for multi-ASIC testing
- `UTILITIES_UNIT_TESTING_TOPOLOGY` — set to `"multi_asic"` for multi-ASIC topology
- `CFGGEN_UNIT_TESTING` — controls mock config DB in config engine tests
- `PLATFORM_API_UNIT_TESTING` — enables mocks for platform API tests
- `CONTAINER_NAME` — required by containerized daemon tests

These environment variables trigger mock database loading in production code (e.g., `src/sonic-utilities/show/main.py`), allowing tests to run without a real Redis/SONiC environment.

---

*Convention analysis: 2025-07-17*
