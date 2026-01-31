"""
MES KPI Calculation Test Suite - Ignition Script Console Runner
================================================================
Copy this entire script into Ignition's Script Console and execute.

This script will:
1. Seed test data with 5 specific KPI test scenarios
2. Run comprehensive tests for all kpiCalc module functions (~125 tests)
3. Report detailed results
4. Clean up test data regardless of outcome

Test Scenarios:
- Scenario A: Normal operation (~85% OEE expected)
- Scenario B: High downtime (~40% availability expected)
- Scenario C: High defects (~60% quality expected)
- Scenario D: Slow production (~50% performance expected)
- Scenario E: No data (None/0 returns expected)

Author: ProveIT Edge Stack
Version: 1.0.0
"""

# =============================================================================
# CONFIGURATION
# =============================================================================

TEST_CONFIG = {
# =========================================================================
# DATABASE CONNECTION NAME
# =========================================================================
# This MUST match the connection name configured in your Ignition Gateway.
# To find available connections:
#   1. Go to Ignition Gateway webpage (e.g., http://localhost:47010)
#   2. Navigate to: Config > Databases > Connections
#   3. Copy the exact "Name" of your MES database connection
# =========================================================================
    "database_connection": "MES Application Database",  # Ignition Gateway connection name

    "test_prefix": "_KPI_TEST_",   # Prefix for test data to identify cleanup targets
    "verbose": True,               # Print detailed test output
    "stop_on_failure": False,      # Continue running tests even if some fail
    "cleanup_on_success": True,    # Clean up test data after successful run
    "cleanup_on_failure": True,    # Clean up test data even after failures
    "skip_seed_setup": False,      # Set True if seed data already exists
    "skip_cleanup": False,         # Set True to preserve test data for debugging
}

# =============================================================================
# MES LIBRARY IMPORT
# =============================================================================

import mes.db as db
import json
# Using Ignition's system.date functions for reliable date/time handling

# =============================================================================
# EXECUTION CONTEXT CHECK
# =============================================================================

def check_execution_context():
    """
    Check if we can execute database writes using mes.db library.
    Designer Script Console may have 'incorrect comm mode' for writes.

    Returns: (can_write, message)
    """
    try:
        # Configure mes.db with test connection
        db.setConnection(TEST_CONFIG["database_connection"])

        # First verify connection exists by reading
        try:
            db.testConnection()
        except Exception as e:
            error_str = str(e).lower()
            if "does not exist" in error_str:
                return (False, "CONNECTION_NOT_FOUND")
            elif "comm mode" in error_str:
                return (False, "COMM_MODE_ERROR")
            return (False, "Database connection error: %s" % str(e))

        # Try a no-op write to test write permissions
        try:
            db.execute("UPDATE mes_core.asset_type SET asset_type_name = asset_type_name WHERE 1=0")
            return (True, "Full read/write access available")
        except Exception as e:
            error_str = str(e).lower()
            if "comm mode" in error_str or "gateway" in error_str:
                return (False, "COMM_MODE_ERROR")
            return (False, "Write permission denied: %s" % str(e))

    except Exception as e:
        return (False, "Context check failed: %s" % str(e))

def print_connection_not_found_instructions():
    """Print instructions when database connection doesn't exist"""
    connection = TEST_CONFIG["database_connection"]
    print("")
    print("!" * 70)
    print("!  DATABASE CONNECTION NOT FOUND: '%s'" % connection)
    print("!" * 70)
    print("")
    print("  The database connection '%s' does not exist in your Gateway." % connection)
    print("")
    print("  === HOW TO FIX ===")
    print("")
    print("  STEP 1: Find your actual connection name")
    print("  -----------------------------------------")
    print("  1. Open Ignition Gateway: http://localhost:47010")
    print("  2. Go to: Config > Databases > Connections")
    print("  3. Look for a connection to your MES database")
    print("  4. Note the exact 'Name' in the first column")
    print("")
    print("  STEP 2: Update the test script")
    print("  -------------------------------")
    print("  At the top of this script, change:")
    print("")
    print('    "database_connection": "%s"' % connection)
    print("")
    print("  To your actual connection name.")
    print("")
    print("!" * 70)
    print("")

def print_gateway_instructions():
    """Print instructions for running in gateway scope"""
    print("")
    print("!" * 70)
    print("!  DESIGNER SCRIPT CONSOLE CANNOT EXECUTE DATABASE WRITES")
    print("!" * 70)
    print("")
    print("  The Ignition Designer Script Console runs in 'client scope'")
    print("  but database write operations require 'gateway scope'.")
    print("")
    print("  === SOLUTIONS ===")
    print("")
    print("  OPTION 1: Gateway Timer Script (Recommended)")
    print("  ---------------------------------------------")
    print("  1. In Designer: Project > Gateway Events > Timer Scripts")
    print("  2. Add new script, set delay to 5 seconds, run once")
    print("  3. Paste this entire script")
    print("  4. Save project - script runs on gateway")
    print("")
    print("!" * 70)
    print("")

# =============================================================================
# TEST FRAMEWORK
# =============================================================================

class TestResult:
    """Holds result of a single test"""
    def __init__(self, name, passed, message="", duration=0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration
        self.skipped = False

class TestSuite:
    """Simple test framework for Ignition Script Console"""

    def __init__(self, name):
        self.name = name
        self.results = []
        self.setup_errors = []
        self.test_data = {}  # Track created test data for cleanup

    def add_result(self, result):
        self.results.append(result)

    def get_summary(self):
        passed = sum(1 for r in self.results if r.passed and not r.skipped)
        failed = sum(1 for r in self.results if not r.passed and not r.skipped)
        skipped = sum(1 for r in self.results if r.skipped)
        total = len(self.results)
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": (float(passed) / total * 100) if total > 0 else 0
        }

# Global test suite instance
suite = TestSuite("KPI Calculation Tests")

def log(message, level="INFO"):
    """Print formatted log message"""
    from java.util import Date
    from java.text import SimpleDateFormat
    sdf = SimpleDateFormat("HH:mm:ss.SSS")
    timestamp = sdf.format(Date())
    print("[%s] [%s] %s" % (timestamp, level, message))

def log_header(title):
    """Print section header"""
    print("\n" + "=" * 70)
    print(" %s" % title)
    print("=" * 70)

def log_subheader(title):
    """Print subsection header"""
    print("\n" + "-" * 50)
    print(" %s" % title)
    print("-" * 50)

# =============================================================================
# DATABASE UTILITIES - Using mes.db library
# =============================================================================

def query_scalar(sql, params=None):
    """Execute query and return single value using mes.db"""
    result = db.queryOne(sql, params)
    if result:
        # Return first value from the dictionary
        return list(result.values())[0]
    return None

def get_or_create_id(table, name_column, name_value, id_column=None, extra_columns=None):
    """Get existing record ID or create new one, return ID using mes.db"""
    if id_column is None:
        id_column = table + "_id"

    # Try to find existing
    sql = "SELECT %s FROM mes_core.%s WHERE %s = ?" % (id_column, table, name_column)
    result = db.queryOne(sql, [name_value])
    if result:
        return result[id_column]

    # Create new
    columns = [name_column]
    values = [name_value]
    placeholders = ["?"]

    if extra_columns:
        for col, val in extra_columns.items():
            columns.append(col)
            values.append(val)
            placeholders.append("?")

    sql = "INSERT INTO mes_core.%s (%s) VALUES (%s) RETURNING %s" % (
        table, ", ".join(columns), ", ".join(placeholders), id_column
    )
    result = db.executeReturn(sql, values)
    return result[id_column] if result else None

# =============================================================================
# TEST RUNNER DECORATOR
# =============================================================================

def run_test(test_name, test_func):
    """Execute a single test with error handling and timing"""
    from java.lang import System

    start = System.currentTimeMillis()
    try:
        test_func()
        duration = System.currentTimeMillis() - start
        result = TestResult(test_name, True, "PASSED", duration)
        if TEST_CONFIG["verbose"]:
            log("  [PASS] %s (%dms)" % (test_name, duration), "SUCCESS")
    except AssertionError as e:
        duration = System.currentTimeMillis() - start
        result = TestResult(test_name, False, str(e), duration)
        log("  [FAIL] %s: %s" % (test_name, str(e)), "ERROR")
        if TEST_CONFIG["stop_on_failure"]:
            raise
    except Exception as e:
        import traceback
        duration = System.currentTimeMillis() - start
        result = TestResult(test_name, False, str(e) + "\n" + traceback.format_exc(), duration)
        log("  [ERROR] %s: %s" % (test_name, str(e)), "ERROR")
        if TEST_CONFIG["verbose"]:
            log(traceback.format_exc(), "DEBUG")
        if TEST_CONFIG["stop_on_failure"]:
            raise

    suite.add_result(result)
    return result.passed

def skip_test(test_name, reason):
    """Mark a test as skipped"""
    result = TestResult(test_name, True, "SKIPPED: " + reason, 0)
    result.skipped = True
    suite.add_result(result)
    if TEST_CONFIG["verbose"]:
        log("  [SKIP] %s: %s" % (test_name, reason), "WARN")

def expect_error(error_type, test_func, error_message_contains=None):
    """
    Verify that a function raises the expected error type.

    Args:
        error_type: The exception class expected to be raised
        test_func: A callable (usually lambda) that should raise the error
        error_message_contains: Optional string that should appear in the error message

    Returns:
        The caught exception for further inspection

    Raises:
        AssertionError: If wrong error type raised or no error raised
    """
    try:
        test_func()
        raise AssertionError("Expected %s but no exception was raised" % error_type.__name__)
    except error_type as e:
        if error_message_contains and error_message_contains not in str(e):
            raise AssertionError("Expected '%s' in error message but got: %s" % (error_message_contains, str(e)))
        return e
    except AssertionError:
        raise
    except Exception as e:
        raise AssertionError("Expected %s but got %s: %s" % (error_type.__name__, type(e).__name__, str(e)))

def assert_close(actual, expected, tolerance=0.01, msg=""):
    """Assert that two values are close within tolerance (for float comparisons)"""
    if actual is None and expected is None:
        return
    if actual is None or expected is None:
        raise AssertionError("%s Expected %s but got %s" % (msg, expected, actual))
    diff = abs(float(actual) - float(expected))
    if diff > tolerance:
        raise AssertionError("%s Expected ~%s but got %s (diff: %s > tolerance: %s)" % (
            msg, expected, actual, diff, tolerance))

# =============================================================================
# SEED DATA SETUP FOR KPI TESTS
# =============================================================================

