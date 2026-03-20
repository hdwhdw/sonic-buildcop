# Testing Patterns

**Analysis Date:** 2025-07-17

## Test Framework

**Runner:**
- pytest (primary for all Python testing)
- Config: `sonic-buildimage/pytest.ini` (root-level, minimal — ensures rootdir selection)
- Per-subproject configs in `setup.cfg` files with `[tool:pytest]` sections

**Assertion Library:**
- Standard `assert` statements (pytest native)
- `unittest.TestCase` assertions in some older tests (`self.assertEqual`, `self.assertTrue`)

**Run Commands:**
```bash
# From a subproject root (e.g., src/sonic-utilities/)
python setup.py test         # Runs pytest via setup.cfg alias
pytest tests/                # Direct pytest invocation
pytest tests/test_bgp.py     # Single file
pytest -vv                   # Verbose (configured in some setup.cfg)

# With coverage (configured in src/sonic-dhcp-utilities/setup.cfg)
pytest --cov                 # Coverage enabled via addopts
```

**Test Count:** ~1490 test files across the entire repository.

## Test File Organization

**Location:** Tests are co-located within each subproject, typically in a `tests/` directory:
```
src/sonic-utilities/tests/          # CLI tool tests
src/sonic-bgpcfgd/tests/            # BGP config daemon tests
src/sonic-dhcp-utilities/tests/     # DHCP utility tests
src/sonic-host-services/tests/      # Host service daemon tests
src/sonic-config-engine/tests/      # Config engine tests
src/sonic-containercfgd/tests/      # Container config daemon tests
src/sonic-yang-models/tests/        # YANG model validation tests
platform/mellanox/mlnx-platform-api/tests/  # Mellanox platform API tests
platform/vs/tests/                  # Virtual switch integration tests
```

**Naming Conventions:**
- Newer subprojects: `test_<module>.py` (prefix style) — e.g., `test_sfp.py`, `test_bgp.py`
- `src/sonic-utilities/tests/`: mixed — both `test_<module>.py` and `<module>_test.py` exist
- Test input/fixture directories: `<feature>_input/` (e.g., `bgp_commands_input/`, `acl_input/`)
- Test vector files: `test_<feature>_vectors.py` (e.g., `test_tacacs_vectors.py`)
- Mock table data: `mock_tables/` directory with JSON files per DB

**Structure:**
```
src/sonic-utilities/
├── tests/
│   ├── conftest.py                    # Shared fixtures, env setup
│   ├── mock_tables/                   # Mock Redis DB data (JSON files)
│   │   ├── dbconnector.py             # Mock DB connector (monkey-patches)
│   │   ├── config_db.json             # Mock config DB entries
│   │   ├── appl_db.json               # Mock application DB entries
│   │   ├── asic0/                     # Per-ASIC mock data
│   │   └── asic1/
│   ├── acl_input/                     # Test input data for ACL tests
│   ├── bgp_commands_input/            # Test input data for BGP tests
│   ├── acl_loader_test.py             # Suffix-style test file
│   ├── config_snmp_test.py
│   └── sonic_package_manager/
│       └── test_manager.py            # Prefix-style test file
```

## Test Structure

**Two Main Styles:**

**Style 1: Class-based tests (older/sonic-utilities pattern)**
```python
# src/sonic-utilities/tests/acl_loader_test.py
class TestAclLoader(object):
    @pytest.fixture(scope="class")
    def acl_loader(self):
        yield AclLoader()

    def test_acl_empty(self):
        yang_acl = AclLoader.parse_acl_json(os.path.join(test_path, 'acl_input/empty_acl.json'))
        assert len(yang_acl.acl.acl_sets.acl_set) == 0

    def test_valid(self):
        yang_acl = AclLoader.parse_acl_json(os.path.join(test_path, 'acl_input/acl1.json'))
        assert len(yang_acl.acl.acl_sets.acl_set) == 9
```