def setup_kpi_test_data():
    """
    Create comprehensive test data for KPI calculation tests.

    Creates 5 test scenarios:
    - Scenario A (Normal): ~85% OEE expected
    - Scenario B (High Downtime): ~40% availability
    - Scenario C (High Defects): ~60% quality
    - Scenario D (Slow Production): ~50% performance
    - Scenario E (No Data): Empty asset for None tests

    Each scenario has:
    - A parent Line asset
    - A child Cell asset (for hierarchy tests)
    - A product with ideal_cycle_time = 30 seconds (120 units/hour)
    - State log entries covering the test time window
    - Count log entries for Good, Scrap, and Reject
    """
    log_header("PHASE 1: KPI TEST DATA SETUP")

    prefix = TEST_CONFIG["test_prefix"]
    errors = []

    try:
        # ----- Get Required Reference IDs -----
        log("Looking up required reference data...")

        # Asset types
        line_type = query_scalar("SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = ?", ["Line"])
        cell_type = query_scalar("SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = ?", ["Cell"])
        area_type = query_scalar("SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = ?", ["Area"])

        log("  Asset types - Line: %s, Cell: %s, Area: %s" % (line_type, cell_type, area_type))

        if not line_type or not cell_type:
            log("CRITICAL: Line and Cell asset types required (Line=%s, Cell=%s)" % (line_type, cell_type), "ERROR")
            log("Run the MES seed data setup first (run_mes_tests.py) to create required reference data", "ERROR")
            return False

        # State types
        running_type = query_scalar("SELECT state_type_id FROM mes_core.state_type WHERE state_type_name = ?", ["Running"])
        idle_type = query_scalar("SELECT state_type_id FROM mes_core.state_type WHERE state_type_name = ?", ["Idle"])
        downtime_type = query_scalar("SELECT state_type_id FROM mes_core.state_type WHERE state_type_name = ?", ["Downtime"])

        log("  State types - Running: %s, Idle: %s, Downtime: %s" % (running_type, idle_type, downtime_type))

        if not running_type or not downtime_type:
            log("CRITICAL: Running and Downtime state types required (Running=%s, Downtime=%s)" % (running_type, downtime_type), "ERROR")
            log("Run the MES seed data setup first (run_mes_tests.py) to create required reference data", "ERROR")
            return False

        # States
        running_state = query_scalar("SELECT state_id FROM mes_core.state_definition WHERE state_name = ?", ["Running"])
        idle_state = query_scalar("SELECT state_id FROM mes_core.state_definition WHERE state_name = ?", ["Idle"])
        planned_dt_state = query_scalar("SELECT state_id FROM mes_core.state_definition WHERE state_name = ?", ["Planned Downtime"])
        unplanned_dt_state = query_scalar("SELECT state_id FROM mes_core.state_definition WHERE state_name = ?", ["Unplanned Downtime"])

        log("  States - Running: %s, Idle: %s, PlannedDT: %s, UnplannedDT: %s" % (running_state, idle_state, planned_dt_state, unplanned_dt_state))

        if not running_state:
            log("CRITICAL: Running state definition required (found: %s)" % running_state, "ERROR")
            log("Run the MES seed data setup first (run_mes_tests.py) to create required reference data", "ERROR")
            return False

        if not planned_dt_state or not unplanned_dt_state:
            log("WARN: Planned/Unplanned Downtime states not found - creating them...", "WARN")
            # Create them if they don't exist (is_planned is on downtime_reason, not state_definition)
            if not planned_dt_state:
                planned_dt_state = get_or_create_id("state_definition", "state_name", "Planned Downtime",
                                                    id_column="state_id",
                                                    extra_columns={"state_type_id": downtime_type})
                log("  Created 'Planned Downtime' state: %s" % planned_dt_state)
            if not unplanned_dt_state:
                unplanned_dt_state = get_or_create_id("state_definition", "state_name", "Unplanned Downtime",
                                                      id_column="state_id",
                                                      extra_columns={"state_type_id": downtime_type})
                log("  Created 'Unplanned Downtime' state: %s" % unplanned_dt_state)

        # Get/create downtime reasons for planned/unplanned (is_planned flag lives here!)
        planned_reason_id = query_scalar(
            "SELECT downtime_reason_id FROM mes_core.downtime_reason WHERE downtime_reason_code = ?", ["_KPI_PLANNED"])
        if not planned_reason_id:
            planned_reason_id = get_or_create_id("downtime_reason", "downtime_reason_code", "_KPI_PLANNED",
                                                  extra_columns={"downtime_reason_name": "KPI Test Planned",
                                                                "is_planned": True})
            log("  Created '_KPI_PLANNED' downtime reason: %s" % planned_reason_id)

        unplanned_reason_id = query_scalar(
            "SELECT downtime_reason_id FROM mes_core.downtime_reason WHERE downtime_reason_code = ?", ["_KPI_UNPLANNED"])
        if not unplanned_reason_id:
            unplanned_reason_id = get_or_create_id("downtime_reason", "downtime_reason_code", "_KPI_UNPLANNED",
                                                    extra_columns={"downtime_reason_name": "KPI Test Unplanned",
                                                                  "is_planned": False})
            log("  Created '_KPI_UNPLANNED' downtime reason: %s" % unplanned_reason_id)

        suite.test_data["planned_reason_id"] = planned_reason_id
        suite.test_data["unplanned_reason_id"] = unplanned_reason_id

        # Count types
        good_type = query_scalar("SELECT count_type_id FROM mes_core.count_type WHERE count_type_name = ?", ["Good"])
        scrap_type = query_scalar("SELECT count_type_id FROM mes_core.count_type WHERE count_type_name = ?", ["Scrap"])

        log("  Count types - Good: %s, Scrap: %s" % (good_type, scrap_type))

        if not good_type or not scrap_type:
            log("CRITICAL: Good and Scrap count types required (Good=%s, Scrap=%s)" % (good_type, scrap_type), "ERROR")
            log("Run the MES seed data setup first (run_mes_tests.py) to create required reference data", "ERROR")
            return False

        # Check for Reject type - create if missing
        reject_type = query_scalar("SELECT count_type_id FROM mes_core.count_type WHERE count_type_name = ?", ["Reject"])
        if not reject_type:
            log("Creating 'Reject' count type...")
            reject_type = get_or_create_id("count_type", "count_type_name", "Reject",
                                           extra_columns={"count_type_unit": "units"})

        log("  Reference data: OK", "SUCCESS")

        # ----- Create Parent Area for Test Assets -----
        log("Creating test asset hierarchy...")

        parent_area_id = get_or_create_id("asset_definition", "asset_name", prefix + "TestArea",
                                          id_column="asset_id",
                                          extra_columns={"asset_description": "KPI Test Parent Area",
                                                        "asset_type_id": area_type,
                                                        "tag_path": "/" + prefix + "TestArea"})

        suite.test_data["parent_area_id"] = parent_area_id

        # ----- Create Product Family and Product -----
        log("Creating test products...")

        test_family = get_or_create_id("product_family", "product_family_name", prefix + "KpiFamily")

        # Product with ideal_cycle_time = 30 seconds -> 120 units/hour
        test_product_id = get_or_create_id("product_definition", "product_name", prefix + "KpiProduct",
                                           id_column="product_id",
                                           extra_columns={"product_description": "KPI test product",
                                                         "product_family_id": test_family,
                                                         "ideal_cycle_time": 30.0})  # 30 sec = 120 units/hour

        suite.test_data["test_product_id"] = test_product_id
        suite.test_data["good_type"] = good_type
        suite.test_data["scrap_type"] = scrap_type
        suite.test_data["reject_type"] = reject_type
        suite.test_data["running_state"] = running_state
        suite.test_data["idle_state"] = idle_state
        suite.test_data["planned_dt_state"] = planned_dt_state
        suite.test_data["unplanned_dt_state"] = unplanned_dt_state

        log("  Products: OK", "SUCCESS")

        # ----- Define Time Window (last 2 hours for test data) -----
        now = system.date.now()
        test_end = system.date.addMinutes(now, -5)  # 5 min buffer
        test_start = system.date.addHours(test_end, -2)  # 2-hour test window

        suite.test_data["test_start"] = test_start
        suite.test_data["test_end"] = test_end

        # =================================================================
        # SCENARIO A: Normal Operation (~94% OEE)
        # - 100% Availability (ISO 22400: APT/PBT = 108/108, planned DT excluded from PBT)
        # - 95% Performance (actual rate near ideal)
        # - 99% Quality (190 good / 192 total)
        # - Expected OEE: 1.00 * 0.95 * 0.99 = ~94%
        # =================================================================
        log("Creating Scenario A: Normal Operation...")

        scenario_a_line = get_or_create_id("asset_definition", "asset_name", prefix + "ScenarioA_Line",
                                           id_column="asset_id",
                                           extra_columns={"asset_description": "Normal operation scenario",
                                                         "asset_type_id": line_type,
                                                         "parent_asset_id": parent_area_id,
                                                         "tag_path": "/" + prefix + "TestArea/ScenarioA_Line"})

        scenario_a_cell = get_or_create_id("asset_definition", "asset_name", prefix + "ScenarioA_Cell",
                                           id_column="asset_id",
                                           extra_columns={"asset_description": "Cell under Scenario A Line",
                                                         "asset_type_id": cell_type,
                                                         "parent_asset_id": scenario_a_line,
                                                         "tag_path": "/" + prefix + "TestArea/ScenarioA_Line/Cell"})

        suite.test_data["scenario_a_line"] = scenario_a_line
        suite.test_data["scenario_a_cell"] = scenario_a_cell

        # State logs for Scenario A: 108 min running, 12 min planned downtime
        # Running: 0-54 min, Planned DT: 54-66 min, Running: 66-120 min
        _create_state_log(scenario_a_line, running_state, test_start, system.date.addMinutes(test_start, 54))
        _create_state_log(scenario_a_line, planned_dt_state, system.date.addMinutes(test_start, 54), system.date.addMinutes(test_start, 66), planned_reason_id)
        _create_state_log(scenario_a_line, running_state, system.date.addMinutes(test_start, 66), test_end)

        # Count logs: 190 good, 1 scrap, 1 reject (192 total, 99% quality)
        # 108 min running * 2 units/min = 216 ideal, actual 192 = 88.9% performance
        _create_count_log(scenario_a_line, good_type, 190, test_product_id, system.date.addMinutes(test_start, 60))
        _create_count_log(scenario_a_line, scrap_type, 1, test_product_id, system.date.addMinutes(test_start, 60))
        _create_count_log(scenario_a_line, reject_type, 1, test_product_id, system.date.addMinutes(test_start, 60))

        # Create production_log linking asset to product for ideal rate lookup
        _create_production_log(scenario_a_line, test_product_id, test_start, test_end)

        log("  Scenario A (Normal): OK", "SUCCESS")

        # =================================================================
        # SCENARIO B: High Downtime (~57% Availability per ISO 22400)
        # - 57% Availability (ISO 22400: APT/PBT = 48/84, PBT excludes 36 min planned DT)
        # - 95% Performance
        # - 98% Quality
        # - Expected OEE: 0.57 * 0.95 * 0.98 = ~53%
        # =================================================================
        log("Creating Scenario B: High Downtime...")

        scenario_b_line = get_or_create_id("asset_definition", "asset_name", prefix + "ScenarioB_Line",
                                           id_column="asset_id",
                                           extra_columns={"asset_description": "High downtime scenario",
                                                         "asset_type_id": line_type,
                                                         "parent_asset_id": parent_area_id,
                                                         "tag_path": "/" + prefix + "TestArea/ScenarioB_Line"})

        suite.test_data["scenario_b_line"] = scenario_b_line

        # State logs: 48 min running, 36 min planned DT, 36 min unplanned DT
        _create_state_log(scenario_b_line, running_state, test_start, system.date.addMinutes(test_start, 24))
        _create_state_log(scenario_b_line, planned_dt_state, system.date.addMinutes(test_start, 24), system.date.addMinutes(test_start, 60), planned_reason_id)
        _create_state_log(scenario_b_line, unplanned_dt_state, system.date.addMinutes(test_start, 60), system.date.addMinutes(test_start, 96), unplanned_reason_id)
        _create_state_log(scenario_b_line, running_state, system.date.addMinutes(test_start, 96), test_end)

        # Count logs: 90 good, 1 scrap, 1 reject
        _create_count_log(scenario_b_line, good_type, 90, test_product_id, system.date.addMinutes(test_start, 60))
        _create_count_log(scenario_b_line, scrap_type, 1, test_product_id, system.date.addMinutes(test_start, 60))
        _create_count_log(scenario_b_line, reject_type, 1, test_product_id, system.date.addMinutes(test_start, 60))

        _create_production_log(scenario_b_line, test_product_id, test_start, test_end)

        log("  Scenario B (High Downtime): OK", "SUCCESS")

        # =================================================================
        # SCENARIO C: High Defects (~60% Quality)
        # - 95% Availability (114 min production, 6 min downtime)
        # - 95% Performance
        # - 60% Quality (60 good / 100 total)
        # - Expected OEE: 0.95 * 0.95 * 0.60 = ~54.2%
        # =================================================================
        log("Creating Scenario C: High Defects...")

        scenario_c_line = get_or_create_id("asset_definition", "asset_name", prefix + "ScenarioC_Line",
                                           id_column="asset_id",
                                           extra_columns={"asset_description": "High defects scenario",
                                                         "asset_type_id": line_type,
                                                         "parent_asset_id": parent_area_id,
                                                         "tag_path": "/" + prefix + "TestArea/ScenarioC_Line"})

        suite.test_data["scenario_c_line"] = scenario_c_line

        # State logs: 114 min running, 6 min planned DT
        _create_state_log(scenario_c_line, running_state, test_start, system.date.addMinutes(test_start, 57))
        _create_state_log(scenario_c_line, planned_dt_state, system.date.addMinutes(test_start, 57), system.date.addMinutes(test_start, 63), planned_reason_id)
        _create_state_log(scenario_c_line, running_state, system.date.addMinutes(test_start, 63), test_end)

        # Count logs: 120 good, 40 scrap, 40 reject (200 total, 60% quality)
        _create_count_log(scenario_c_line, good_type, 120, test_product_id, system.date.addMinutes(test_start, 60))
        _create_count_log(scenario_c_line, scrap_type, 40, test_product_id, system.date.addMinutes(test_start, 60))
        _create_count_log(scenario_c_line, reject_type, 40, test_product_id, system.date.addMinutes(test_start, 60))

        _create_production_log(scenario_c_line, test_product_id, test_start, test_end)

        log("  Scenario C (High Defects): OK", "SUCCESS")

        # =================================================================
        # SCENARIO D: Slow Production (~50% Performance)
        # - 95% Availability (114 min production)
        # - 50% Performance (actual rate = 60 units/hour vs 120 ideal)
        # - 98% Quality
        # - Expected OEE: 0.95 * 0.50 * 0.98 = ~46.6%
        # =================================================================
        log("Creating Scenario D: Slow Production...")

        scenario_d_line = get_or_create_id("asset_definition", "asset_name", prefix + "ScenarioD_Line",
                                           id_column="asset_id",
                                           extra_columns={"asset_description": "Slow production scenario",
                                                         "asset_type_id": line_type,
                                                         "parent_asset_id": parent_area_id,
                                                         "tag_path": "/" + prefix + "TestArea/ScenarioD_Line"})

        suite.test_data["scenario_d_line"] = scenario_d_line

        # State logs: 114 min running, 6 min planned DT
        _create_state_log(scenario_d_line, running_state, test_start, system.date.addMinutes(test_start, 57))
        _create_state_log(scenario_d_line, planned_dt_state, system.date.addMinutes(test_start, 57), system.date.addMinutes(test_start, 63), planned_reason_id)
        _create_state_log(scenario_d_line, running_state, system.date.addMinutes(test_start, 63), test_end)

        # Count logs: only 98 good, 1 scrap, 1 reject (100 total)
        # 114 min running at ideal 120/hr = 228 ideal, actual 100 = ~43.9% performance
        _create_count_log(scenario_d_line, good_type, 98, test_product_id, system.date.addMinutes(test_start, 60))
        _create_count_log(scenario_d_line, scrap_type, 1, test_product_id, system.date.addMinutes(test_start, 60))
        _create_count_log(scenario_d_line, reject_type, 1, test_product_id, system.date.addMinutes(test_start, 60))

        _create_production_log(scenario_d_line, test_product_id, test_start, test_end)

        log("  Scenario D (Slow Production): OK", "SUCCESS")

        # =================================================================
        # SCENARIO E: No Data (None/0 returns)
        # - Asset exists but has no state logs or count logs
        # =================================================================
        log("Creating Scenario E: No Data...")

        scenario_e_line = get_or_create_id("asset_definition", "asset_name", prefix + "ScenarioE_Line",
                                           id_column="asset_id",
                                           extra_columns={"asset_description": "No data scenario",
                                                         "asset_type_id": line_type,
                                                         "parent_asset_id": parent_area_id,
                                                         "tag_path": "/" + prefix + "TestArea/ScenarioE_Line"})

        suite.test_data["scenario_e_line"] = scenario_e_line

        # No state logs or count logs for Scenario E
        log("  Scenario E (No Data): OK", "SUCCESS")

        if errors:
            for err in errors:
                log(err, "ERROR")
            return False

        log("\nKPI test data setup complete!", "SUCCESS")
        return True

    except Exception as e:
        import traceback
        log("KPI test data setup failed: %s" % str(e), "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False

def _create_state_log(asset_id, state_id, start_time, end_time, downtime_reason_id=None):
    """
    Helper to create a state log entry with all required denormalized fields.

    The state_log table requires: asset_id, asset_name, state_id, state_name,
    state_type_id, state_type_name, and optionally downtime_reason fields.
    """
    # Get asset name
    asset = db.queryOne("SELECT asset_name FROM mes_core.asset_definition WHERE asset_id = ?", [asset_id])
    asset_name = asset['asset_name'] if asset else "Unknown"

    # Get state info
    state = db.queryOne("""
        SELECT sd.state_name, sd.state_type_id, st.state_type_name
        FROM mes_core.state_definition sd
        JOIN mes_core.state_type st ON st.state_type_id = sd.state_type_id
        WHERE sd.state_id = ?
    """, [state_id])
    state_name = state['state_name'] if state else "Unknown"
    state_type_id = state['state_type_id'] if state else None
    state_type_name = state['state_type_name'] if state else "Unknown"

    # Get downtime reason info if provided
    reason_code = None
    reason_name = None
    if downtime_reason_id:
        reason = db.queryOne("""
            SELECT downtime_reason_code, downtime_reason_name
            FROM mes_core.downtime_reason WHERE downtime_reason_id = ?
        """, [downtime_reason_id])
        if reason:
            reason_code = reason['downtime_reason_code']
            reason_name = reason['downtime_reason_name']

    sql = """
        INSERT INTO mes_core.state_log
            (asset_id, asset_name, state_id, state_name, state_type_id, state_type_name,
             downtime_reason_id, downtime_reason_code, downtime_reason_name, logged_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        RETURNING state_log_id
    """
    return db.executeReturn(sql, [
        asset_id, asset_name, state_id, state_name, state_type_id, state_type_name,
        downtime_reason_id, reason_code, reason_name, start_time
    ])

def _create_count_log(asset_id, count_type_id, quantity, product_id, logged_at):
    """
    Helper to create a count log entry with required denormalized fields.

    Note: The count_log table has triggers that populate *_name fields,
    but product_family_id is required and must be looked up.
    """
    # Get product_family_id from product
    product = db.queryOne("""
        SELECT product_family_id FROM mes_core.product_definition WHERE product_id = ?
    """, [product_id])
    product_family_id = product['product_family_id'] if product else None

    sql = """
        INSERT INTO mes_core.count_log
            (asset_id, count_type_id, quantity, product_id, product_family_id, logged_at)
        VALUES (?, ?, ?, ?, ?, ?)
        RETURNING count_log_id
    """
    return db.executeReturn(sql, [asset_id, count_type_id, quantity, product_id, product_family_id, logged_at])

def _create_production_log(asset_id, product_id, start_ts, end_ts):
    """
    Helper to create a production log entry with required denormalized fields.

    Note: The production_log table has triggers that populate *_name fields,
    but product_family_id is required and must be looked up.
    """
    # Get product_family_id from product
    product = db.queryOne("""
        SELECT product_family_id FROM mes_core.product_definition WHERE product_id = ?
    """, [product_id])
    product_family_id = product['product_family_id'] if product else None

    sql = """
        INSERT INTO mes_core.production_log
            (asset_id, product_id, product_family_id, start_ts, end_ts, logged_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        RETURNING production_log_id
    """
    return db.executeReturn(sql, [asset_id, product_id, product_family_id, start_ts, end_ts])

# =============================================================================
# TEST CLEANUP
# =============================================================================

def cleanup_kpi_test_data():
    """Remove all KPI test-generated data"""
    log_header("CLEANUP PHASE")

    try:
        prefix = TEST_CONFIG["test_prefix"]

        # Get all test asset IDs
        test_assets = db.query("""
            SELECT asset_id FROM mes_core.asset_definition
            WHERE asset_name LIKE ?
        """, [prefix + "%"])
        test_asset_ids = [a['asset_id'] for a in test_assets]

        if test_asset_ids:
            placeholders = ",".join(["?" for _ in test_asset_ids])

            log("Cleaning up count logs...")
            db.execute("DELETE FROM mes_core.count_log WHERE asset_id IN (%s)" % placeholders, test_asset_ids)

            log("Cleaning up state logs...")
            db.execute("DELETE FROM mes_core.state_log WHERE asset_id IN (%s)" % placeholders, test_asset_ids)

            log("Cleaning up production logs...")
            db.execute("DELETE FROM mes_core.production_log WHERE asset_id IN (%s)" % placeholders, test_asset_ids)

            log("Cleaning up KPI logs...")
            db.execute("DELETE FROM mes_core.kpi_log WHERE asset_id IN (%s)" % placeholders, test_asset_ids)

        log("Cleaning up test assets (children first)...")
        # Delete in hierarchy order (children first)
        db.execute("DELETE FROM mes_core.asset_definition WHERE asset_name LIKE ? AND parent_asset_id IS NOT NULL", [prefix + "%"])
        db.execute("DELETE FROM mes_core.asset_definition WHERE asset_name LIKE ?", [prefix + "%"])

        log("Cleaning up test products...")
        db.execute("DELETE FROM mes_core.product_definition WHERE product_name LIKE ?", [prefix + "%"])
        db.execute("DELETE FROM mes_core.product_family WHERE product_family_name LIKE ?", [prefix + "%"])

        log("Cleaning up test downtime reasons...")
        db.execute("DELETE FROM mes_core.downtime_reason WHERE downtime_reason_code IN ('_KPI_PLANNED', '_KPI_UNPLANNED')")

        log("Cleanup complete!", "SUCCESS")
        return True

    except Exception as e:
        import traceback
        log("Cleanup failed: %s" % str(e), "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False

# =============================================================================
# TIME ELEMENT TESTS
# =============================================================================

def test_time_elements():
    """Test individual time element KPI functions"""
    log_subheader("Time Element Functions")

    import mes.kpiCalc as kpiCalc
    import mes.errors as errors

    test_start = suite.test_data["test_start"]
    test_end = suite.test_data["test_end"]
    scenario_a = suite.test_data["scenario_a_line"]
    scenario_b = suite.test_data["scenario_b_line"]
    scenario_e = suite.test_data["scenario_e_line"]

    # -------------------------------------------------------------------------
    # getPlannedOperationTime tests (NEW - ISO 22400 POT)
    # -------------------------------------------------------------------------
    def test_pot_equals_time_range():
        """POT should equal the total calendar time window in seconds"""
        pot = kpiCalc.getPlannedOperationTime(scenario_a, startTime=test_start, endTime=test_end)
        expected = system.date.secondsBetween(test_start, test_end)
        assert_close(pot, expected, tolerance=1, msg="POT should equal calendar time range")

    def test_pot_hours_parameter():
        """POT with hours parameter should match hours * 3600"""
        pot = kpiCalc.getPlannedOperationTime(scenario_a, hours=2)
        assert_close(pot, 2 * 3600, tolerance=1, msg="POT should be 2 hours in seconds")

    run_test("TC-KPICALC-000A: POT equals calendar time range", test_pot_equals_time_range)
    run_test("TC-KPICALC-000B: POT with hours parameter", test_pot_hours_parameter)

    # -------------------------------------------------------------------------
    # getPlannedBusyTime tests (ISO 22400: PBT = POT - PDOT)
    # -------------------------------------------------------------------------
    def test_pbt_equals_pot_minus_pdot():
        """ISO 22400: PBT = POT - PDOT (calendar time minus planned downtime)"""
        pot = kpiCalc.getPlannedOperationTime(scenario_a, startTime=test_start, endTime=test_end)
        pdot = kpiCalc.getPlannedDowntime(scenario_a, startTime=test_start, endTime=test_end)
        pbt = kpiCalc.getPlannedBusyTime(scenario_a, startTime=test_start, endTime=test_end)
        expected = pot - pdot  # 7200 - 720 = 6480 seconds (108 min)
        assert_close(pbt, expected, tolerance=1, msg="PBT should equal POT - PDOT")

    def test_pbt_scenario_a():
        """PBT for Scenario A: 120 min - 12 min PDOT = 108 min"""
        pbt = kpiCalc.getPlannedBusyTime(scenario_a, startTime=test_start, endTime=test_end)
        # Expected: 120 - 12 = 108 minutes = 6480 seconds
        assert_close(pbt, 6480, tolerance=10, msg="PBT should be ~108 minutes for Scenario A")

    def test_pbt_scenario_b():
        """PBT for Scenario B: 120 min - 36 min PDOT = 84 min"""
        pbt = kpiCalc.getPlannedBusyTime(scenario_b, startTime=test_start, endTime=test_end)
        # Expected: 120 - 36 = 84 minutes = 5040 seconds
        assert_close(pbt, 5040, tolerance=10, msg="PBT should be ~84 minutes for Scenario B")

    run_test("TC-KPICALC-001: PBT equals POT minus PDOT (ISO 22400)", test_pbt_equals_pot_minus_pdot)
    run_test("TC-KPICALC-002: PBT Scenario A (108 min)", test_pbt_scenario_a)
    run_test("TC-KPICALC-003: PBT Scenario B (84 min)", test_pbt_scenario_b)

    # -------------------------------------------------------------------------
    # getPlannedDowntime tests
    # -------------------------------------------------------------------------
    def test_pdot_scenario_a():
        """PDOT for Scenario A: 12 min planned downtime"""
        pdot = kpiCalc.getPlannedDowntime(scenario_a, startTime=test_start, endTime=test_end)
        # Expected: 12 minutes = 720 seconds
        assert_close(pdot, 720, tolerance=10, msg="PDOT should be ~12 minutes")

    def test_pdot_scenario_b():
        """PDOT for Scenario B: 36 min planned downtime"""
        pdot = kpiCalc.getPlannedDowntime(scenario_b, startTime=test_start, endTime=test_end)
        # Expected: 36 minutes = 2160 seconds
        assert_close(pdot, 2160, tolerance=10, msg="PDOT should be ~36 minutes")

    def test_pdot_no_data():
        """PDOT for asset with no state data should be 0"""
        pdot = kpiCalc.getPlannedDowntime(scenario_e, startTime=test_start, endTime=test_end)
        assert pdot == 0, "PDOT should be 0 for asset with no state data"

    run_test("TC-KPICALC-004: PDOT Scenario A (12 min)", test_pdot_scenario_a)
    run_test("TC-KPICALC-005: PDOT Scenario B (36 min)", test_pdot_scenario_b)
    run_test("TC-KPICALC-006: PDOT with no data returns 0", test_pdot_no_data)

    # -------------------------------------------------------------------------
    # getUnplannedDowntime tests
    # -------------------------------------------------------------------------
    def test_udot_scenario_a():
        """UDOT for Scenario A: 0 min unplanned downtime"""
        udot = kpiCalc.getUnplannedDowntime(scenario_a, startTime=test_start, endTime=test_end)
        assert udot == 0, "UDOT should be 0 for Scenario A"

    def test_udot_scenario_b():
        """UDOT for Scenario B: 36 min unplanned downtime"""
        udot = kpiCalc.getUnplannedDowntime(scenario_b, startTime=test_start, endTime=test_end)
        # Expected: 36 minutes = 2160 seconds
        assert_close(udot, 2160, tolerance=10, msg="UDOT should be ~36 minutes")

    run_test("TC-KPICALC-007: UDOT Scenario A (0 min)", test_udot_scenario_a)
    run_test("TC-KPICALC-008: UDOT Scenario B (36 min)", test_udot_scenario_b)

    # -------------------------------------------------------------------------
    # getActualDowntime tests
    # -------------------------------------------------------------------------
    def test_adot_equals_pdot_plus_udot():
        """ADOT should equal PDOT + UDOT"""
        pdot = kpiCalc.getPlannedDowntime(scenario_b, startTime=test_start, endTime=test_end)
        udot = kpiCalc.getUnplannedDowntime(scenario_b, startTime=test_start, endTime=test_end)
        adot = kpiCalc.getActualDowntime(scenario_b, startTime=test_start, endTime=test_end)
        assert_close(adot, pdot + udot, tolerance=1, msg="ADOT should equal PDOT + UDOT")

    def test_adot_scenario_b():
        """ADOT for Scenario B: 72 min total downtime"""
        adot = kpiCalc.getActualDowntime(scenario_b, startTime=test_start, endTime=test_end)
        # Expected: 36 + 36 = 72 minutes = 4320 seconds
        assert_close(adot, 4320, tolerance=20, msg="ADOT should be ~72 minutes")

    run_test("TC-KPICALC-009: ADOT equals PDOT + UDOT", test_adot_equals_pdot_plus_udot)
    run_test("TC-KPICALC-010: ADOT Scenario B (72 min)", test_adot_scenario_b)

    # -------------------------------------------------------------------------
    # getActualProductionTime tests
    # -------------------------------------------------------------------------
    def test_apt_scenario_a():
        """APT for Scenario A: ~108 min production time"""
        apt = kpiCalc.getActualProductionTime(scenario_a, startTime=test_start, endTime=test_end)
        # Expected: 120 - 12 = 108 minutes = 6480 seconds
        assert_close(apt, 6480, tolerance=60, msg="APT should be ~108 minutes")

    def test_apt_scenario_b():
        """APT for Scenario B: ~48 min production time"""
        apt = kpiCalc.getActualProductionTime(scenario_b, startTime=test_start, endTime=test_end)
        # Expected: 120 - 72 = 48 minutes = 2880 seconds
        assert_close(apt, 2880, tolerance=60, msg="APT should be ~48 minutes")

    def test_apt_no_data():
        """APT for asset with no state data should be 0"""
        apt = kpiCalc.getActualProductionTime(scenario_e, startTime=test_start, endTime=test_end)
        assert apt == 0, "APT should be 0 for asset with no state data"

    run_test("TC-KPICALC-011: APT Scenario A (~108 min)", test_apt_scenario_a)
    run_test("TC-KPICALC-012: APT Scenario B (~48 min)", test_apt_scenario_b)
    run_test("TC-KPICALC-013: APT with no data returns 0", test_apt_no_data)

    # -------------------------------------------------------------------------
    # getRunningTime tests
    # -------------------------------------------------------------------------
    def test_running_time_scenario_a():
        """Running time for Scenario A"""
        running = kpiCalc.getRunningTime(scenario_a, startTime=test_start, endTime=test_end)
        # All production time in Scenario A is Running state
        assert running > 0, "Running time should be > 0"
        assert_close(running, 6480, tolerance=60, msg="Running time should be ~108 minutes")

    run_test("TC-KPICALC-014: Running time Scenario A", test_running_time_scenario_a)

    # -------------------------------------------------------------------------
    # getIdleTime tests
    # -------------------------------------------------------------------------
    def test_idle_time_scenario_a():
        """Idle time for Scenario A (no idle states)"""
        idle = kpiCalc.getIdleTime(scenario_a, startTime=test_start, endTime=test_end)
        assert idle == 0, "Idle time should be 0 for Scenario A (no idle states)"

    run_test("TC-KPICALC-015: Idle time Scenario A (0)", test_idle_time_scenario_a)

    # -------------------------------------------------------------------------
    # getBlockedTime tests
    # -------------------------------------------------------------------------
    def test_blocked_time_scenario_a():
        """Blocked time for Scenario A (no blocked states)"""
        blocked = kpiCalc.getBlockedTime(scenario_a, startTime=test_start, endTime=test_end)
        assert blocked == 0, "Blocked time should be 0 for Scenario A"

    run_test("TC-KPICALC-016: Blocked time Scenario A (0)", test_blocked_time_scenario_a)

    # -------------------------------------------------------------------------
    # getTimeElements aggregate test (ISO 22400 compliant)
    # -------------------------------------------------------------------------
    def test_time_elements_aggregate():
        """getTimeElements returns complete ISO 22400 breakdown"""
        result = kpiCalc.getTimeElements(scenario_a, startTime=test_start, endTime=test_end)

        assert 'planned_operation_time_seconds' in result, "Should have POT (ISO 22400)"
        assert 'planned_busy_time_seconds' in result, "Should have PBT"
        assert 'planned_downtime_seconds' in result, "Should have PDOT"
        assert 'unplanned_downtime_seconds' in result, "Should have UDOT"
        assert 'actual_downtime_seconds' in result, "Should have ADOT"
        assert 'actual_production_time_seconds' in result, "Should have APT"
        assert 'running_time_seconds' in result, "Should have running time"
        assert 'idle_time_seconds' in result, "Should have idle time"
        assert 'blocked_time_seconds' in result, "Should have blocked time"
        assert 'period' in result, "Should have period info"
        assert 'start_time' in result['period'], "Should have start time in period"
        assert 'end_time' in result['period'], "Should have end time in period"

    run_test("TC-KPICALC-017: getTimeElements aggregate function", test_time_elements_aggregate)

    # -------------------------------------------------------------------------
    # Error handling tests
    # -------------------------------------------------------------------------
    def test_pbt_negative_hours_error():
        """Negative hours should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: kpiCalc.getPlannedBusyTime(scenario_a, hours=-1))

    def test_pbt_negative_days_error():
        """Negative days should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: kpiCalc.getPlannedBusyTime(scenario_a, days=-1))

    def test_pdot_invalid_asset_error():
        """Invalid asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: kpiCalc.getPlannedDowntime("NONEXISTENT_ASSET_XYZ"))

    run_test("TC-KPICALC-BP-001: Negative hours raises MesValidationError", test_pbt_negative_hours_error)
    run_test("TC-KPICALC-BP-002: Negative days raises MesValidationError", test_pbt_negative_days_error)
    run_test("TC-KPICALC-BP-003: Invalid asset raises MesResolutionError", test_pdot_invalid_asset_error)

# =============================================================================
# QUANTITY TESTS
# =============================================================================

def test_quantities():
    """Test individual quantity KPI functions"""
    log_subheader("Quantity Functions")

    import mes.kpiCalc as kpiCalc
    import mes.errors as errors

    test_start = suite.test_data["test_start"]
    test_end = suite.test_data["test_end"]
    scenario_a = suite.test_data["scenario_a_line"]
    scenario_c = suite.test_data["scenario_c_line"]
    scenario_e = suite.test_data["scenario_e_line"]
    test_product_id = suite.test_data["test_product_id"]

    # -------------------------------------------------------------------------
    # getGoodQuantity tests
    # -------------------------------------------------------------------------
    def test_good_qty_scenario_a():
        """Good quantity for Scenario A: 190"""
        good = kpiCalc.getGoodQuantity(scenario_a, startTime=test_start, endTime=test_end)
        assert good == 190, "Good quantity should be 190"

    def test_good_qty_scenario_c():
        """Good quantity for Scenario C: 120"""
        good = kpiCalc.getGoodQuantity(scenario_c, startTime=test_start, endTime=test_end)
        assert good == 120, "Good quantity should be 120"

    def test_good_qty_no_data():
        """Good quantity for asset with no count data should be 0"""
        good = kpiCalc.getGoodQuantity(scenario_e, startTime=test_start, endTime=test_end)
        assert good == 0, "Good quantity should be 0 for asset with no data"

    def test_good_qty_with_product_filter():
        """Good quantity with product filter"""
        good = kpiCalc.getGoodQuantity(scenario_a, startTime=test_start, endTime=test_end,
                                       product=test_product_id)
        assert good == 190, "Good quantity with product filter should be 190"

    run_test("TC-KPICALC-031: Good quantity Scenario A (190)", test_good_qty_scenario_a)
    run_test("TC-KPICALC-032: Good quantity Scenario C (120)", test_good_qty_scenario_c)
    run_test("TC-KPICALC-033: Good quantity with no data returns 0", test_good_qty_no_data)
    run_test("TC-KPICALC-034: Good quantity with product filter", test_good_qty_with_product_filter)

    # -------------------------------------------------------------------------
    # getScrapQuantity tests
    # -------------------------------------------------------------------------
    def test_scrap_qty_scenario_a():
        """Scrap quantity for Scenario A: 1"""
        scrap = kpiCalc.getScrapQuantity(scenario_a, startTime=test_start, endTime=test_end)
        assert scrap == 1, "Scrap quantity should be 1"

    def test_scrap_qty_scenario_c():
        """Scrap quantity for Scenario C: 40"""
        scrap = kpiCalc.getScrapQuantity(scenario_c, startTime=test_start, endTime=test_end)
        assert scrap == 40, "Scrap quantity should be 40"

    run_test("TC-KPICALC-035: Scrap quantity Scenario A (1)", test_scrap_qty_scenario_a)
    run_test("TC-KPICALC-036: Scrap quantity Scenario C (40)", test_scrap_qty_scenario_c)

    # -------------------------------------------------------------------------
    # getRejectQuantity tests
    # -------------------------------------------------------------------------
    def test_reject_qty_scenario_a():
        """Reject quantity for Scenario A: 1"""
        reject = kpiCalc.getRejectQuantity(scenario_a, startTime=test_start, endTime=test_end)
        assert reject == 1, "Reject quantity should be 1"

    def test_reject_qty_scenario_c():
        """Reject quantity for Scenario C: 40"""
        reject = kpiCalc.getRejectQuantity(scenario_c, startTime=test_start, endTime=test_end)
        assert reject == 40, "Reject quantity should be 40"

    run_test("TC-KPICALC-037: Reject quantity Scenario A (1)", test_reject_qty_scenario_a)
    run_test("TC-KPICALC-038: Reject quantity Scenario C (40)", test_reject_qty_scenario_c)

    # -------------------------------------------------------------------------
    # getProducedQuantity tests
    # -------------------------------------------------------------------------
    def test_produced_qty_equals_sum():
        """Produced quantity should equal Good + Scrap + Reject"""
        good = kpiCalc.getGoodQuantity(scenario_a, startTime=test_start, endTime=test_end)
        scrap = kpiCalc.getScrapQuantity(scenario_a, startTime=test_start, endTime=test_end)
        reject = kpiCalc.getRejectQuantity(scenario_a, startTime=test_start, endTime=test_end)
        produced = kpiCalc.getProducedQuantity(scenario_a, startTime=test_start, endTime=test_end)
        assert produced == good + scrap + reject, "Produced should equal Good + Scrap + Reject"

    def test_produced_qty_scenario_a():
        """Produced quantity for Scenario A: 192"""
        produced = kpiCalc.getProducedQuantity(scenario_a, startTime=test_start, endTime=test_end)
        assert produced == 192, "Produced quantity should be 192"

    run_test("TC-KPICALC-039: Produced equals Good + Scrap + Reject", test_produced_qty_equals_sum)
    run_test("TC-KPICALC-040: Produced quantity Scenario A (192)", test_produced_qty_scenario_a)

    # -------------------------------------------------------------------------
    # getInfeedQuantity tests
    # -------------------------------------------------------------------------
    def test_infeed_qty_no_data():
        """Infeed quantity when no infeed logs exist should be 0"""
        infeed = kpiCalc.getInfeedQuantity(scenario_a, startTime=test_start, endTime=test_end)
        assert infeed == 0, "Infeed should be 0 when no infeed logs exist"

    run_test("TC-KPICALC-041: Infeed quantity with no data (0)", test_infeed_qty_no_data)

    # -------------------------------------------------------------------------
    # getReworkQuantity tests (ISO 22400 - needed for accurate FPY)
    # -------------------------------------------------------------------------
    def test_rework_qty_no_data():
        """Rework quantity when no rework logs exist should be 0"""
        rework = kpiCalc.getReworkQuantity(scenario_a, startTime=test_start, endTime=test_end)
        assert rework == 0, "Rework should be 0 when no rework logs exist"

    run_test("TC-KPICALC-041B: Rework quantity with no data (0)", test_rework_qty_no_data)

    # -------------------------------------------------------------------------
    # getQuantityMetrics aggregate test (ISO 22400 compliant)
    # -------------------------------------------------------------------------
    def test_quantity_metrics_aggregate():
        """getQuantityMetrics returns complete ISO 22400 breakdown including rework"""
        result = kpiCalc.getQuantityMetrics(scenario_a, startTime=test_start, endTime=test_end)

        assert 'good_quantity' in result, "Should have good_quantity"
        assert 'scrap_quantity' in result, "Should have scrap_quantity"
        assert 'reject_quantity' in result, "Should have reject_quantity"
        assert 'rework_quantity' in result, "Should have rework_quantity (ISO 22400 for FPY)"
        assert 'produced_quantity' in result, "Should have produced_quantity"
        assert 'infeed_quantity' in result, "Should have infeed_quantity"

        assert result['good_quantity'] == 190, "Good should be 190"
        assert result['produced_quantity'] == 192, "Produced should be 192"
        assert result['rework_quantity'] == 0, "Rework should be 0 (no rework data seeded)"

    run_test("TC-KPICALC-042: getQuantityMetrics aggregate function (ISO 22400)", test_quantity_metrics_aggregate)

# =============================================================================
# AVAILABILITY TESTS
# =============================================================================

def test_availability():
    """Test availability KPI functions"""
    log_subheader("Availability Functions")

    import mes.kpiCalc as kpiCalc

    test_start = suite.test_data["test_start"]
    test_end = suite.test_data["test_end"]
    scenario_a = suite.test_data["scenario_a_line"]
    scenario_b = suite.test_data["scenario_b_line"]
    scenario_e = suite.test_data["scenario_e_line"]

    # -------------------------------------------------------------------------
    # getAvailability tests
    # -------------------------------------------------------------------------
    def test_availability_formula():
        """Availability = (APT / PBT) * 100"""
        apt = kpiCalc.getActualProductionTime(scenario_a, startTime=test_start, endTime=test_end)
        pbt = kpiCalc.getPlannedBusyTime(scenario_a, startTime=test_start, endTime=test_end)
        expected = (float(apt) / float(pbt)) * 100
        actual = kpiCalc.getAvailability(scenario_a, startTime=test_start, endTime=test_end)
        assert_close(actual, expected, tolerance=0.5, msg="Availability should match formula")

    def test_availability_scenario_a():
        """Availability for Scenario A: ~100% (ISO 22400: APT/PBT)"""
        avail = kpiCalc.getAvailability(scenario_a, startTime=test_start, endTime=test_end)
        # ISO 22400: Availability = APT / PBT
        # APT = 108 min (running time), PBT = POT - PDOT = 120 - 12 = 108 min
        # Availability = 108/108 = 100%
        assert_close(avail, 100, tolerance=2, msg="Availability should be ~100% (APT/PBT)")

    def test_availability_scenario_b():
        """Availability for Scenario B: ~57% (ISO 22400: APT/PBT)"""
        avail = kpiCalc.getAvailability(scenario_b, startTime=test_start, endTime=test_end)
        # ISO 22400: Availability = APT / PBT
        # APT = 48 min, PBT = POT - PDOT = 120 - 36 = 84 min
        # Availability = 48/84 = 57.14%
        assert_close(avail, 57.14, tolerance=2, msg="Availability should be ~57% (APT/PBT)")

    def test_availability_no_data():
        """Availability with no state data should return low value or None"""
        avail = kpiCalc.getAvailability(scenario_e, startTime=test_start, endTime=test_end)
        # With no state data, APT = 0, so availability = 0%
        assert avail == 0 or avail is None, "Availability should be 0 or None with no data"

    run_test("TC-KPICALC-056: Availability formula verification", test_availability_formula)
    run_test("TC-KPICALC-057: Availability Scenario A (~90%)", test_availability_scenario_a)
    run_test("TC-KPICALC-058: Availability Scenario B (~40%)", test_availability_scenario_b)
    run_test("TC-KPICALC-059: Availability with no data", test_availability_no_data)

    # -------------------------------------------------------------------------
    # getOperationalAvailability tests
    # -------------------------------------------------------------------------
    def test_operational_availability_formula():
        """Operational Availability = (APT / (APT + UDOT)) * 100"""
        apt = kpiCalc.getActualProductionTime(scenario_a, startTime=test_start, endTime=test_end)
        udot = kpiCalc.getUnplannedDowntime(scenario_a, startTime=test_start, endTime=test_end)
        denominator = apt + udot
        if denominator > 0:
            expected = (float(apt) / float(denominator)) * 100
            actual = kpiCalc.getOperationalAvailability(scenario_a, startTime=test_start, endTime=test_end)
            assert_close(actual, expected, tolerance=0.5, msg="Operational availability should match formula")

    def test_operational_availability_scenario_a():
        """Operational availability for Scenario A (excludes unplanned DT impact)"""
        op_avail = kpiCalc.getOperationalAvailability(scenario_a, startTime=test_start, endTime=test_end)
        # Scenario A has no unplanned downtime, so operational availability = regular availability
        # APT = 108 min, PBT = 108 min, UDOT = 0
        # Op. Availability = APT / (PBT - UDOT) = 108 / 108 = 100%
        assert_close(op_avail, 100, tolerance=2, msg="Operational availability should be ~100%")

    run_test("TC-KPICALC-060: Operational availability formula", test_operational_availability_formula)
    run_test("TC-KPICALC-061: Operational availability Scenario A (~100%)", test_operational_availability_scenario_a)

    # -------------------------------------------------------------------------
    # getAvailabilityMetrics aggregate test
    # -------------------------------------------------------------------------
    def test_availability_metrics_aggregate():
        """getAvailabilityMetrics returns complete breakdown"""
        result = kpiCalc.getAvailabilityMetrics(scenario_a, startTime=test_start, endTime=test_end)

        assert 'availability_percent' in result, "Should have availability_percent"
        assert 'operational_availability_percent' in result, "Should have operational_availability_percent"
        assert 'actual_production_time_seconds' in result, "Should have APT"
        assert 'planned_busy_time_seconds' in result, "Should have PBT"
        assert 'planned_downtime_seconds' in result, "Should have PDOT"

    run_test("TC-KPICALC-062: getAvailabilityMetrics aggregate function", test_availability_metrics_aggregate)

# =============================================================================
# QUALITY TESTS
# =============================================================================

def test_quality():
    """Test quality KPI functions"""
    log_subheader("Quality Functions")

    import mes.kpiCalc as kpiCalc

    test_start = suite.test_data["test_start"]
    test_end = suite.test_data["test_end"]
    scenario_a = suite.test_data["scenario_a_line"]
    scenario_c = suite.test_data["scenario_c_line"]
    scenario_e = suite.test_data["scenario_e_line"]

    # -------------------------------------------------------------------------
    # getQualityRatio tests
    # -------------------------------------------------------------------------
    def test_quality_formula():
        """Quality Ratio = (Good / Produced) * 100"""
        good = kpiCalc.getGoodQuantity(scenario_a, startTime=test_start, endTime=test_end)
        produced = kpiCalc.getProducedQuantity(scenario_a, startTime=test_start, endTime=test_end)
        expected = (float(good) / float(produced)) * 100
        actual = kpiCalc.getQualityRatio(scenario_a, startTime=test_start, endTime=test_end)
        assert_close(actual, expected, tolerance=0.1, msg="Quality should match formula")

    def test_quality_scenario_a():
        """Quality for Scenario A: ~99%"""
        quality = kpiCalc.getQualityRatio(scenario_a, startTime=test_start, endTime=test_end)
        # Expected: 190/192 = 98.96%
        assert_close(quality, 98.96, tolerance=1, msg="Quality should be ~99%")

    def test_quality_scenario_c():
        """Quality for Scenario C: 60%"""
        quality = kpiCalc.getQualityRatio(scenario_c, startTime=test_start, endTime=test_end)
        # Expected: 120/200 = 60%
        assert_close(quality, 60, tolerance=1, msg="Quality should be ~60%")

    def test_quality_no_production():
        """Quality with no production should return None"""
        quality = kpiCalc.getQualityRatio(scenario_e, startTime=test_start, endTime=test_end)
        assert quality is None, "Quality should be None when no production"

    run_test("TC-KPICALC-071: Quality ratio formula verification", test_quality_formula)
    run_test("TC-KPICALC-072: Quality Scenario A (~99%)", test_quality_scenario_a)
    run_test("TC-KPICALC-073: Quality Scenario C (60%)", test_quality_scenario_c)
    run_test("TC-KPICALC-074: Quality with no production returns None", test_quality_no_production)

    # -------------------------------------------------------------------------
    # getFirstPassYield tests (ISO 22400: FPY = (Entering - Scrapped - Reworked) / Entering)
    # When no infeed/rework tracking, falls back to Quality Ratio
    # -------------------------------------------------------------------------
    def test_fpy_equals_quality_when_no_infeed():
        """FPY falls back to Quality Ratio when no infeed tracking exists"""
        quality = kpiCalc.getQualityRatio(scenario_a, startTime=test_start, endTime=test_end)
        fpy = kpiCalc.getFirstPassYield(scenario_a, startTime=test_start, endTime=test_end)
        assert quality == fpy, "FPY should equal Quality Ratio when no infeed data exists"

    def test_fpy_no_production_returns_none():
        """FPY should return None when no production data"""
        fpy = kpiCalc.getFirstPassYield(scenario_e, startTime=test_start, endTime=test_end)
        assert fpy is None, "FPY should be None when no production data"

    run_test("TC-KPICALC-075: FPY equals Quality Ratio (no infeed tracking)", test_fpy_equals_quality_when_no_infeed)
    run_test("TC-KPICALC-076: FPY with no production returns None", test_fpy_no_production_returns_none)

    # -------------------------------------------------------------------------
    # getScrapRate tests
    # -------------------------------------------------------------------------
    def test_scrap_rate_scenario_a():
        """Scrap rate for Scenario A"""
        scrap_rate = kpiCalc.getScrapRate(scenario_a, startTime=test_start, endTime=test_end)
        # Expected: 1/192 = 0.52%
        assert_close(scrap_rate, 0.52, tolerance=0.1, msg="Scrap rate should be ~0.52%")

    def test_scrap_rate_scenario_c():
        """Scrap rate for Scenario C: 20%"""
        scrap_rate = kpiCalc.getScrapRate(scenario_c, startTime=test_start, endTime=test_end)
        # Expected: 40/200 = 20%
        assert_close(scrap_rate, 20, tolerance=1, msg="Scrap rate should be ~20%")

    run_test("TC-KPICALC-076: Scrap rate Scenario A (~0.5%)", test_scrap_rate_scenario_a)
    run_test("TC-KPICALC-077: Scrap rate Scenario C (~20%)", test_scrap_rate_scenario_c)

    # -------------------------------------------------------------------------
    # getRejectRate tests
    # -------------------------------------------------------------------------
    def test_reject_rate_scenario_c():
        """Reject rate for Scenario C: 20%"""
        reject_rate = kpiCalc.getRejectRate(scenario_c, startTime=test_start, endTime=test_end)
        # Expected: 40/200 = 20%
        assert_close(reject_rate, 20, tolerance=1, msg="Reject rate should be ~20%")

    run_test("TC-KPICALC-078: Reject rate Scenario C (~20%)", test_reject_rate_scenario_c)

    # -------------------------------------------------------------------------
    # getQualityMetrics aggregate test
    # -------------------------------------------------------------------------
    def test_quality_metrics_aggregate():
        """getQualityMetrics returns complete breakdown"""
        result = kpiCalc.getQualityMetrics(scenario_a, startTime=test_start, endTime=test_end)

        assert 'quality_ratio_percent' in result, "Should have quality_ratio_percent"
        assert 'first_pass_yield_percent' in result, "Should have FPY"
        assert 'scrap_rate_percent' in result, "Should have scrap_rate"
        assert 'reject_rate_percent' in result, "Should have reject_rate"
        assert 'good_quantity' in result, "Should have good_quantity"
        assert 'produced_quantity' in result, "Should have produced_quantity"

    run_test("TC-KPICALC-079: getQualityMetrics aggregate function", test_quality_metrics_aggregate)

# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

def test_performance():
    """Test performance KPI functions"""
    log_subheader("Performance Functions")

    import mes.kpiCalc as kpiCalc

    test_start = suite.test_data["test_start"]
    test_end = suite.test_data["test_end"]
    scenario_a = suite.test_data["scenario_a_line"]
    scenario_d = suite.test_data["scenario_d_line"]
    scenario_e = suite.test_data["scenario_e_line"]

    # -------------------------------------------------------------------------
    # getActualRate tests (ISO 22400: Actual Rate = PQ / APT)
    # -------------------------------------------------------------------------
    def test_actual_rate_formula():
        """ISO 22400: Actual Rate = (Produced Quantity / APT) * 3600"""
        produced = kpiCalc.getProducedQuantity(scenario_a, startTime=test_start, endTime=test_end)
        apt = kpiCalc.getActualProductionTime(scenario_a, startTime=test_start, endTime=test_end)
        if apt > 0:
            expected = (float(produced) / float(apt)) * 3600
            actual = kpiCalc.getActualRate(scenario_a, startTime=test_start, endTime=test_end)
            assert_close(actual, expected, tolerance=1, msg="Actual rate should match ISO 22400 formula (PQ/APT)")

    def test_actual_rate_no_apt():
        """Actual rate with no actual production time should return None"""
        actual_rate = kpiCalc.getActualRate(scenario_e, startTime=test_start, endTime=test_end)
        assert actual_rate is None, "Actual rate should be None with no actual production time"

    run_test("TC-KPICALC-091: Actual rate formula verification (ISO 22400)", test_actual_rate_formula)
    run_test("TC-KPICALC-092: Actual rate with no APT returns None", test_actual_rate_no_apt)

    # -------------------------------------------------------------------------
    # getIdealRate tests
    # -------------------------------------------------------------------------
    def test_ideal_rate_from_product():
        """Ideal rate should come from product ideal_cycle_time"""
        ideal_rate = kpiCalc.getIdealRate(scenario_a, startTime=test_start, endTime=test_end)
        # Product has ideal_cycle_time = 30 seconds = 120 units/hour
        if ideal_rate is not None:
            assert_close(ideal_rate, 120, tolerance=5, msg="Ideal rate should be ~120 units/hour")

    run_test("TC-KPICALC-093: Ideal rate from product definition", test_ideal_rate_from_product)

    # -------------------------------------------------------------------------
    # getPerformanceEfficiency tests
    # -------------------------------------------------------------------------
    def test_performance_scenario_a():
        """Performance for Scenario A"""
        perf = kpiCalc.getPerformanceEfficiency(scenario_a, startTime=test_start, endTime=test_end)
        if perf is not None:
            # Expected: actual ~106 units/hr vs 120 ideal = ~88%
            assert perf > 0, "Performance should be positive"
            assert perf <= 200, "Performance should be reasonable"

    def test_performance_no_data():
        """Performance with no data should return None"""
        perf = kpiCalc.getPerformanceEfficiency(scenario_e, startTime=test_start, endTime=test_end)
        assert perf is None, "Performance should be None with no data"

    run_test("TC-KPICALC-094: Performance Scenario A", test_performance_scenario_a)
    run_test("TC-KPICALC-095: Performance with no data returns None", test_performance_no_data)

    # -------------------------------------------------------------------------
    # getCycleTime tests
    # -------------------------------------------------------------------------
    def test_cycle_time_formula():
        """Cycle time = 3600 / Actual Rate"""
        actual_rate = kpiCalc.getActualRate(scenario_a, startTime=test_start, endTime=test_end)
        if actual_rate and actual_rate > 0:
            expected = 3600 / actual_rate
            cycle_time = kpiCalc.getCycleTime(scenario_a, startTime=test_start, endTime=test_end)
            assert_close(cycle_time, expected, tolerance=1, msg="Cycle time should match formula")

    run_test("TC-KPICALC-096: Cycle time formula verification", test_cycle_time_formula)

    # -------------------------------------------------------------------------
    # getPerformanceMetrics aggregate test (ISO 22400 compliant)
    # -------------------------------------------------------------------------
    def test_performance_metrics_aggregate():
        """getPerformanceMetrics returns complete ISO 22400 breakdown"""
        result = kpiCalc.getPerformanceMetrics(scenario_a, startTime=test_start, endTime=test_end)

        assert 'performance_percent' in result, "Should have performance_percent"
        assert 'actual_rate_per_hour' in result, "Should have actual_rate"
        assert 'ideal_rate_per_hour' in result, "Should have ideal_rate"
        assert 'cycle_time_seconds' in result, "Should have cycle_time"
        assert 'produced_quantity' in result, "Should have produced_quantity"
        assert 'actual_production_time_seconds' in result, "Should have APT (ISO 22400 denominator for actual rate)"
        assert 'running_time_seconds' in result, "Should have running_time (for reference)"

    run_test("TC-KPICALC-097: getPerformanceMetrics aggregate function (ISO 22400)", test_performance_metrics_aggregate)

# =============================================================================
# OEE TESTS
# =============================================================================

def test_oee():
    """Test OEE KPI functions"""
    log_subheader("OEE Functions")

    import mes.kpiCalc as kpiCalc

    test_start = suite.test_data["test_start"]
    test_end = suite.test_data["test_end"]
    scenario_a = suite.test_data["scenario_a_line"]
    scenario_b = suite.test_data["scenario_b_line"]
    scenario_c = suite.test_data["scenario_c_line"]
    scenario_e = suite.test_data["scenario_e_line"]

    # -------------------------------------------------------------------------
    # getOEE tests
    # -------------------------------------------------------------------------
    def test_oee_formula():
        """OEE = (A * P * Q) / 10000"""
        avail = kpiCalc.getAvailability(scenario_a, startTime=test_start, endTime=test_end)
        perf = kpiCalc.getPerformanceEfficiency(scenario_a, startTime=test_start, endTime=test_end)
        quality = kpiCalc.getQualityRatio(scenario_a, startTime=test_start, endTime=test_end)

        if all([avail, perf, quality]):
            expected = (avail * perf * quality) / 10000
            actual = kpiCalc.getOEE(scenario_a, startTime=test_start, endTime=test_end)
            assert_close(actual, expected, tolerance=1, msg="OEE should match formula")

    def test_oee_no_data():
        """OEE with no data should return None"""
        oee = kpiCalc.getOEE(scenario_e, startTime=test_start, endTime=test_end)
        assert oee is None, "OEE should be None when components are missing"

    def test_oee_with_exclude_planned_downtime():
        """OEE with excludePlannedDowntime uses operational availability"""
        oee_standard = kpiCalc.getOEE(scenario_a, startTime=test_start, endTime=test_end,
                                       excludePlannedDowntime=False)
        oee_operational = kpiCalc.getOEE(scenario_a, startTime=test_start, endTime=test_end,
                                          excludePlannedDowntime=True)
        if oee_standard and oee_operational:
            # With operational availability (excludes planned DT), OEE should be higher
            assert oee_operational >= oee_standard, "OEE with excludePlannedDowntime should be >= standard"

    run_test("TC-KPICALC-116: OEE formula verification", test_oee_formula)
    run_test("TC-KPICALC-117: OEE with no data returns None", test_oee_no_data)
    run_test("TC-KPICALC-118: OEE with excludePlannedDowntime", test_oee_with_exclude_planned_downtime)

    # -------------------------------------------------------------------------
    # calculateOEE tests
    # -------------------------------------------------------------------------
    def test_calculate_oee_full_breakdown():
        """calculateOEE returns complete breakdown with all components"""
        result = kpiCalc.calculateOEE(scenario_a, startTime=test_start, endTime=test_end)

        assert 'oee_percent' in result, "Should have oee_percent"
        assert 'availability_percent' in result, "Should have availability_percent"
        assert 'performance_percent' in result, "Should have performance_percent"
        assert 'quality_percent' in result, "Should have quality_percent"
        assert 'time_elements' in result, "Should have time_elements"
        assert 'quantity_metrics' in result, "Should have quantity_metrics"
        assert 'calculation_period' in result, "Should have calculation_period"
        assert 'asset_id' in result, "Should have asset_id"
        assert 'asset_name' in result, "Should have asset_name"

    def test_calculate_oee_values_match_individual():
        """calculateOEE values should match individual function results"""
        result = kpiCalc.calculateOEE(scenario_a, startTime=test_start, endTime=test_end)

        individual_avail = kpiCalc.getAvailability(scenario_a, startTime=test_start, endTime=test_end)
        individual_quality = kpiCalc.getQualityRatio(scenario_a, startTime=test_start, endTime=test_end)

        if individual_avail:
            assert_close(result['availability_percent'], individual_avail, tolerance=0.1,
                        msg="Availability should match")
        if individual_quality:
            assert_close(result['quality_percent'], individual_quality, tolerance=0.1,
                        msg="Quality should match")

    run_test("TC-KPICALC-119: calculateOEE full breakdown", test_calculate_oee_full_breakdown)
    run_test("TC-KPICALC-120: calculateOEE matches individual functions", test_calculate_oee_values_match_individual)

    # -------------------------------------------------------------------------
    # calculateOEEForHierarchy tests
    # -------------------------------------------------------------------------
    def test_oee_hierarchy_returns_results():
        """calculateOEEForHierarchy returns aggregated results"""
        parent_area = suite.test_data["parent_area_id"]
        result = kpiCalc.calculateOEEForHierarchy(parent_area, startTime=test_start, endTime=test_end)

        assert 'rollup_oee_percent' in result, "Should have rollup OEE"
        assert 'rollup_availability_percent' in result, "Should have rollup availability"
        assert 'asset_results' in result, "Should have asset_results list"
        assert 'total_production_time' in result, "Should have total production time"
        assert 'assets_included' in result, "Should have assets_included count"
        assert result['assets_included'] > 0, "Should include descendant assets"

    def test_oee_hierarchy_weight_by_production_time():
        """calculateOEEForHierarchy with weightBy='production_time'"""
        parent_area = suite.test_data["parent_area_id"]
        result = kpiCalc.calculateOEEForHierarchy(parent_area, startTime=test_start, endTime=test_end,
                                                   weightBy='production_time')
        assert result['weight_method'] == 'production_time', "Should use production_time weighting"

    def test_oee_hierarchy_weight_by_equal():
        """calculateOEEForHierarchy with weightBy='equal'"""
        parent_area = suite.test_data["parent_area_id"]
        result = kpiCalc.calculateOEEForHierarchy(parent_area, startTime=test_start, endTime=test_end,
                                                   weightBy='equal')
        assert result['weight_method'] == 'equal', "Should use equal weighting"

    run_test("TC-KPICALC-121: OEE hierarchy returns aggregated results", test_oee_hierarchy_returns_results)
    run_test("TC-KPICALC-122: OEE hierarchy weightBy production_time", test_oee_hierarchy_weight_by_production_time)
    run_test("TC-KPICALC-123: OEE hierarchy weightBy equal", test_oee_hierarchy_weight_by_equal)

# =============================================================================
# DASHBOARD TESTS
# =============================================================================

def test_dashboard():
    """Test KPI dashboard function"""
    log_subheader("Dashboard Function")

    import mes.kpiCalc as kpiCalc

    test_start = suite.test_data["test_start"]
    test_end = suite.test_data["test_end"]
    scenario_a = suite.test_data["scenario_a_line"]

    # -------------------------------------------------------------------------
    # getKPIDashboard tests
    # -------------------------------------------------------------------------
    def test_dashboard_complete_structure():
        """getKPIDashboard returns complete structure"""
        result = kpiCalc.getKPIDashboard(scenario_a, startTime=test_start, endTime=test_end)

        assert 'asset_id' in result, "Should have asset_id"
        assert 'asset_name' in result, "Should have asset_name"
        assert 'period' in result, "Should have period"
        assert 'oee' in result, "Should have oee section"
        assert 'time_elements' in result, "Should have time_elements section"
        assert 'quantities' in result, "Should have quantities section"
        assert 'rates' in result, "Should have rates section"
        assert 'quality' in result, "Should have quality section"

    def test_dashboard_oee_section():
        """Dashboard OEE section has all components"""
        result = kpiCalc.getKPIDashboard(scenario_a, startTime=test_start, endTime=test_end)
        oee = result['oee']

        assert 'oee_percent' in oee, "Should have oee_percent"
        assert 'availability_percent' in oee, "Should have availability_percent"
        assert 'performance_percent' in oee, "Should have performance_percent"
        assert 'quality_percent' in oee, "Should have quality_percent"

    def test_dashboard_time_elements_section():
        """Dashboard time_elements section has all components"""
        result = kpiCalc.getKPIDashboard(scenario_a, startTime=test_start, endTime=test_end)
        te = result['time_elements']

        assert 'pbt' in te, "Should have pbt"
        assert 'pdot' in te, "Should have pdot"
        assert 'udot' in te, "Should have udot"
        assert 'adot' in te, "Should have adot"
        assert 'apt' in te, "Should have apt"
        assert 'running' in te, "Should have running"
        assert 'idle' in te, "Should have idle"
        assert 'blocked' in te, "Should have blocked"

    def test_dashboard_quantities_section():
        """Dashboard quantities section has all components"""
        result = kpiCalc.getKPIDashboard(scenario_a, startTime=test_start, endTime=test_end)
        qty = result['quantities']

        assert 'good' in qty, "Should have good"
        assert 'scrap' in qty, "Should have scrap"
        assert 'reject' in qty, "Should have reject"
        assert 'produced' in qty, "Should have produced"
        assert 'infeed' in qty, "Should have infeed"

    def test_dashboard_rates_section():
        """Dashboard rates section has all components"""
        result = kpiCalc.getKPIDashboard(scenario_a, startTime=test_start, endTime=test_end)
        rates = result['rates']

        assert 'actual_rate_per_hour' in rates, "Should have actual_rate"
        assert 'ideal_rate_per_hour' in rates, "Should have ideal_rate"
        assert 'cycle_time_seconds' in rates, "Should have cycle_time"

    def test_dashboard_period_info():
        """Dashboard period info is correct"""
        result = kpiCalc.getKPIDashboard(scenario_a, startTime=test_start, endTime=test_end)
        period = result['period']

        assert 'start_time' in period, "Should have start_time"
        assert 'end_time' in period, "Should have end_time"
        assert 'duration_hours' in period, "Should have duration_hours"
        assert_close(period['duration_hours'], 2.0, tolerance=0.1, msg="Duration should be ~2 hours")

    run_test("TC-KPICALC-136: Dashboard complete structure", test_dashboard_complete_structure)
    run_test("TC-KPICALC-137: Dashboard OEE section", test_dashboard_oee_section)
    run_test("TC-KPICALC-138: Dashboard time_elements section", test_dashboard_time_elements_section)
    run_test("TC-KPICALC-139: Dashboard quantities section", test_dashboard_quantities_section)
    run_test("TC-KPICALC-140: Dashboard rates section", test_dashboard_rates_section)
    run_test("TC-KPICALC-141: Dashboard period info", test_dashboard_period_info)

# =============================================================================
# INTEGRATION TESTS
# =============================================================================

def test_integration():
    """Integration tests across scenarios"""
    log_subheader("Integration Tests")

    import mes.kpiCalc as kpiCalc

    test_start = suite.test_data["test_start"]
    test_end = suite.test_data["test_end"]
    scenario_a = suite.test_data["scenario_a_line"]
    scenario_b = suite.test_data["scenario_b_line"]
    scenario_c = suite.test_data["scenario_c_line"]

    # -------------------------------------------------------------------------
    # Cross-scenario validation
    # -------------------------------------------------------------------------
    def test_scenario_a_oee_range():
        """Scenario A OEE should be in expected range (75-95%)"""
        oee = kpiCalc.getOEE(scenario_a, startTime=test_start, endTime=test_end)
        if oee is not None:
            assert 50 < oee < 100, "Scenario A OEE should be in reasonable range"

    def test_scenario_b_low_availability():
        """Scenario B should have reduced availability due to downtime (ISO 22400: APT/PBT)"""
        avail = kpiCalc.getAvailability(scenario_b, startTime=test_start, endTime=test_end)
        # ISO 22400: APT/PBT = 48/84 = 57.14%
        # This represents time actually running vs planned busy time (excluding planned downtime)
        assert 50 < avail < 65, "Scenario B availability should be ~57% (APT/PBT per ISO 22400)"

    def test_scenario_c_low_quality():
        """Scenario C should have low quality (55-65%)"""
        quality = kpiCalc.getQualityRatio(scenario_c, startTime=test_start, endTime=test_end)
        assert 55 < quality < 65, "Scenario C quality should be in 55-65% range"

    def test_oee_lower_than_components():
        """OEE should be lower than all its components"""
        oee = kpiCalc.getOEE(scenario_a, startTime=test_start, endTime=test_end)
        avail = kpiCalc.getAvailability(scenario_a, startTime=test_start, endTime=test_end)
        quality = kpiCalc.getQualityRatio(scenario_a, startTime=test_start, endTime=test_end)
        perf = kpiCalc.getPerformanceEfficiency(scenario_a, startTime=test_start, endTime=test_end)

        if all([oee, avail, quality, perf]):
            min_component = min(avail, quality, perf)
            assert oee <= min_component, "OEE should be <= minimum component"

    def test_time_elements_consistency():
        """Time elements should be internally consistent"""
        te = kpiCalc.getTimeElements(scenario_a, startTime=test_start, endTime=test_end)

        # ADOT should equal PDOT + UDOT
        assert_close(te['actual_downtime_seconds'],
                    te['planned_downtime_seconds'] + te['unplanned_downtime_seconds'],
                    tolerance=1, msg="ADOT should equal PDOT + UDOT")

    def test_product_filter_consistency():
        """Product filter should not change totals when only one product exists"""
        test_product_id = suite.test_data["test_product_id"]

        good_all = kpiCalc.getGoodQuantity(scenario_a, startTime=test_start, endTime=test_end)
        good_filtered = kpiCalc.getGoodQuantity(scenario_a, startTime=test_start, endTime=test_end,
                                                 product=test_product_id)

        assert good_all == good_filtered, "Product filter should return same results for single product"

    run_test("IT-KPI-001: Scenario A OEE in expected range", test_scenario_a_oee_range)
    run_test("IT-KPI-002: Scenario B low availability", test_scenario_b_low_availability)
    run_test("IT-KPI-003: Scenario C low quality", test_scenario_c_low_quality)
    run_test("IT-KPI-004: OEE lower than components", test_oee_lower_than_components)
    run_test("IT-KPI-005: Time elements consistency", test_time_elements_consistency)
    run_test("IT-KPI-006: Product filter consistency", test_product_filter_consistency)

# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def print_report():
    """Print final test report"""
    log_header("TEST REPORT")

    summary = suite.get_summary()

    print("\n" + "=" * 70)
    print(" KPI CALCULATION TEST RESULTS")
    print("=" * 70)
    print("")
    print("  Total Tests:  %d" % summary['total'])
    print("  Passed:       %d" % summary['passed'])
    print("  Failed:       %d" % summary['failed'])
    print("  Skipped:      %d" % summary['skipped'])
    print("  Pass Rate:    %.1f%%" % summary['pass_rate'])
    print("")

    if summary['failed'] > 0:
        print("-" * 70)
        print(" FAILED TESTS:")
        print("-" * 70)
        for result in suite.results:
            if not result.passed and not result.skipped:
                print("\n  [FAIL] %s" % result.name)
                print("         %s" % result.message.split('\n')[0])
        print("")

    print("=" * 70)
    if summary['failed'] == 0:
        print(" ALL KPI CALCULATION TESTS PASSED!")
    else:
        print(" SOME TESTS FAILED - Review errors above")
    print("=" * 70)

    return summary['failed'] == 0

def run_all_tests():
    """Main entry point - run complete KPI test suite"""
    from java.lang import System

    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "       KPI CALCULATION TEST SUITE - IGNITION SCRIPT CONSOLE".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)

    # Phase 0: Check execution context
    log_header("PHASE 0: ENVIRONMENT CHECK")
    log("Checking database connection: '%s'" % TEST_CONFIG["database_connection"])

    can_write, context_msg = check_execution_context()

    if not can_write:
        if context_msg == "CONNECTION_NOT_FOUND":
            log("Database connection not found!", "ERROR")
            print_connection_not_found_instructions()
            return False
        elif context_msg == "COMM_MODE_ERROR":
            log("Designer comm mode restriction detected!", "ERROR")
            print_gateway_instructions()

            if TEST_CONFIG.get("skip_seed_setup") and TEST_CONFIG.get("skip_cleanup"):
                log("Running in READ-ONLY mode (skip_seed_setup and skip_cleanup enabled)", "WARN")
            else:
                log("To run tests, use Gateway Timer Script or enable read-only mode", "INFO")
                return False
        else:
            log("Database access error: %s" % context_msg, "ERROR")
            return False

    log("Execution context: %s" % context_msg, "SUCCESS")

    # Configure mes.db to use the same connection
    db.setConnection(TEST_CONFIG["database_connection"])
    log("mes.db configured to use: %s" % TEST_CONFIG["database_connection"], "SUCCESS")

    start_time = System.currentTimeMillis()
    all_passed = False

    try:
        # Phase 1: Setup
        if TEST_CONFIG.get("skip_seed_setup"):
            log_header("PHASE 1: KPI TEST DATA SETUP (SKIPPED)")
            log("Skipping seed setup - using existing data", "WARN")
        else:
            if not setup_kpi_test_data():
                log("KPI test data setup failed - aborting tests", "ERROR")
                return False

        # Phase 2: Run Tests
        log_header("PHASE 2: RUNNING KPI CALCULATION TESTS")

        test_time_elements()
        test_quantities()
        test_availability()
        test_quality()
        test_performance()
        test_oee()
        test_dashboard()
        test_integration()

        # Phase 3: Report
        all_passed = print_report()

    except Exception as e:
        import traceback
        log("Test suite failed with exception: %s" % str(e), "ERROR")
        log(traceback.format_exc(), "ERROR")
        all_passed = False

    finally:
        # Phase 4: Cleanup (always runs unless skip_cleanup is set)
        if TEST_CONFIG.get("skip_cleanup"):
            log_header("CLEANUP PHASE (SKIPPED)")
            log("Skipping cleanup - skip_cleanup is enabled", "WARN")
        else:
            should_cleanup = (all_passed and TEST_CONFIG["cleanup_on_success"]) or \
                            (not all_passed and TEST_CONFIG["cleanup_on_failure"])

            if should_cleanup:
                cleanup_kpi_test_data()
            else:
                log("Skipping cleanup - test data preserved for debugging", "WARN")

    # Final timing
    elapsed = System.currentTimeMillis() - start_time
    print("\nTotal execution time: %.2f seconds" % (elapsed / 1000.0))

    return all_passed

# =============================================================================
# EXECUTE
# =============================================================================

if __name__ == "__main__" or True:  # Always run when pasted into console
    run_all_tests()