**Style 2: Module-level test functions (newer/bgpcfgd pattern)**
```python
# src/sonic-bgpcfgd/tests/test_bgp.py
@patch('bgpcfgd.managers_bgp.log_info')
def test_update_peer_up(mocked_log_info):
    for constant in load_constant_files():
        m = constructor(constant)
        res = m.set_handler("10.10.10.1", {"admin_status": "up"})
        assert res, "Expect True return value for peer update"
        mocked_log_info.assert_called_with("Peer 'default|10.10.10.1' admin state is set to 'up'")
```

**Setup/Teardown Patterns:**
- `@classmethod setup_class(cls)` / `teardown_class(cls)` — for class-scoped setup
- `pytest.fixture(autouse=True)` — for automatic per-test setup
- Environment variable manipulation in setup: `os.environ["UTILITIES_UNIT_TESTING"] = "1"`

## Mocking

**Framework:** `unittest.mock` (stdlib) — used exclusively

**Patterns:**

**1. Decorator-based mocking (most common):**
```python
# src/sonic-bgpcfgd/tests/test_bgp.py
@patch('bgpcfgd.managers_bgp.log_info')
def test_update_peer_up(mocked_log_info):
    m = constructor(constant)
    res = m.set_handler("10.10.10.1", {"admin_status": "up"})
    mocked_log_info.assert_called_with("Peer 'default|10.10.10.1' admin state is set to 'up'")
```

**2. Class-level mock decorators:**
```python
# platform/mellanox/mlnx-platform-api/tests/test_sfp.py
class TestSfp:
    @mock.patch('sonic_platform.device_data.DeviceDataManager.get_linecard_count', mock.MagicMock(return_value=8))
    @mock.patch('sonic_platform.device_data.DeviceDataManager.get_linecard_max_port_count')
    def test_sfp_index(self, mock_max_port):
        mock_max_port.return_value = 16
        sfp = SFP(sfp_index=0, slot_id=1, linecard_port_count=16, lc_name='LINE-CARD1')
        assert sfp.sdk_index == 0
```

**3. Context-manager mocking:**
```python
# src/sonic-dhcp-utilities/tests/conftest.py
@pytest.fixture(scope="function")
def mock_swsscommon_dbconnector_init():
    with patch.object(utils.swsscommon.DBConnector, "__init__", return_value=None) as mock_init:
        yield mock_init
```

**4. Monkey-patching (Redis/DB mocking — sonic-utilities pattern):**
```python
# src/sonic-utilities/tests/mock_tables/dbconnector.py
# Wholesale monkey-patching of swsscommon DB connectors
_old_connect_SonicV2Connector = SonicV2Connector.connect
def connect_SonicV2Connector(self, db_name, retry_on=True):
    self.dbintf.redis_kwargs['topo'] = topo
    self.dbintf.redis_kwargs['namespace'] = self.namespace
    _old_connect_SonicV2Connector(self, db_name, retry_on)
```

**5. Auto-recovery fixture (Mellanox pattern):**
```python
# platform/mellanox/mlnx-platform-api/tests/conftest.py
@pytest.fixture(scope='function', autouse=True)
def auto_recover_mock():
    origin_os_path_exists = os.path.exists
    origin_read_int_from_file = utils.read_int_from_file
    yield
    os.path.exists = origin_os_path_exists
    utils.read_int_from_file = origin_read_int_from_file
```

**6. sys.modules patching (for import-time dependencies):**
```python
# platform/broadcom/sonic-platform-modules-nexthop/test/unit/conftest.py
@pytest.fixture(scope="function", autouse=True)
def patch_dependencies():
    from fixtures.mock_imports_unit_tests import dependencies_dict
    with patch.dict(sys.modules, dependencies_dict()):
        yield
```

**What to Mock:**
- Redis/DB connections (`swsscommon.DBConnector`, `SonicV2Connector`, `ConfigDBConnector`)
- System commands (`subprocess.Popen`, `subprocess.check_output`)
- File system operations (`os.path.exists`, `open`)
- Hardware interfaces (platform-specific SDK calls, `sysfs` reads/writes)
- Syslog output (for verifying log messages)
- External services (`docker`, `systemctl`)

**What NOT to Mock:**
- Click CLI routing logic (use `CliRunner` to test real command paths)
- JSON parsing and data transformation logic
- Template rendering (Jinja2)
- YANG model validation

## Fixtures and Factories

**conftest.py Patterns:**

**Session-scoped mock (host-services):**
```python
# src/sonic-host-services/tests/hostcfgd/conftest.py
@pytest.fixture(autouse=True, scope='session')
def mock_get_device_runtime_metadata():
    device_info.get_device_runtime_metadata = mock.MagicMock(return_value={})
```

**Environment setup (sonic-utilities):**
```python
# src/sonic-utilities/tests/conftest.py
@pytest.fixture(autouse=True)
def setup_env():
    if "PYTHONPATH" not in os.environ:
        os.environ["PYTHONPATH"] = os.getcwd()
```

**Multi-ASIC environment (sonic-utilities):**
```python
# src/sonic-utilities/tests/conftest.py
@pytest.fixture(scope='class')
def setup_multi_asic_env():
    os.environ['UTILITIES_UNIT_TESTING'] = "2"
    os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = "multi_asic"
    from .mock_tables import mock_multi_asic
    importlib.reload(mock_multi_asic)
    dbconnector.load_namespace_config()
    yield
    # teardown restores single-asic state
```

**Test Data (Mock DB Tables):**
```
src/sonic-utilities/tests/mock_tables/
├── config_db.json          # Default mock config DB
├── appl_db.json            # Default mock application DB
├── state_db.json           # Default mock state DB
├── counters_db.json        # Default mock counters DB
├── asic_db.json            # Default mock ASIC DB
├── database_config.json    # Single-namespace DB config
├── database_global.json    # Multi-namespace DB config
├── asic0/                  # Per-ASIC mock data for multi-ASIC
│   ├── config_db.json
│   └── ...
└── asic1/
```

**Test Vectors (host-services pattern):**
```python
# src/sonic-host-services/tests/hostcfgd/test_tacacs_vectors.py
HOSTCFGD_TEST_TACACS_VECTOR = [
    [
        "TACACS",
        {
            "config_db_local": { ... },  # Input config DB state
            "expected_config_db": { ... },  # Expected output
            "expected_subprocess_calls": [ ... ],  # Expected system calls
        }
    ],
]
```

**Test Input Files:**
- JSON files for mock DB data: `tests/mock_tables/*.json`
- XML files for minigraph testing: `src/sonic-config-engine/tests/*.xml`
- INI files for port config: `src/sonic-config-engine/tests/*-port-config.ini`
- Per-feature input directories: `src/sonic-utilities/tests/bgp_commands_input/`

## Coverage

**Requirements:**
- `src/sonic-dhcp-utilities/`: 80% minimum enforced (`fail_under = 80` in `setup.cfg`)
- `src/sonic-utilities/`: Coverage reports generated (HTML, terminal, XML) via `--cov` in `pytest.ini`
- Most other subprojects: No enforced coverage threshold

**Coverage Configuration (sonic-utilities):**
```ini
# src/sonic-utilities/pytest.ini
[pytest]
addopts = --cov-config=.coveragerc --cov --cov-report html --cov-report term --cov-report xml --junitxml=test-results.xml -vv
```

**Coverage Configuration (sonic-dhcp-utilities):**
```ini
# src/sonic-dhcp-utilities/setup.cfg
[coverage:run]
branch = True
source = dhcp_utilities

[coverage:report]
precision = 2
show_missing = True
fail_under = 80
```

## Test Types

**Unit Tests:**
- The vast majority of tests in the repo
- Test individual functions, handlers, and CLI commands in isolation
- Mock all external dependencies (Redis, system calls, file I/O)
- Run without Docker or any SONiC runtime environment
- Located in `tests/` directories within each subproject

**Integration Tests (Virtual Switch):**
- Located at `platform/vs/tests/` and `src/sonic-swss/tests/`
- Require Docker (DVS — Docker Virtual Switch) environment
- Test real Redis interactions and SWSS (Switch State Service) pipeline
- Use `dvslib` helper library for database assertions and polling
- Custom pytest options: `--dvsname`, `--forcedvs`
- Heavier infrastructure: `conftest.py` at `platform/vs/tests/conftest.py` manages Docker lifecycle

**Hardware Tests (Platform-specific):**
- Located at `platform/mellanox/hw-management/hw-mgmt/tests/`
- Split into `offline/` (unit-like, no hardware needed) and `hardware/` (requires physical hardware)
- Shell-based test scripts also exist: `tests/shell/spec/*.sh`

**YANG Model Tests:**
- Located at `src/sonic-yang-models/tests/`
- Validate YANG model schemas against test data
- Use `libyang` Python bindings

**Rust Tests:**
- Standard Rust `#[test]` and `#[tokio::test]` annotations
- Located in `tests/` directories within Rust crates: `src/sonic-dash-ha/crates/*/tests/`
- Run via `cargo test`

## Common Patterns

**Click CLI Testing (sonic-utilities):**
```python
from click.testing import CliRunner
from utilities_common.db import Db
import config.main as config

def test_config_snmp_community_add_new_community_ro(self):
    db = Db()
    runner = CliRunner()
    with mock.patch('utilities_common.cli.run_command') as mock_run_command:
        result = runner.invoke(
            config.config.commands["snmp"].commands["community"].commands["add"],
            ["Everest", "ro"],
            obj=db
        )
    assert result.exit_code == 0
    assert 'SNMP community Everest added to configuration' in result.output
    assert db.cfgdb.get_entry("SNMP_COMMUNITY", "Everest") == {"TYPE": "RO"}
```

**Subprocess Command Testing:**
```python
# src/sonic-config-engine/tests/test_cfggen.py
class TestCfgGen(TestCase):
    def run_script(self, argument, check_stderr=False):
        output = subprocess.check_output(self.script_file + argument)
        return output.decode()

    def test_something(self):
        output = self.run_script(['-m', self.sample_graph, '-v', 'SOME_TABLE'])
        self.assertEqual(output.strip(), expected)
```

**Mock ConfigDB Pattern:**
```python
# Common across many test files
class MockConfigDb(object):
    def __init__(self, config_db_path="tests/test_data/mock_config_db.json"):
        with open(config_db_path, "r") as file:
            self.config_db = json.load(file)

    def get_config_db_table(self, table_name):
        return self.config_db.get(table_name, {})
```

**Error Testing:**
```python
# Using pytest.raises
def test_invalid(self):
    with pytest.raises(AclLoaderException):
        AclLoader.parse_acl_json(os.path.join(test_path, 'acl_input/acl2.json'))

# Using unittest assertions
def test_get_memory_usage(self, mock_open):
    container_id = 'your_container_id'
    with self.assertRaises(SystemExit) as cm:
        memory_checker.get_memory_usage(container_id)
    self.assertEqual(cm.exception.code, 1)
```

**Async Testing (Rust):**
```rust
// src/sonic-dash-ha/crates/swbus-actor/tests/echo.rs
#[tokio::test]
async fn echo() {
    let mut swbus_edge = SwbusEdgeRuntime::new(...);
    swbus_edge.start().await.unwrap();
    // ... test actor messaging
    timeout(Duration::from_secs(3), is_done)
        .await
        .expect("timeout")
        .unwrap();
}
```

## CI/CD Integration

**Azure Pipelines:** Primary CI system (see `azure-pipelines.yml`, `.azure-pipelines/`)
- Builds for multiple platforms: vs, broadcom, mellanox, marvell, etc.
- Multi-architecture: amd64, arm64
- Test stages include VS image build and integration testing
- PR triggers on `master` and `202???` branches

**Test Execution in CI:**
- Unit tests run via `python setup.py test` (mapped to pytest)
- Integration tests run against Docker Virtual Switch (DVS)
- Coverage reports generated as JUnit XML (`test-results.xml`)

---

*Testing analysis: 2025-07-17*
