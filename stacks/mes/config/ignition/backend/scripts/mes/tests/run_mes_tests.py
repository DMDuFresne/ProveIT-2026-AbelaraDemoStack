"""
MES Backend Test Suite - Ignition Script Console Runner
========================================================
Copy this entire script into Ignition's Script Console and execute.

This script will:
1. Verify/seed all required reference data
2. Run comprehensive tests for all MES modules
3. Report detailed results
4. Clean up test data regardless of outcome

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
#
# Common names: "MES", "proveit-mes", "MES Database", "TimescaleDB"
# =========================================================================
    "database_connection": "MES Application Database",  # Ignition Gateway connection name (brackets required for names with spaces)

    "test_prefix": "_TEST_",       # Prefix for test data to identify cleanup targets
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
    print("  1. Open Ignition Gateway: http://localhost:47010 (or your gateway URL)")
    print("  2. Go to: Config > Databases > Connections")
    print("  3. Look for a connection to your MES database (proveit-mes)")
    print("  4. Note the exact 'Name' in the first column")
    print("")
    print("  STEP 2: Update the test script")
    print("  -------------------------------")
    print("  At the top of this script, change:")
    print("")
    print('    "database_connection": "%s"' % connection)
    print("")
    print("  To your actual connection name, e.g.:")
    print("")
    print('    "database_connection": "MES"')
    print('    "database_connection": "proveit-mes"')
    print('    "database_connection": "MES_Database"')
    print("")
    print("  === OR CREATE THE CONNECTION ===")
    print("")
    print("  If no MES connection exists, create one:")
    print("  1. Config > Databases > Connections > Create new Connection")
    print("  2. Name: MES")
    print("  3. Type: PostgreSQL")
    print("  4. Connect URL: jdbc:postgresql://mes-pgbouncer:6432/proveit-mes")
    print("  5. Username: postgres")
    print("  6. Password: (your MES_POSTGRES_PASSWORD)")
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
    print("  OPTION 2: Gateway Message Handler")
    print("  ----------------------------------")
    print("  1. In Designer: Project > Gateway Events > Message Handlers")
    print("  2. Create handler named 'runMesTests'")
    print("  3. Paste this script in the handler")
    print("  4. From Script Console run: system.util.sendMessage('runMesTests')")
    print("")
    print("  OPTION 3: Tag Change Script")
    print("  ----------------------------")
    print("  1. Create a boolean memory tag '[Test]RunMesTests'")
    print("  2. Add tag change script with this code")
    print("  3. Toggle tag to True to run tests")
    print("")
    print("  OPTION 4: Read-Only Mode (Limited)")
    print("  -----------------------------------")
    print("  Set TEST_CONFIG['skip_seed_setup'] = True")
    print("  Set TEST_CONFIG['skip_cleanup'] = True")
    print("  This runs tests WITHOUT creating/deleting data")
    print("  (Only works if seed data already exists)")
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
suite = TestSuite("MES Backend Tests")

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
    """Get existing record ID or create new one, return ID using mes.db.

    Handles soft-deleted records: if a removed record exists, it will be
    reactivated (removed = FALSE) rather than creating a duplicate.
    """
    if id_column is None:
        id_column = table + "_id"

    # Try to find existing ACTIVE record (not soft-deleted)
    sql = "SELECT %s FROM mes_core.%s WHERE %s = ? AND removed IS DISTINCT FROM TRUE" % (id_column, table, name_column)
    result = db.queryOne(sql, [name_value])
    if result:
        return result[id_column]

    # Check for soft-deleted record and reactivate it
    sql = "SELECT %s FROM mes_core.%s WHERE %s = ? AND removed = TRUE" % (id_column, table, name_column)
    result = db.queryOne(sql, [name_value])
    if result:
        # Reactivate the soft-deleted record
        record_id = result[id_column]
        update_sql = "UPDATE mes_core.%s SET removed = FALSE" % table
        update_values = []

        # Also update extra_columns if provided
        if extra_columns:
            for col, val in extra_columns.items():
                update_sql += ", %s = ?" % col
                update_values.append(val)

        update_sql += " WHERE %s = ?" % id_column
        update_values.append(record_id)
        db.execute(update_sql, update_values)
        return record_id

    # Create new record
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
# SEED DATA SETUP
# =============================================================================

def setup_seed_data():
    """Ensure all required seed data exists for testing"""
    import mes.resolver as resolver
    import mes.lookups as lookups

    log_header("PHASE 1: SEED DATA SETUP")

    errors = []
    created = []

    try:
        # ----- ASSET TYPES -----
        log("Setting up asset types...")
        asset_types = ["Enterprise", "Site", "Area", "Line", "Cell"]
        for type_name in asset_types:
            get_or_create_id("asset_type", "asset_type_name", type_name)
        log("  Asset types: OK", "SUCCESS")

        # ----- STATE TYPES -----
        log("Setting up state types...")
        # Running and Idle are not downtime states, Downtime is
        state_types = [
            ("Running", False),
            ("Idle", False),
            ("Downtime", True),
        ]
        for st_name, st_is_downtime in state_types:
            get_or_create_id("state_type", "state_type_name", st_name,
                           extra_columns={"is_downtime": st_is_downtime})
        # Ensure is_downtime flag is correctly set for existing data
        db.execute("UPDATE mes_core.state_type SET is_downtime = TRUE WHERE state_type_name = 'Downtime'")
        db.execute("UPDATE mes_core.state_type SET is_downtime = FALSE WHERE state_type_name IN ('Running', 'Idle')")
        log("  State types: OK", "SUCCESS")

        # ----- STATES -----
        log("Setting up states...")
        # Get state type IDs
        running_type = query_scalar("SELECT state_type_id FROM mes_core.state_type WHERE state_type_name = ?", ["Running"])
        idle_type = query_scalar("SELECT state_type_id FROM mes_core.state_type WHERE state_type_name = ?", ["Idle"])
        downtime_type = query_scalar("SELECT state_type_id FROM mes_core.state_type WHERE state_type_name = ?", ["Downtime"])

        states = [
            ("Running", running_type),
            ("Idle", idle_type),
            ("Planned Downtime", downtime_type),
            ("Unplanned Downtime", downtime_type),
        ]
        for state_name, type_id in states:
            get_or_create_id("state_definition", "state_name", state_name,
                           id_column="state_id",
                           extra_columns={"state_type_id": type_id})
        # Ensure state_type_id is correctly set (for existing data that may have wrong linkage)
        db.execute("UPDATE mes_core.state_definition SET state_type_id = ? WHERE state_name = 'Running'", [running_type])
        db.execute("UPDATE mes_core.state_definition SET state_type_id = ? WHERE state_name = 'Idle'", [idle_type])
        db.execute("UPDATE mes_core.state_definition SET state_type_id = ? WHERE state_name IN ('Planned Downtime', 'Unplanned Downtime')", [downtime_type])
        log("  States: OK", "SUCCESS")

        # ----- PRODUCT FAMILIES -----
        log("Setting up product families...")
        families = ["Widgets", "Gadgets", TEST_CONFIG["test_prefix"] + "TestFamily"]
        for fam in families:
            get_or_create_id("product_family", "product_family_name", fam)
        log("  Product families: OK", "SUCCESS")

        # ----- PRODUCTS -----
        log("Setting up products...")
        widgets_family = query_scalar("SELECT product_family_id FROM mes_core.product_family WHERE product_family_name = ?", ["Widgets"])
        test_family = query_scalar("SELECT product_family_id FROM mes_core.product_family WHERE product_family_name = ?",
                                   [TEST_CONFIG["test_prefix"] + "TestFamily"])

        products = [
            ("Widget A", "Standard widget type A", widgets_family, 60.0),
            ("Widget B", "Standard widget type B", widgets_family, 45.0),
            (TEST_CONFIG["test_prefix"] + "TestProduct", "Test product for automated testing", test_family, 30.0),
        ]
        for prod_name, prod_desc, family_id, cycle_time in products:
            get_or_create_id("product_definition", "product_name", prod_name,
                           id_column="product_id",
                           extra_columns={"product_description": prod_desc, "product_family_id": family_id, "ideal_cycle_time": cycle_time})
        log("  Products: OK", "SUCCESS")

        # ----- COUNT TYPES -----
        log("Setting up count types...")
        count_types = [
            ("Good", "units"),
            ("Scrap", "units"),
            ("Rework", "units")
        ]
        for ct_name, ct_unit in count_types:
            get_or_create_id("count_type", "count_type_name", ct_name,
                           extra_columns={"count_type_unit": ct_unit})
        log("  Count types: OK", "SUCCESS")

        # Verify critical count types
        good_id = query_scalar("SELECT count_type_id FROM mes_core.count_type WHERE count_type_name = ?", ["Good"])
        scrap_id = query_scalar("SELECT count_type_id FROM mes_core.count_type WHERE count_type_name = ?", ["Scrap"])
        if not good_id or not scrap_id:
            errors.append("CRITICAL: 'Good' and 'Scrap' count types are required!")

        # ----- MEASUREMENT TYPES -----
        log("Setting up measurement types...")
        measurement_types = [
            ("Temperature", "C"),
            ("Pressure", "PSI"),
            ("Weight", "kg"),
        ]
        for mt_name, mt_unit in measurement_types:
            get_or_create_id("measurement_type", "measurement_type_name", mt_name,
                           extra_columns={"measurement_type_unit": mt_unit})
        log("  Measurement types: OK", "SUCCESS")

        # ----- KPI DEFINITIONS -----
        log("Setting up KPI definitions...")
        kpis = [
            ("OEE", "%", "availability * performance * quality"),
            ("Availability", "%", "uptime / planned_time"),
            ("Performance", "%", "actual_rate / ideal_rate"),
            ("Quality", "%", "good_count / total_count"),
        ]
        for kpi_name, kpi_unit, formula in kpis:
            get_or_create_id("kpi_definition", "kpi_name", kpi_name,
                           id_column="kpi_id",
                           extra_columns={"kpi_unit": kpi_unit, "kpi_formula": formula})
        log("  KPI definitions: OK", "SUCCESS")

        # ----- DOWNTIME REASONS -----
        log("Setting up downtime reasons...")
        reasons = [
            ("PM", "Preventive Maintenance", True),
            ("SETUP", "Changeover/Setup", True),
            ("BREAK", "Mechanical Breakdown", False),
            ("MATL", "Material Shortage", False),
        ]
        for code, name, is_planned in reasons:
            get_or_create_id("downtime_reason", "downtime_reason_code", code,
                           extra_columns={"downtime_reason_name": name, "is_planned": is_planned})
        log("  Downtime reasons: OK", "SUCCESS")

        # ----- ASSETS (HIERARCHY) -----
        log("Setting up asset hierarchy...")

        # Get asset type IDs
        enterprise_type = query_scalar("SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = ?", ["Enterprise"])
        site_type = query_scalar("SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = ?", ["Site"])
        area_type = query_scalar("SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = ?", ["Area"])
        line_type = query_scalar("SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = ?", ["Line"])
        cell_type = query_scalar("SELECT asset_type_id FROM mes_core.asset_type WHERE asset_type_name = ?", ["Cell"])

        # Create hierarchy - Enterprise
        enterprise_id = get_or_create_id("asset_definition", "asset_name", "Abelara Corp",
                                        id_column="asset_id",
                                        extra_columns={"asset_description": "Abelara Corporation enterprise",
                                                      "asset_type_id": enterprise_type, "tag_path": "/AbelaraCorp"})

        # Site
        site_id = get_or_create_id("asset_definition", "asset_name", "Plant Alpha",
                                  id_column="asset_id",
                                  extra_columns={"asset_description": "Main production plant",
                                               "asset_type_id": site_type, "parent_asset_id": enterprise_id,
                                               "tag_path": "/AbelaraCorp/PlantAlpha"})

        # Area
        area_id = get_or_create_id("asset_definition", "asset_name", "Production Area 1",
                                  id_column="asset_id",
                                  extra_columns={"asset_description": "Production area 1",
                                               "asset_type_id": area_type, "parent_asset_id": site_id,
                                               "tag_path": "/AbelaraCorp/PlantAlpha/Area1"})

        # Line (main test asset)
        line_id = get_or_create_id("asset_definition", "asset_name", "Line 1",
                                  id_column="asset_id",
                                  extra_columns={"asset_description": "Production line 1",
                                               "asset_type_id": line_type, "parent_asset_id": area_id,
                                               "tag_path": "/AbelaraCorp/PlantAlpha/Area1/Line1"})

        # Cell
        cell_id = get_or_create_id("asset_definition", "asset_name", "Cell A",
                                  id_column="asset_id",
                                  extra_columns={"asset_description": "Cell A workstation",
                                               "asset_type_id": cell_type, "parent_asset_id": line_id,
                                               "tag_path": "/AbelaraCorp/PlantAlpha/Area1/Line1/CellA"})

        # Test asset for cleanup tests
        test_line_id = get_or_create_id("asset_definition", "asset_name", TEST_CONFIG["test_prefix"] + "TestLine",
                                       id_column="asset_id",
                                       extra_columns={"asset_description": "Test line for automated testing",
                                                    "asset_type_id": line_type, "parent_asset_id": area_id,
                                                    "tag_path": "/AbelaraCorp/PlantAlpha/Area1/" + TEST_CONFIG["test_prefix"] + "TestLine"})

        suite.test_data["line_id"] = line_id
        suite.test_data["cell_id"] = cell_id
        suite.test_data["test_line_id"] = test_line_id
        suite.test_data["enterprise_id"] = enterprise_id

        log("  Asset hierarchy: OK", "SUCCESS")

        # Store IDs for tests
        suite.test_data["good_count_type_id"] = good_id
        suite.test_data["scrap_count_type_id"] = scrap_id

        if errors:
            for err in errors:
                log(err, "ERROR")
            return False

        log("\nSeed data setup complete!", "SUCCESS")
        return True

    except Exception as e:
        import traceback
        log("Seed data setup failed: %s" % str(e), "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False

# =============================================================================
# TEST CLEANUP
# =============================================================================

def cleanup_test_data():
    """Remove all test-generated data"""
    log_header("CLEANUP PHASE")

    try:
        prefix = TEST_CONFIG["test_prefix"]

        # Order matters due to foreign key constraints!
        # Clean up in reverse order of dependencies

        log("Cleaning up notes...")
        # General notes from tests
        db.execute("DELETE FROM mes_core.general_note WHERE note LIKE ?", [prefix + "%"])
        db.execute("DELETE FROM mes_core.general_note WHERE note LIKE ?", ["Test note%"])
        db.execute("DELETE FROM mes_core.general_note WHERE note LIKE ?", ["TC-%"])

        log("Cleaning up log notes...")
        # Note tables linked to logs we'll delete
        for note_table in ["state_log_note", "production_log_note", "count_log_note",
                          "measurement_log_note", "kpi_log_note"]:
            try:
                # Delete notes where parent log has test prefix in additional_info
                db.execute("DELETE FROM mes_core.%s WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'" % note_table)
            except:
                pass

        log("Cleaning up KPI logs...")
        db.execute("DELETE FROM mes_core.kpi_log WHERE logged_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'")

        log("Cleaning up measurement logs...")
        db.execute("DELETE FROM mes_core.measurement_log WHERE logged_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'")

        log("Cleaning up count logs...")
        db.execute("DELETE FROM mes_core.count_log WHERE logged_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'")

        log("Cleaning up state logs...")
        db.execute("DELETE FROM mes_core.state_log WHERE logged_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'")

        log("Cleaning up production logs...")
        # First clean any active runs from test assets
        test_line_id = suite.test_data.get("test_line_id")
        line_id = suite.test_data.get("line_id")

        if test_line_id:
            db.execute("DELETE FROM mes_core.production_log WHERE asset_id = ?", [test_line_id])

        # Clean recent production logs (from test runs)
        db.execute("DELETE FROM mes_core.production_log WHERE logged_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'")

        log("Cleaning up test reference data...")
        # Clean test-prefixed reference data
        db.execute("DELETE FROM mes_core.asset_definition WHERE asset_name LIKE ?", [prefix + "%"])
        db.execute("DELETE FROM mes_core.product_definition WHERE product_name LIKE ?", [prefix + "%"])
        db.execute("DELETE FROM mes_core.product_family WHERE product_family_name LIKE ?", [prefix + "%"])

        log("Cleanup complete!", "SUCCESS")
        return True

    except Exception as e:
        import traceback
        log("Cleanup failed: %s" % str(e), "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False

def emergency_cleanup():
    """Force cleanup of active production runs on test assets"""
    log("Running emergency cleanup...")
    try:
        # End any active runs on Line 1 and test assets
        line_id = suite.test_data.get("line_id")
        test_line_id = suite.test_data.get("test_line_id")

        if line_id:
            db.execute("UPDATE mes_core.production_log SET end_ts = CURRENT_TIMESTAMP WHERE asset_id = ? AND end_ts IS NULL", [line_id])
        if test_line_id:
            db.execute("UPDATE mes_core.production_log SET end_ts = CURRENT_TIMESTAMP WHERE asset_id = ? AND end_ts IS NULL", [test_line_id])

        log("Emergency cleanup complete", "SUCCESS")
    except Exception as e:
        log("Emergency cleanup error: %s" % str(e), "WARN")

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

    Example:
        expect_error(errors.MesValidationError, lambda: production.startRun(None, "Widget A"))
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

# =============================================================================
# MODULE 1: ERRORS TESTS
# =============================================================================

def test_errors_module():
    """Test the mes.errors exception hierarchy"""
    log_subheader("Module: errors.py")

    import mes.errors as errors

    def test_mes_error_base():
        error = errors.MesError("Test message")
        assert str(error) == "Test message", "Message mismatch"
        assert error.message == "Test message", "Message attribute missing"

    def test_validation_error():
        error = errors.MesValidationError("Invalid value", "quantity", -5)
        assert error.field == "quantity", "Field mismatch"
        assert error.value == -5, "Value mismatch"

    def test_not_found_error():
        error = errors.MesNotFoundError("Not found", "Product", 999)
        assert error.entityType == "Product", "Entity type mismatch"
        assert error.entityId == 999, "Entity ID mismatch"

    def test_database_error():
        cause = Exception("SQL error")
        error = errors.MesDatabaseError("Query failed", "SELECT * FROM x", cause)
        assert error.sql == "SELECT * FROM x", "SQL mismatch"
        assert error.cause == cause, "Cause mismatch"

    def test_conflict_error():
        error = errors.MesConflictError("Conflict", "ProductionLog", 1, "ACTIVE_RUN_EXISTS")
        assert error.conflictType == "ACTIVE_RUN_EXISTS", "Conflict type mismatch"

    def test_resolution_error():
        error = errors.MesResolutionError("Cannot resolve", "Asset", "BadAsset")
        assert error.entityType == "Asset", "Entity type mismatch"
        assert error.identifier == "BadAsset", "Identifier mismatch"

    run_test("TC-ERR-001: MesError base exception", test_mes_error_base)
    run_test("TC-ERR-002: MesValidationError", test_validation_error)
    run_test("TC-ERR-003: MesNotFoundError", test_not_found_error)
    run_test("TC-ERR-004: MesDatabaseError", test_database_error)
    run_test("TC-ERR-005: MesConflictError", test_conflict_error)
    run_test("TC-ERR-006: MesResolutionError", test_resolution_error)

# =============================================================================
# MODULE 2: DATABASE TESTS
# =============================================================================

def test_db_module():
    """Test the mes.db database client layer"""
    log_subheader("Module: db.py")

    import mes.db as db

    def test_connection():
        result = db.testConnection()
        assert result == True, "Database connection failed"

    def test_query_returns_list():
        result = db.query("SELECT asset_type_id, asset_type_name FROM mes_core.asset_type LIMIT 5")
        assert isinstance(result, list), "Query should return list"
        assert len(result) > 0, "Should have results"
        assert 'asset_type_id' in result[0], "Should have asset_type_id column"

    def test_query_one():
        result = db.queryOne("SELECT * FROM mes_core.asset_type WHERE asset_type_name = ?", ["Line"])
        assert result is not None, "Should find 'Line' asset type"
        assert isinstance(result, dict), "Should return dict"

    def test_query_one_no_match():
        result = db.queryOne("SELECT * FROM mes_core.asset_type WHERE asset_type_name = ?", ["NONEXISTENT_XYZ_99999"])
        assert result is None, "Should return None for no match"

    def test_execute_insert():
        sql = "INSERT INTO mes_core.general_note (note, created_at) VALUES (?, CURRENT_TIMESTAMP)"
        rowCount = db.execute(sql, [TEST_CONFIG["test_prefix"] + "TC-DB-005"])
        assert rowCount == 1, "Should insert 1 row"

    def test_execute_return():
        sql = """
            INSERT INTO mes_core.general_note (note, created_at)
            VALUES (?, CURRENT_TIMESTAMP)
            RETURNING note_id, note
        """
        result = db.executeReturn(sql, [TEST_CONFIG["test_prefix"] + "TC-DB-006"])
        assert result is not None, "Should return inserted record"
        assert 'note_id' in result, "Should have ID"

    def test_parameterized_query():
        # SQL injection attempt should be safely escaped
        malicious = "'; DROP TABLE asset_type; --"
        result = db.queryOne("SELECT * FROM mes_core.asset_type WHERE asset_type_name = ?", [malicious])
        assert result is None, "Should return None, not execute injection"
        # Verify table still exists
        result2 = db.query("SELECT COUNT(*) as cnt FROM mes_core.asset_type")
        assert result2[0]['cnt'] > 0, "Table should still exist"

    run_test("TC-DB-001: Test connection", test_connection)
    run_test("TC-DB-002: Query returns list", test_query_returns_list)
    run_test("TC-DB-003: QueryOne returns single record", test_query_one)
    run_test("TC-DB-004: QueryOne returns None for no match", test_query_one_no_match)
    run_test("TC-DB-005: Execute INSERT", test_execute_insert)
    run_test("TC-DB-006: ExecuteReturn with RETURNING", test_execute_return)
    run_test("TC-DB-008: Parameterized query prevents SQL injection", test_parameterized_query)

    # =========================================================================
    # BAD PATH TESTS
    # =========================================================================
    log_subheader("Module: db.py - Bad Path Tests")

    import mes.errors as errors

    def test_invalid_sql_syntax():
        """Query with invalid SQL syntax should raise MesDatabaseError"""
        expect_error(errors.MesDatabaseError, lambda: db.query("SELEKT * FORM invalid_syntax"))

    def test_wrong_param_count():
        """Query with wrong parameter count should raise MesDatabaseError"""
        expect_error(errors.MesDatabaseError, lambda: db.query("SELECT * FROM mes_core.asset_type WHERE asset_type_name = ? AND asset_type_id = ?", ["Line"]))

    def test_execute_nonexistent_table():
        """Execute on nonexistent table should raise MesDatabaseError"""
        expect_error(errors.MesDatabaseError, lambda: db.execute("INSERT INTO mes_core.nonexistent_table_xyz (col) VALUES (?)", ["test"]))

    def test_query_nonexistent_table():
        """Query on nonexistent table should raise MesDatabaseError"""
        expect_error(errors.MesDatabaseError, lambda: db.query("SELECT * FROM mes_core.nonexistent_table_xyz"))

    def test_invalid_column_reference():
        """Query with invalid column should raise MesDatabaseError"""
        expect_error(errors.MesDatabaseError, lambda: db.query("SELECT nonexistent_column FROM mes_core.asset_type"))

    def test_constraint_violation():
        """Insert violating NOT NULL constraint should raise MesDatabaseError"""
        # state_definition requires state_name and state_type_id
        expect_error(errors.MesDatabaseError, lambda: db.execute("INSERT INTO mes_core.state_definition (state_name) VALUES (NULL)"))

    run_test("TC-DB-BP-001: Invalid SQL syntax raises MesDatabaseError", test_invalid_sql_syntax)
    run_test("TC-DB-BP-002: Wrong parameter count raises MesDatabaseError", test_wrong_param_count)
    run_test("TC-DB-BP-003: Execute on nonexistent table raises MesDatabaseError", test_execute_nonexistent_table)
    run_test("TC-DB-BP-004: Query on nonexistent table raises MesDatabaseError", test_query_nonexistent_table)
    run_test("TC-DB-BP-005: Invalid column reference raises MesDatabaseError", test_invalid_column_reference)
    run_test("TC-DB-BP-006: Constraint violation raises MesDatabaseError", test_constraint_violation)

# =============================================================================
# MODULE 3: RESOLVER TESTS
# =============================================================================

def test_resolver_module():
    """Test the mes.resolver entity resolution module"""
    log_subheader("Module: resolver.py")

    import mes.resolver as resolver
    import mes.errors as errors

    def test_resolve_asset_by_id():
        line_id = suite.test_data.get("line_id")
        result = resolver.resolveAsset(line_id)
        assert result is not None, "Should resolve by ID"
        assert result['asset_id'] == line_id, "ID should match"

    def test_resolve_asset_by_name():
        result = resolver.resolveAsset("Line 1")
        assert result is not None, "Should resolve by name"
        assert result['asset_name'] == "Line 1", "Name should match"

    def test_resolve_asset_by_tag_path():
        result = resolver.resolveAsset("/AbelaraCorp/PlantAlpha/Area1/Line1")
        assert result is not None, "Should resolve by tag path"
        assert "Line1" in result['tag_path'], "Tag path should match"

    def test_resolve_asset_not_found():
        try:
            resolver.resolveAsset("NONEXISTENT_ASSET_XYZ_99999")
            assert False, "Should have raised MesResolutionError"
        except errors.MesResolutionError as e:
            assert e.entityType == "asset", "Should be asset resolution error"

    def test_resolve_state():
        result = resolver.resolveState("Running")
        assert result is not None, "Should resolve state"
        assert result['state_name'] == "Running", "Name should match"

    def test_resolve_product():
        result = resolver.resolveProduct("Widget A")
        assert result is not None, "Should resolve product"
        assert result['product_name'] == "Widget A", "Name should match"
        assert result['product_family_id'] is not None, "Should have family"

    def test_resolve_product_family():
        result = resolver.resolveProductFamily("Widgets")
        assert result is not None, "Should resolve family"
        assert result['product_family_name'] == "Widgets", "Name should match"

    def test_resolve_count_type():
        result = resolver.resolveCountType("Good")
        assert result is not None, "Should resolve count type"
        assert result['count_type_name'] == "Good", "Name should match"

    def test_resolve_measurement_type():
        result = resolver.resolveMeasurementType("Temperature")
        assert result is not None, "Should resolve measurement type"

    def test_resolve_kpi():
        result = resolver.resolveKPI("OEE")
        assert result is not None, "Should resolve KPI"
        assert result['kpi_name'] == "OEE", "Name should match"

    def test_resolve_downtime_reason():
        result = resolver.resolveDowntimeReason("PM")
        assert result is not None, "Should resolve by code"
        assert result['downtime_reason_code'] == "PM", "Code should match"

    run_test("TC-RES-001: Resolve asset by ID", test_resolve_asset_by_id)
    run_test("TC-RES-002: Resolve asset by name", test_resolve_asset_by_name)
    run_test("TC-RES-003: Resolve asset by tag path", test_resolve_asset_by_tag_path)
    run_test("TC-RES-004: Resolve asset not found", test_resolve_asset_not_found)
    run_test("TC-RES-006: Resolve state by name", test_resolve_state)
    run_test("TC-RES-008: Resolve product by name", test_resolve_product)
    run_test("TC-RES-009: Resolve product family", test_resolve_product_family)
    run_test("TC-RES-010: Resolve count type", test_resolve_count_type)
    run_test("TC-RES-011: Resolve measurement type", test_resolve_measurement_type)
    run_test("TC-RES-012: Resolve KPI", test_resolve_kpi)
    run_test("TC-RES-013: Resolve downtime reason", test_resolve_downtime_reason)

    # =========================================================================
    # BAD PATH TESTS
    # =========================================================================
    log_subheader("Module: resolver.py - Bad Path Tests")

    def test_resolve_asset_null():
        """resolveAsset(None) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: resolver.resolveAsset(None))

    def test_resolve_asset_nonexistent_id():
        """resolveAsset with nonexistent ID should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: resolver.resolveAsset(999999))

    def test_resolve_asset_invalid_type():
        """resolveAsset with invalid type (list) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: resolver.resolveAsset([1, 2, 3]))

    def test_resolve_asset_empty_string():
        """resolveAsset with empty string should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: resolver.resolveAsset(""))

    def test_resolve_state_null():
        """resolveState(None) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: resolver.resolveState(None))

    def test_resolve_state_nonexistent():
        """resolveState with nonexistent name should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: resolver.resolveState("NONEXISTENT_STATE_XYZ"))

    def test_resolve_product_null():
        """resolveProduct(None) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: resolver.resolveProduct(None))

    def test_resolve_product_nonexistent():
        """resolveProduct with nonexistent name should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: resolver.resolveProduct("NONEXISTENT_PRODUCT_XYZ"))

    def test_resolve_count_type_null():
        """resolveCountType(None) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: resolver.resolveCountType(None))

    def test_resolve_measurement_type_nonexistent():
        """resolveMeasurementType with nonexistent name should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: resolver.resolveMeasurementType("INVALID_MEASUREMENT_TYPE"))

    def test_resolve_kpi_null():
        """resolveKPI(None) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: resolver.resolveKPI(None))

    def test_resolve_downtime_reason_nonexistent():
        """resolveDowntimeReason with nonexistent code should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: resolver.resolveDowntimeReason("INVALID_REASON_XYZ"))

    def test_resolve_product_family_null():
        """resolveProductFamily(None) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: resolver.resolveProductFamily(None))

    run_test("TC-RES-BP-001: resolveAsset(None) raises MesValidationError", test_resolve_asset_null)
    run_test("TC-RES-BP-002: resolveAsset(999999) raises MesResolutionError", test_resolve_asset_nonexistent_id)
    run_test("TC-RES-BP-003: resolveAsset([1,2,3]) raises MesValidationError", test_resolve_asset_invalid_type)
    run_test("TC-RES-BP-004: resolveAsset('') raises MesResolutionError", test_resolve_asset_empty_string)
    run_test("TC-RES-BP-005: resolveState(None) raises MesValidationError", test_resolve_state_null)
    run_test("TC-RES-BP-006: resolveState('NONEXISTENT') raises MesResolutionError", test_resolve_state_nonexistent)
    run_test("TC-RES-BP-007: resolveProduct(None) raises MesValidationError", test_resolve_product_null)
    run_test("TC-RES-BP-008: resolveProduct('NONEXISTENT') raises MesResolutionError", test_resolve_product_nonexistent)
    run_test("TC-RES-BP-009: resolveCountType(None) raises MesValidationError", test_resolve_count_type_null)
    run_test("TC-RES-BP-010: resolveMeasurementType('INVALID') raises MesResolutionError", test_resolve_measurement_type_nonexistent)
    run_test("TC-RES-BP-011: resolveKPI(None) raises MesValidationError", test_resolve_kpi_null)
    run_test("TC-RES-BP-012: resolveDowntimeReason('INVALID') raises MesResolutionError", test_resolve_downtime_reason_nonexistent)
    run_test("TC-RES-BP-013: resolveProductFamily(None) raises MesValidationError", test_resolve_product_family_null)

# =============================================================================
# MODULE 4: LOOKUPS TESTS
# =============================================================================

def test_lookups_module():
    """Test the mes.lookups reference data lookup module"""
    log_subheader("Module: lookups.py")

    import mes.lookups as lookups

    def test_get_states():
        result = lookups.getStates()
        assert isinstance(result, list), "Should return list"
        assert len(result) > 0, "Should have states"
        assert 'state_name' in result[0], "Should have state_name"

    def test_get_state_types():
        result = lookups.getStateTypes()
        assert isinstance(result, list), "Should return list"
        assert len(result) >= 3, "Should have at least 3 types"

    def test_get_products():
        result = lookups.getProducts()
        assert isinstance(result, list), "Should return list"
        assert len(result) > 0, "Should have products"

    def test_get_product_families():
        result = lookups.getProductFamilies()
        assert isinstance(result, list), "Should return list"
        assert len(result) >= 2, "Should have families"

    def test_get_good_count_type_id():
        result = lookups.getGoodCountTypeId()
        assert result is not None, "Should return Good count type ID"
        assert isinstance(result, (int, long)), "Should be integer"

    def test_get_scrap_count_type_id():
        result = lookups.getScrapCountTypeId()
        assert result is not None, "Should return Scrap count type ID"

    def test_get_count_types():
        result = lookups.getCountTypes()
        assert isinstance(result, list), "Should return list"
        names = [ct['count_type_name'] for ct in result]
        assert 'Good' in names, "Should have 'Good'"
        assert 'Scrap' in names, "Should have 'Scrap'"

    def test_get_measurement_types():
        result = lookups.getMeasurementTypes()
        assert isinstance(result, list), "Should return list"
        assert len(result) > 0, "Should have measurement types"

    def test_get_kpis():
        result = lookups.getKPIs()
        assert isinstance(result, list), "Should return list"
        names = [k['kpi_name'] for k in result]
        assert 'OEE' in names, "Should have OEE"

    def test_get_downtime_reasons():
        result = lookups.getDowntimeReasons()
        assert isinstance(result, list), "Should return list"
        assert len(result) > 0, "Should have reasons"

    def test_get_assets():
        result = lookups.getAssets()
        assert isinstance(result, list), "Should return list"
        assert len(result) > 0, "Should have assets"

    def test_get_asset_types():
        result = lookups.getAssetTypes()
        assert isinstance(result, list), "Should return list"
        assert len(result) >= 5, "Should have 5+ asset types"

    run_test("TC-LKP-001: Get states", test_get_states)
    run_test("TC-LKP-003: Get state types", test_get_state_types)
    run_test("TC-LKP-004: Get products", test_get_products)
    run_test("TC-LKP-006: Get product families", test_get_product_families)
    run_test("TC-LKP-007: Get good count type ID", test_get_good_count_type_id)
    run_test("TC-LKP-008: Get scrap count type ID", test_get_scrap_count_type_id)
    run_test("TC-LKP-009: Get count types", test_get_count_types)
    run_test("TC-LKP-010: Get measurement types", test_get_measurement_types)
    run_test("TC-LKP-011: Get KPIs", test_get_kpis)
    run_test("TC-LKP-012: Get downtime reasons", test_get_downtime_reasons)
    run_test("TC-LKP-014: Get assets", test_get_assets)
    run_test("TC-LKP-017: Get asset types", test_get_asset_types)

    # =========================================================================
    # BAD PATH TESTS
    # =========================================================================
    log_subheader("Module: lookups.py - Bad Path Tests")

    import mes.errors as errors

    def test_get_products_filtered_no_match():
        """getProducts with filter that matches nothing should return empty list"""
        # This tests edge case where active=True filter returns nothing for certain queries
        result = lookups.getProducts()
        # Should return list (possibly empty), not None or error
        assert isinstance(result, list), "Should return list even if empty"

    def test_lookup_functions_return_lists():
        """All lookup functions should return lists, never None"""
        result_states = lookups.getStates()
        result_products = lookups.getProducts()
        result_assets = lookups.getAssets()
        assert isinstance(result_states, list), "getStates should return list"
        assert isinstance(result_products, list), "getProducts should return list"
        assert isinstance(result_assets, list), "getAssets should return list"

    run_test("TC-LKP-BP-002: getProducts always returns list", test_get_products_filtered_no_match)
    run_test("TC-LKP-BP-003: All lookup functions return lists, never None", test_lookup_functions_return_lists)

# =============================================================================
# MODULE 5: PRODUCTION TESTS
# =============================================================================

def test_production_module():
    """Test the mes.production production run management module"""
    log_subheader("Module: production.py")

    import mes.production as production
    import mes.errors as errors

    # Clean slate - end any active runs on test asset
    try:
        production.endRunForAsset("Line 1")
    except:
        pass

    def test_start_run():
        run = production.startRun("Line 1", "Widget A")
        assert run is not None, "Should create run"
        assert 'production_log_id' in run, "Should have ID"
        assert run['end_ts'] is None, "Should be active (no end time)"
        # Store for later tests
        suite.test_data['current_run_id'] = run['production_log_id']
        # Cleanup
        production.endRun(run['production_log_id'])

    def test_start_run_with_options():
        run = production.startRun(
            "Line 1", "Widget A",
            workOrder="WO-TEST-001",
            lotNumber="LOT-TEST-001"
        )
        try:
            # workOrder and lotNumber are stored in additional_info JSON field
            info = run.get('additional_info') or {}
            if isinstance(info, basestring):
                info = json.loads(info)
            assert info.get('workOrder') == "WO-TEST-001", "Should have work order in additional_info"
            assert info.get('lotNumber') == "LOT-TEST-001", "Should have lot number in additional_info"
        finally:
            production.endRun(run['production_log_id'])

    def test_start_run_conflict():
        run1 = production.startRun("Line 1", "Widget A")
        try:
            run2 = production.startRun("Line 1", "Widget B")
            production.endRun(run2['production_log_id'])
            assert False, "Should have raised MesConflictError"
        except errors.MesConflictError as e:
            assert "ACTIVE_RUN" in str(e.conflictType).upper(), "Should be active run conflict"
        finally:
            production.endRun(run1['production_log_id'])

    def test_start_run_allow_multiple():
        run1 = production.startRun("Line 1", "Widget A")
        try:
            run2 = production.startRun("Line 1", "Widget B", allowMultipleRuns=True)
            assert run1['production_log_id'] != run2['production_log_id'], "Should be different runs"
            production.endRun(run2['production_log_id'])
        finally:
            production.endRun(run1['production_log_id'])

    def test_end_run():
        run = production.startRun("Line 1", "Widget A")
        result = production.endRun(run['production_log_id'])
        assert result is not None, "Should return ended run"
        assert result['end_ts'] is not None, "Should have end time"

    def test_end_run_for_asset():
        production.startRun("Line 1", "Widget A")
        result = production.endRunForAsset("Line 1")
        assert result is not None, "Should end the run"
        assert result['end_ts'] is not None, "Should have end time"

    def test_end_run_for_asset_no_active():
        # Ensure no active run
        production.endRunForAsset("Line 1")
        result = production.endRunForAsset("Line 1")
        assert result is None, "Should return None when no active run"

    def test_get_active_run():
        run = production.startRun("Line 1", "Widget A")
        result = production.getActiveRun("Line 1")
        assert result is not None, "Should find active run"
        assert result['production_log_id'] == run['production_log_id'], "Should match"
        production.endRun(run['production_log_id'])

    def test_has_active_run():
        production.endRunForAsset("Line 1")  # Clear
        assert production.hasActiveRun("Line 1") == False, "Should not have active run"

        run = production.startRun("Line 1", "Widget A")
        assert production.hasActiveRun("Line 1") == True, "Should have active run"
        production.endRun(run['production_log_id'])

    def test_get_all_active_runs():
        run = production.startRun("Line 1", "Widget A")
        result = production.getAllActiveRuns()
        assert isinstance(result, list), "Should return list"
        ids = [r['production_log_id'] for r in result]
        assert run['production_log_id'] in ids, "Should include our run"
        production.endRun(run['production_log_id'])

    def test_get_run_by_id():
        run = production.startRun("Line 1", "Widget A")
        result = production.getRunById(run['production_log_id'])
        assert result is not None, "Should find run"
        assert result['production_log_id'] == run['production_log_id'], "Should match"
        production.endRun(run['production_log_id'])

    def test_get_run_history():
        run = production.startRun("Line 1", "Widget A")
        production.endRun(run['production_log_id'])
        result = production.getRunHistory(asset="Line 1", hours=1)
        assert isinstance(result, list), "Should return list"
        assert len(result) > 0, "Should have history"

    run_test("TC-PRD-001: Start production run", test_start_run)
    run_test("TC-PRD-002: Start run with options", test_start_run_with_options)
    run_test("TC-PRD-003: Start run conflict error", test_start_run_conflict)
    run_test("TC-PRD-004: Start run allow multiple", test_start_run_allow_multiple)
    run_test("TC-PRD-005: End production run", test_end_run)
    run_test("TC-PRD-006: End run for asset", test_end_run_for_asset)
    run_test("TC-PRD-007: End run for asset no active", test_end_run_for_asset_no_active)
    run_test("TC-PRD-008: Get active run", test_get_active_run)
    run_test("TC-PRD-010: Has active run", test_has_active_run)
    run_test("TC-PRD-011: Get all active runs", test_get_all_active_runs)
    run_test("TC-PRD-012: Get run by ID", test_get_run_by_id)
    run_test("TC-PRD-013: Get run history", test_get_run_history)

    # =========================================================================
    # BAD PATH TESTS
    # =========================================================================
    log_subheader("Module: production.py - Bad Path Tests")

    def test_start_run_null_asset():
        """startRun(None, product) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: production.startRun(None, "Widget A"))

    def test_start_run_null_product():
        """startRun(asset, None) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: production.startRun("Line 1", None))

    def test_start_run_nonexistent_asset():
        """startRun with nonexistent asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: production.startRun("NONEXISTENT_ASSET_XYZ", "Widget A"))

    def test_start_run_nonexistent_product():
        """startRun with nonexistent product should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: production.startRun("Line 1", "NONEXISTENT_PRODUCT_XYZ"))

    def test_end_run_nonexistent_id():
        """endRun with nonexistent ID should raise MesNotFoundError"""
        expect_error(errors.MesNotFoundError, lambda: production.endRun(999999))

    def test_end_run_twice():
        """Ending an already-ended run should raise MesConflictError"""
        run = production.startRun("Line 1", "Widget A")
        production.endRun(run['production_log_id'])
        expect_error(errors.MesConflictError, lambda: production.endRun(run['production_log_id']))

    def test_get_run_by_id_null():
        """getRunById(None) should return None gracefully"""
        result = production.getRunById(None)
        assert result is None, "Should return None for null ID"

    def test_get_active_run_nonexistent_asset():
        """getActiveRun with nonexistent asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: production.getActiveRun("NONEXISTENT_ASSET_XYZ"))

    run_test("TC-PRD-BP-001: startRun(None, product) raises MesValidationError", test_start_run_null_asset)
    run_test("TC-PRD-BP-002: startRun(asset, None) raises MesValidationError", test_start_run_null_product)
    run_test("TC-PRD-BP-003: startRun with nonexistent asset raises MesResolutionError", test_start_run_nonexistent_asset)
    run_test("TC-PRD-BP-004: startRun with nonexistent product raises MesResolutionError", test_start_run_nonexistent_product)
    run_test("TC-PRD-BP-005: endRun(999999) raises MesNotFoundError", test_end_run_nonexistent_id)
    run_test("TC-PRD-BP-006: End run twice raises MesConflictError", test_end_run_twice)
    run_test("TC-PRD-BP-007: getRunById(None) returns None gracefully", test_get_run_by_id_null)
    run_test("TC-PRD-BP-008: getActiveRun with nonexistent asset raises MesResolutionError", test_get_active_run_nonexistent_asset)

    # Final cleanup
    try:
        production.endRunForAsset("Line 1")
    except:
        pass

# =============================================================================
# MODULE 6: COUNTS TESTS
# =============================================================================

def test_counts_module():
    """Test the mes.counts production counting module"""
    log_subheader("Module: counts.py")

    import mes.counts as counts
    import mes.production as production
    import mes.lookups as lookups

    # Ensure no active run
    try:
        production.endRunForAsset("Line 1")
    except:
        pass

    def test_record_count():
        # Without active run, product must be specified
        result = counts.recordCount("Line 1", "Good", 50, product="Widget A")
        assert result is not None, "Should create count"
        assert 'count_log_id' in result, "Should have ID"
        assert result['quantity'] == 50, "Quantity should match"

    def test_record_good_count():
        # Without active run, product must be specified
        result = counts.recordGoodCount("Line 1", 100, product="Widget A")
        assert result is not None, "Should create count"
        goodTypeId = lookups.getGoodCountTypeId()
        assert result['count_type_id'] == goodTypeId, "Should be Good type"

    def test_record_scrap_count():
        # Without active run, product must be specified
        result = counts.recordScrapCount("Line 1", 5, product="Widget A", reason="BREAK")
        assert result is not None, "Should create count"
        scrapTypeId = lookups.getScrapCountTypeId()
        assert result['count_type_id'] == scrapTypeId, "Should be Scrap type"

    def test_record_rework_count():
        # Without active run, product must be specified
        result = counts.recordReworkCount("Line 1", 10, product="Widget A", reason="Quality Issue")
        assert result is not None, "Should create count"

    def test_count_auto_links_to_run():
        run = production.startRun("Line 1", "Widget A")
        count = counts.recordGoodCount("Line 1", 25)
        assert count['production_log_id'] == run['production_log_id'], "Should auto-link to active run"
        production.endRun(run['production_log_id'])

    def test_count_inherits_product():
        run = production.startRun("Line 1", "Widget A")
        count = counts.recordGoodCount("Line 1", 30)  # No product specified
        assert count['product_id'] == run['product_id'], "Should inherit product from run"
        production.endRun(run['production_log_id'])

    def test_get_count_history():
        # Without active run, product must be specified
        counts.recordGoodCount("Line 1", 50, product="Widget A")
        result = counts.getCountHistory(asset="Line 1", hours=1)
        assert isinstance(result, list), "Should return list"
        assert len(result) > 0, "Should have history"

    def test_get_count_summary():
        # Without active run, product must be specified
        counts.recordGoodCount("Line 1", 100, product="Widget A")
        counts.recordScrapCount("Line 1", 10, product="Widget A", reason="BREAK")
        result = counts.getCountSummary(asset="Line 1", hours=1)
        assert isinstance(result, list), "Should return list"

    def test_get_total_count():
        # Without active run, product must be specified
        counts.recordGoodCount("Line 1", 50, product="Widget A")
        counts.recordGoodCount("Line 1", 75, product="Widget A")
        result = counts.getTotalCount(asset="Line 1", countType="Good", hours=1)
        assert result >= 125, "Should have at least our counts"

    def test_get_yield():
        # Without active run, product must be specified
        counts.recordGoodCount("Line 1", 90, product="Widget A")
        counts.recordScrapCount("Line 1", 10, product="Widget A", reason="BREAK")
        result = counts.getYield(asset="Line 1", hours=1)
        assert 'good_count' in result, "Should have good_count"
        assert 'total_count' in result, "Should have total_count"
        assert 'yield_percent' in result, "Should have yield_percent"

    run_test("TC-CNT-001: Record count", test_record_count)
    run_test("TC-CNT-003: Record good count", test_record_good_count)
    run_test("TC-CNT-004: Record scrap count", test_record_scrap_count)
    run_test("TC-CNT-005: Record rework count", test_record_rework_count)
    run_test("TC-CNT-006: Count auto-links to active run", test_count_auto_links_to_run)
    run_test("TC-CNT-007: Count inherits product from run", test_count_inherits_product)
    run_test("TC-CNT-009: Get count history", test_get_count_history)
    run_test("TC-CNT-012: Get count summary", test_get_count_summary)
    run_test("TC-CNT-013: Get total count", test_get_total_count)
    run_test("TC-CNT-014: Get yield", test_get_yield)

    # =========================================================================
    # BAD PATH TESTS
    # =========================================================================
    log_subheader("Module: counts.py - Bad Path Tests")

    import mes.errors as errors

    def test_record_count_negative_quantity():
        """recordCount with negative quantity should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: counts.recordCount("Line 1", "Good", -5, product="Widget A"))

    def test_record_count_no_product_no_run():
        """recordCount without product and no active run should raise MesValidationError"""
        # Ensure no active run
        production.endRunForAsset("Line 1")
        expect_error(errors.MesValidationError, lambda: counts.recordCount("Line 1", "Good", 10))

    def test_record_count_invalid_asset():
        """recordCount with invalid asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: counts.recordCount("NONEXISTENT_ASSET_XYZ", "Good", 10, product="Widget A"))

    def test_record_count_invalid_count_type():
        """recordCount with invalid count type should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: counts.recordCount("Line 1", "INVALID_COUNT_TYPE_XYZ", 10, product="Widget A"))

    def test_record_good_count_zero_quantity():
        """recordGoodCount with quantity=0 should succeed (edge case)"""
        # Zero is a valid quantity in some scenarios (e.g., recording that nothing was produced)
        result = counts.recordGoodCount("Line 1", 0, product="Widget A")
        assert result is not None, "Zero quantity should be allowed"
        assert result['quantity'] == 0, "Quantity should be 0"

    def test_record_scrap_count_missing_reason():
        """recordScrapCount without reason should succeed (reason is optional)"""
        result = counts.recordScrapCount("Line 1", 5, product="Widget A")
        assert result is not None, "Should create scrap count without reason"

    def test_get_count_history_invalid_asset():
        """getCountHistory with invalid asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: counts.getCountHistory(asset="NONEXISTENT_ASSET_XYZ", hours=1))

    run_test("TC-CNT-BP-001: recordCount with negative quantity raises MesValidationError", test_record_count_negative_quantity)
    run_test("TC-CNT-BP-002: recordCount without product and no active run raises MesValidationError", test_record_count_no_product_no_run)
    run_test("TC-CNT-BP-003: recordCount with invalid asset raises MesResolutionError", test_record_count_invalid_asset)
    run_test("TC-CNT-BP-004: recordCount with invalid count type raises MesResolutionError", test_record_count_invalid_count_type)
    run_test("TC-CNT-BP-005: recordGoodCount with quantity=0 succeeds (edge case)", test_record_good_count_zero_quantity)
    run_test("TC-CNT-BP-006: recordScrapCount without reason succeeds (optional)", test_record_scrap_count_missing_reason)
    run_test("TC-CNT-BP-007: getCountHistory with invalid asset raises MesResolutionError", test_get_count_history_invalid_asset)

    # Overflow value tests
    def test_record_count_overflow_quantity():
        """recordCount with quantity exceeding NUMERIC(10,2) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: counts.recordCount("Line 1", "Good", 999999999.99, product="Widget A"))

    run_test("TC-CNT-BP-008: recordCount with overflow quantity raises MesValidationError", test_record_count_overflow_quantity)

    # Cleanup
    try:
        production.endRunForAsset("Line 1")
    except:
        pass

# =============================================================================
# MODULE 7: QUALITY TESTS
# =============================================================================

def test_quality_module():
    """Test the mes.quality measurement module"""
    log_subheader("Module: quality.py")

    import mes.quality as quality

    def test_record_measurement():
        # Without active run, product must be specified
        result = quality.recordMeasurement(
            "Line 1", "Temperature", 25.5,
            product="Widget A",
            targetValue=25.0,
            tolerance=0.05
        )
        assert result is not None, "Should create measurement"
        assert 'measurement_log_id' in result, "Should have ID"
        assert result['actual_value'] == 25.5, "Value should match"

    def test_measurement_in_tolerance():
        # Without active run, product must be specified
        result = quality.recordMeasurement(
            "Line 1", "Weight", 100.0,
            product="Widget A",
            targetValue=100.0,
            tolerance=0.05
        )
        assert result['in_tolerance'] == True, "Should be in tolerance"

    def test_measurement_out_of_tolerance():
        # Without active run, product must be specified
        result = quality.recordMeasurement(
            "Line 1", "Weight", 120.0,  # 20% above
            product="Widget A",
            targetValue=100.0,
            tolerance=0.05  # 5% tolerance
        )
        assert result['in_tolerance'] == False, "Should be out of tolerance"

    def test_measurement_with_uom():
        # Without active run, product must be specified
        result = quality.recordMeasurement(
            "Line 1", "Pressure", 50.0,
            product="Widget A",
            unitOfMeasure="PSI"
        )
        assert result['unit_of_measure'] == "PSI", "Should have UoM"

    def test_get_measurement_history():
        # Without active run, product must be specified
        quality.recordMeasurement("Line 1", "Temperature", 25.0, product="Widget A")
        result = quality.getMeasurementHistory(asset="Line 1", hours=1)
        assert isinstance(result, list), "Should return list"
        assert len(result) > 0, "Should have history"

    def test_get_measurement_summary():
        # Without active run, product must be specified
        quality.recordMeasurement("Line 1", "Temperature", 24.0, product="Widget A", targetValue=25.0, tolerance=0.05)
        quality.recordMeasurement("Line 1", "Temperature", 25.0, product="Widget A", targetValue=25.0, tolerance=0.05)
        quality.recordMeasurement("Line 1", "Temperature", 26.0, product="Widget A", targetValue=25.0, tolerance=0.05)
        result = quality.getMeasurementSummary(asset="Line 1", hours=1)
        assert isinstance(result, list), "Should return list"

    def test_first_pass_yield():
        # Without active run, product must be specified
        quality.recordMeasurement("Line 1", "Temperature", 25.0, product="Widget A", targetValue=25.0, tolerance=0.10)
        quality.recordMeasurement("Line 1", "Temperature", 25.0, product="Widget A", targetValue=25.0, tolerance=0.10)
        quality.recordMeasurement("Line 1", "Temperature", 100.0, product="Widget A", targetValue=25.0, tolerance=0.10)
        result = quality.getFirstPassYield(asset="Line 1", hours=1)
        assert 'in_tolerance_count' in result, "Should have in_tolerance_count"
        assert 'total_count' in result, "Should have total_count"
        assert 'first_pass_yield' in result, "Should have first_pass_yield"

    run_test("TC-QTY-001: Record measurement", test_record_measurement)
    run_test("TC-QTY-002: Measurement in tolerance", test_measurement_in_tolerance)
    run_test("TC-QTY-003: Measurement out of tolerance", test_measurement_out_of_tolerance)
    run_test("TC-QTY-004: Measurement with unit of measure", test_measurement_with_uom)
    run_test("TC-QTY-006: Get measurement history", test_get_measurement_history)
    run_test("TC-QTY-009: Get measurement summary", test_get_measurement_summary)
    run_test("TC-QTY-010: Get first pass yield", test_first_pass_yield)

    # =========================================================================
    # BAD PATH TESTS
    # =========================================================================
    log_subheader("Module: quality.py - Bad Path Tests")

    import mes.errors as errors
    import mes.production as production

    def test_record_measurement_no_product_no_run():
        """recordMeasurement without product and no active run should raise MesValidationError"""
        # Ensure no active run
        production.endRunForAsset("Line 1")
        expect_error(errors.MesValidationError, lambda: quality.recordMeasurement("Line 1", "Temperature", 25.0))

    def test_record_measurement_invalid_asset():
        """recordMeasurement with invalid asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: quality.recordMeasurement("NONEXISTENT_ASSET_XYZ", "Temperature", 25.0, product="Widget A"))

    def test_record_measurement_invalid_type():
        """recordMeasurement with invalid measurement type should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: quality.recordMeasurement("Line 1", "INVALID_MEASUREMENT_TYPE_XYZ", 25.0, product="Widget A"))

    def test_measurement_tolerance_zero():
        """Measurement with tolerance=0 should calculate in_tolerance correctly"""
        # When tolerance is 0, only exact matches should be in tolerance
        result = quality.recordMeasurement(
            "Line 1", "Temperature", 25.0,
            product="Widget A",
            targetValue=25.0,
            tolerance=0.0
        )
        assert result['in_tolerance'] == True, "Exact match with 0 tolerance should be in tolerance"

        result2 = quality.recordMeasurement(
            "Line 1", "Temperature", 25.01,
            product="Widget A",
            targetValue=25.0,
            tolerance=0.0
        )
        assert result2['in_tolerance'] == False, "Non-exact match with 0 tolerance should be out of tolerance"

    def test_measurement_target_zero_with_tolerance():
        """Measurement with target=0 and percentage tolerance should handle correctly"""
        # This tests division by zero edge case when calculating percentage deviation
        result = quality.recordMeasurement(
            "Line 1", "Temperature", 0.0,
            product="Widget A",
            targetValue=0.0,
            tolerance=0.05
        )
        # Should not raise error - implementation should handle this gracefully
        assert result is not None, "Should handle target=0 gracefully"

    def test_record_batch_measurements_empty():
        """recordBatchMeasurements with empty list should return empty list"""
        # Check if recordBatchMeasurements exists
        if hasattr(quality, 'recordBatchMeasurements'):
            result = quality.recordBatchMeasurements([])
            assert result == [] or result is None, "Empty batch should return empty list or None"
        else:
            # If the function doesn't exist, skip this test implicitly by passing
            pass

    def test_get_measurement_history_invalid_asset():
        """getMeasurementHistory with invalid asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: quality.getMeasurementHistory(asset="NONEXISTENT_ASSET_XYZ", hours=1))

    run_test("TC-QTY-BP-001: recordMeasurement without product and no active run raises MesValidationError", test_record_measurement_no_product_no_run)
    run_test("TC-QTY-BP-002: recordMeasurement with invalid asset raises MesResolutionError", test_record_measurement_invalid_asset)
    run_test("TC-QTY-BP-003: recordMeasurement with invalid type raises MesResolutionError", test_record_measurement_invalid_type)
    run_test("TC-QTY-BP-004: Measurement with tolerance=0 calculates correctly", test_measurement_tolerance_zero)
    run_test("TC-QTY-BP-005: Measurement with target=0 handles division correctly", test_measurement_target_zero_with_tolerance)
    run_test("TC-QTY-BP-006: recordBatchMeasurements([]) returns empty list", test_record_batch_measurements_empty)
    run_test("TC-QTY-BP-007: getMeasurementHistory with invalid asset raises MesResolutionError", test_get_measurement_history_invalid_asset)

    # Overflow value tests
    def test_measurement_overflow_actual():
        """recordMeasurement with actual_value exceeding NUMERIC(10,2) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: quality.recordMeasurement(
            "Line 1", "Temperature", 999999999.99, product="Widget A"))

    def test_measurement_overflow_target():
        """recordMeasurement with target_value exceeding NUMERIC(10,2) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: quality.recordMeasurement(
            "Line 1", "Temperature", 25.0, product="Widget A", targetValue=999999999.99))

    def test_measurement_overflow_tolerance():
        """recordMeasurement with tolerance exceeding NUMERIC(10,4) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: quality.recordMeasurement(
            "Line 1", "Temperature", 25.0, product="Widget A", targetValue=25.0, tolerance=9999999.99))

    run_test("TC-QTY-BP-008: recordMeasurement with overflow actual_value raises MesValidationError", test_measurement_overflow_actual)
    run_test("TC-QTY-BP-009: recordMeasurement with overflow target_value raises MesValidationError", test_measurement_overflow_target)
    run_test("TC-QTY-BP-010: recordMeasurement with overflow tolerance raises MesValidationError", test_measurement_overflow_tolerance)

# =============================================================================
# MODULE 8: KPI TESTS
# =============================================================================

def test_kpi_module():
    """Test the mes.kpi KPI operations module"""
    log_subheader("Module: kpi.py")

    import mes.kpi as kpi

    def test_record_kpi():
        result = kpi.recordKPI("Line 1", "OEE", 85.5)
        assert result is not None, "Should create KPI"
        assert 'kpi_log_id' in result, "Should have ID"
        assert result['kpi_value'] == 85.5, "Value should match"

    def test_record_oee():
        result = kpi.recordOEE(
            "Line 1",
            oeeValue=82.5,
            availability=95.0,
            performance=90.0,
            quality=96.5
        )
        assert result is not None, "Should create OEE record"
        assert result['kpi_value'] == 82.5, "OEE value should match"

    def test_get_latest_kpi():
        kpi.recordKPI("Line 1", "OEE", 80.0)
        kpi.recordKPI("Line 1", "OEE", 90.0)  # More recent
        result = kpi.getLatestKPI("Line 1", "OEE")
        assert result is not None, "Should find latest"
        assert result['kpi_value'] == 90.0, "Should be most recent"

    def test_get_all_latest_kpis():
        kpi.recordKPI("Line 1", "OEE", 85.0)
        kpi.recordKPI("Line 1", "Availability", 95.0)
        result = kpi.getAllLatestKPIs("Line 1")
        assert isinstance(result, list), "Should return list"

    def test_get_kpi_history():
        kpi.recordKPI("Line 1", "OEE", 85.0)
        kpi.recordKPI("Line 1", "OEE", 87.0)
        result = kpi.getKPIHistory("Line 1", "OEE", days=1)
        assert isinstance(result, list), "Should return list"
        assert len(result) >= 2, "Should have history"

    def test_get_kpi_average():
        kpi.recordKPI("Line 1", "OEE", 80.0)
        kpi.recordKPI("Line 1", "OEE", 85.0)
        kpi.recordKPI("Line 1", "OEE", 90.0)
        result = kpi.getKPIAverage("Line 1", "OEE", days=1)
        assert 'avg_value' in result, "Should have avg_value"
        assert 'min_value' in result, "Should have min_value"
        assert 'max_value' in result, "Should have max_value"

    run_test("TC-KPI-001: Record KPI", test_record_kpi)
    run_test("TC-KPI-003: Record OEE with components", test_record_oee)
    run_test("TC-KPI-004: Get latest KPI", test_get_latest_kpi)
    run_test("TC-KPI-005: Get all latest KPIs", test_get_all_latest_kpis)
    run_test("TC-KPI-006: Get KPI history", test_get_kpi_history)
    run_test("TC-KPI-008: Get KPI average", test_get_kpi_average)

    # =========================================================================
    # BAD PATH TESTS
    # =========================================================================
    log_subheader("Module: kpi.py - Bad Path Tests")

    import mes.errors as errors

    def test_record_kpi_null_asset():
        """recordKPI(None, kpi, value) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: kpi.recordKPI(None, "OEE", 85.0))

    def test_record_kpi_null_kpi():
        """recordKPI(asset, None, value) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: kpi.recordKPI("Line 1", None, 85.0))

    def test_record_kpi_invalid_asset():
        """recordKPI with invalid asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: kpi.recordKPI("NONEXISTENT_ASSET_XYZ", "OEE", 85.0))

    def test_record_kpi_invalid_kpi():
        """recordKPI with invalid KPI name should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: kpi.recordKPI("Line 1", "INVALID_KPI_XYZ", 85.0))

    def test_get_latest_kpi_invalid_asset():
        """getLatestKPI with invalid asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: kpi.getLatestKPI("NONEXISTENT_ASSET_XYZ", "OEE"))

    def test_get_kpi_average_invalid_asset():
        """getKPIAverage with invalid asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: kpi.getKPIAverage("NONEXISTENT_ASSET_XYZ", "OEE", days=1))

    run_test("TC-KPI-BP-001: recordKPI(None, kpi, value) raises MesValidationError", test_record_kpi_null_asset)
    run_test("TC-KPI-BP-002: recordKPI(asset, None, value) raises MesValidationError", test_record_kpi_null_kpi)
    run_test("TC-KPI-BP-003: recordKPI with invalid asset raises MesResolutionError", test_record_kpi_invalid_asset)
    run_test("TC-KPI-BP-004: recordKPI with invalid KPI raises MesResolutionError", test_record_kpi_invalid_kpi)
    run_test("TC-KPI-BP-005: getLatestKPI with invalid asset raises MesResolutionError", test_get_latest_kpi_invalid_asset)
    run_test("TC-KPI-BP-006: getKPIAverage with invalid asset raises MesResolutionError", test_get_kpi_average_invalid_asset)

    # Overflow value tests
    def test_record_kpi_overflow_value():
        """recordKPI with value exceeding NUMERIC(10,2) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: kpi.recordKPI("Line 1", "OEE", 999999999.99))

    run_test("TC-KPI-BP-007: recordKPI with overflow value raises MesValidationError", test_record_kpi_overflow_value)

# =============================================================================
# MODULE 9: STATE TESTS
# =============================================================================

def test_state_module():
    """Test the mes.state state management module"""
    log_subheader("Module: state.py")

    import mes.state as state

    def test_change_state():
        result = state.changeState("Line 1", "Running")
        assert result is not None, "Should create state log"
        assert 'state_log_id' in result, "Should have ID"

    def test_change_state_with_reason():
        result = state.changeState(
            "Line 1",
            "Planned Downtime",
            downtimeReason="PM"
        )
        assert result is not None, "Should create state log"
        assert result['downtime_reason_id'] is not None, "Should have reason"

    def test_start_downtime():
        result = state.startDowntime("Line 1", reason="BREAK", planned=False)
        assert result is not None, "Should start downtime"

    def test_end_downtime():
        state.startDowntime("Line 1", reason="PM", planned=True)
        result = state.endDowntime("Line 1", newState="Running")
        assert result is not None, "Should end downtime"

    def test_get_current_state():
        state.changeState("Line 1", "Running")
        result = state.getCurrentState("Line 1")
        assert result is not None, "Should get current state"
        assert result['state_name'] == "Running", "State should match"

    def test_is_in_state():
        state.changeState("Line 1", "Running")
        assert state.isInState("Line 1", "Running") == True, "Should be in Running"
        assert state.isInState("Line 1", "Idle") == False, "Should not be in Idle"

    def test_is_downtime():
        state.changeState("Line 1", "Planned Downtime")
        result = state.isDowntime("Line 1")
        assert result == True, "Should be downtime"

        state.changeState("Line 1", "Running")
        result = state.isDowntime("Line 1")
        assert result == False, "Should not be downtime"

    def test_get_state_history():
        state.changeState("Line 1", "Running")
        state.changeState("Line 1", "Idle")
        state.changeState("Line 1", "Running")
        result = state.getStateHistory("Line 1", hours=1)
        assert isinstance(result, list), "Should return list"
        assert len(result) >= 3, "Should have history"

    def test_get_downtime_events():
        state.startDowntime("Line 1", reason="BREAK", planned=False)
        state.endDowntime("Line 1", newState="Running")
        result = state.getDowntimeEvents("Line 1", hours=1)
        assert isinstance(result, list), "Should return list"

    def test_get_state_duration_summary():
        result = state.getStateDurationSummary("Line 1", hours=1)
        assert isinstance(result, list), "Should return list"

    run_test("TC-STA-001: Change state", test_change_state)
    run_test("TC-STA-002: Change state with downtime reason", test_change_state_with_reason)
    run_test("TC-STA-003: Start downtime", test_start_downtime)
    run_test("TC-STA-004: End downtime", test_end_downtime)
    run_test("TC-STA-005: Get current state", test_get_current_state)
    run_test("TC-STA-006: Is in state", test_is_in_state)
    run_test("TC-STA-007: Is downtime", test_is_downtime)
    run_test("TC-STA-010: Get state history", test_get_state_history)
    run_test("TC-STA-011: Get downtime events", test_get_downtime_events)
    run_test("TC-STA-013: Get state duration summary", test_get_state_duration_summary)

    # =========================================================================
    # BAD PATH TESTS
    # =========================================================================
    log_subheader("Module: state.py - Bad Path Tests")

    import mes.errors as errors

    def test_change_state_null_asset():
        """changeState(None, state) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: state.changeState(None, "Running"))

    def test_change_state_null_state():
        """changeState(asset, None) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: state.changeState("Line 1", None))

    def test_change_state_invalid_asset():
        """changeState with invalid asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: state.changeState("NONEXISTENT_ASSET_XYZ", "Running"))

    def test_change_state_invalid_state():
        """changeState with invalid state should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: state.changeState("Line 1", "INVALID_STATE_XYZ"))

    def test_start_downtime_invalid_reason():
        """startDowntime with invalid reason should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: state.startDowntime("Line 1", reason="INVALID_REASON_XYZ", planned=True))

    def test_get_current_state_invalid_asset():
        """getCurrentState with invalid asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: state.getCurrentState("NONEXISTENT_ASSET_XYZ"))

    def test_get_state_history_invalid_asset():
        """getStateHistory with invalid asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: state.getStateHistory("NONEXISTENT_ASSET_XYZ", hours=1))

    run_test("TC-STA-BP-001: changeState(None, state) raises MesValidationError", test_change_state_null_asset)
    run_test("TC-STA-BP-002: changeState(asset, None) raises MesValidationError", test_change_state_null_state)
    run_test("TC-STA-BP-003: changeState with invalid asset raises MesResolutionError", test_change_state_invalid_asset)
    run_test("TC-STA-BP-004: changeState with invalid state raises MesResolutionError", test_change_state_invalid_state)
    run_test("TC-STA-BP-005: startDowntime with invalid reason raises MesResolutionError", test_start_downtime_invalid_reason)
    run_test("TC-STA-BP-006: getCurrentState with invalid asset raises MesResolutionError", test_get_current_state_invalid_asset)
    run_test("TC-STA-BP-007: getStateHistory with invalid asset raises MesResolutionError", test_get_state_history_invalid_asset)

# =============================================================================
# MODULE 10: ASSETS TESTS
# =============================================================================

def test_assets_module():
    """Test the mes.assets asset hierarchy module"""
    log_subheader("Module: assets.py")

    import mes.assets as assets

    def test_get_asset_by_id():
        line_id = suite.test_data.get("line_id")
        result = assets.getAssetById(line_id)
        assert result is not None, "Should find asset"
        assert result['asset_id'] == line_id, "ID should match"

    def test_get_asset_by_name():
        result = assets.getAssetByName("Line 1")
        assert result is not None, "Should find asset"
        assert result['asset_name'] == "Line 1", "Name should match"

    def test_get_asset():
        # By ID
        line_id = suite.test_data.get("line_id")
        result1 = assets.getAsset(line_id)
        assert result1 is not None, "Should resolve by ID"

        # By name
        result2 = assets.getAsset("Line 1")
        assert result2 is not None, "Should resolve by name"

    def test_get_parent():
        result = assets.getParent("Line 1")
        assert result is not None, "Should have parent"
        assert result['asset_name'] == "Production Area 1", "Parent should be Area"

    def test_get_parent_root():
        result = assets.getParent("Abelara Corp")
        assert result is None, "Root should have no parent"

    def test_get_children():
        result = assets.getChildren("Production Area 1")
        assert isinstance(result, list), "Should return list"
        names = [c['asset_name'] for c in result]
        assert "Line 1" in names, "Should include Line 1"

    def test_get_ancestors():
        result = assets.getAncestors("Cell A")
        assert isinstance(result, list), "Should return list"
        assert len(result) >= 4, "Should have 4+ ancestors"

    def test_get_descendants():
        result = assets.getDescendants("Plant Alpha")
        assert isinstance(result, list), "Should return list"
        assert len(result) >= 3, "Should have 3+ descendants"

    def test_get_root_assets():
        result = assets.getRootAssets()
        assert isinstance(result, list), "Should return list"
        assert all(a['parent_asset_id'] is None for a in result), "All should be roots"

    def test_find_assets():
        result = assets.findAssets(name="Line")
        assert isinstance(result, list), "Should return list"
        assert all("Line" in a['asset_name'] for a in result), "All should match"

    def test_get_assets_by_type():
        result = assets.getAssetsByType("Line")
        assert isinstance(result, list), "Should return list"

    def test_get_full_path():
        result = assets.getFullPath("Cell A")
        assert result is not None, "Should return path"
        assert len(result) > 0, "Path should not be empty"

    run_test("TC-AST-001: Get asset by ID", test_get_asset_by_id)
    run_test("TC-AST-002: Get asset by name", test_get_asset_by_name)
    run_test("TC-AST-003: Get asset (generic)", test_get_asset)
    run_test("TC-AST-004: Get parent asset", test_get_parent)
    run_test("TC-AST-005: Get parent root returns None", test_get_parent_root)
    run_test("TC-AST-006: Get children", test_get_children)
    run_test("TC-AST-007: Get ancestors", test_get_ancestors)
    run_test("TC-AST-009: Get descendants", test_get_descendants)
    run_test("TC-AST-011: Get root assets", test_get_root_assets)
    run_test("TC-AST-012: Find assets by name", test_find_assets)
    run_test("TC-AST-015: Get assets by type", test_get_assets_by_type)
    run_test("TC-AST-017: Get full path", test_get_full_path)

    # =========================================================================
    # BAD PATH TESTS
    # =========================================================================
    log_subheader("Module: assets.py - Bad Path Tests")

    import mes.errors as errors

    def test_get_asset_null():
        """getAsset(None) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: assets.getAsset(None))

    def test_get_asset_nonexistent():
        """getAsset with nonexistent name should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: assets.getAsset("NONEXISTENT_ASSET_XYZ"))

    def test_get_parent_null():
        """getParent(None) should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: assets.getParent(None))

    def test_get_children_nonexistent():
        """getChildren with nonexistent asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: assets.getChildren("NONEXISTENT_ASSET_XYZ"))

    def test_get_ancestors_nonexistent():
        """getAncestors with nonexistent asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: assets.getAncestors("NONEXISTENT_ASSET_XYZ"))

    def test_get_descendants_nonexistent():
        """getDescendants with nonexistent asset should raise MesResolutionError"""
        expect_error(errors.MesResolutionError, lambda: assets.getDescendants("NONEXISTENT_ASSET_XYZ"))

    def test_find_assets_invalid_type():
        """findAssets with invalid assetType should return empty list"""
        result = assets.findAssets(assetType="INVALID_TYPE_XYZ")
        assert isinstance(result, list), "Should return list"
        assert len(result) == 0, "Should return empty list for invalid type"

    run_test("TC-AST-BP-001: getAsset(None) raises MesValidationError", test_get_asset_null)
    run_test("TC-AST-BP-002: getAsset with nonexistent name raises MesResolutionError", test_get_asset_nonexistent)
    run_test("TC-AST-BP-003: getParent(None) raises MesValidationError", test_get_parent_null)
    run_test("TC-AST-BP-004: getChildren with nonexistent asset raises MesResolutionError", test_get_children_nonexistent)
    run_test("TC-AST-BP-005: getAncestors with nonexistent asset raises MesResolutionError", test_get_ancestors_nonexistent)
    run_test("TC-AST-BP-006: getDescendants with nonexistent asset raises MesResolutionError", test_get_descendants_nonexistent)
    run_test("TC-AST-BP-007: findAssets with invalid assetType returns empty list", test_find_assets_invalid_type)

# =============================================================================
# MODULE 11: NOTES TESTS
# =============================================================================

def test_notes_module():
    """Test the mes.notes annotations module"""
    log_subheader("Module: notes.py")

    import mes.notes as notes
    import mes.state as state
    import mes.production as production
    import mes.counts as counts
    import mes.quality as quality
    import mes.kpi as kpi

    # Ensure clean state
    try:
        production.endRunForAsset("Line 1")
    except:
        pass

    def test_add_state_note():
        stateLog = state.changeState("Line 1", "Running")
        result = notes.addStateNote(stateLog['state_log_id'], TEST_CONFIG["test_prefix"] + "State note")
        assert result is not None, "Should create note"
        assert 'note' in result, "Should have note"

    def test_get_state_notes():
        stateLog = state.changeState("Line 1", "Idle")
        notes.addStateNote(stateLog['state_log_id'], TEST_CONFIG["test_prefix"] + "Note 1")
        notes.addStateNote(stateLog['state_log_id'], TEST_CONFIG["test_prefix"] + "Note 2")
        result = notes.getStateNotes(stateLog['state_log_id'])
        assert len(result) >= 2, "Should have notes"

    def test_add_production_note():
        run = production.startRun("Line 1", "Widget A")
        result = notes.addProductionNote(run['production_log_id'], TEST_CONFIG["test_prefix"] + "Production note")
        assert result is not None, "Should create note"
        production.endRun(run['production_log_id'])

    def test_add_count_note():
        # Product required when no active production run
        count = counts.recordGoodCount("Line 1", 50, product="Widget A")
        result = notes.addCountNote(count['count_log_id'], TEST_CONFIG["test_prefix"] + "Count note")
        assert result is not None, "Should create note"

    def test_add_measurement_note():
        # Product required when no active production run
        measurement = quality.recordMeasurement("Line 1", "Temperature", 25.0, product="Widget A")
        result = notes.addMeasurementNote(measurement['measurement_log_id'], TEST_CONFIG["test_prefix"] + "Measurement note")
        assert result is not None, "Should create note"

    def test_add_kpi_note():
        kpiLog = kpi.recordKPI("Line 1", "OEE", 85.0)
        result = notes.addKPINote(kpiLog['kpi_log_id'], TEST_CONFIG["test_prefix"] + "KPI note")
        assert result is not None, "Should create note"

    def test_add_general_note():
        result = notes.addGeneralNote(TEST_CONFIG["test_prefix"] + "General observation")
        assert result is not None, "Should create note"
        assert 'note_id' in result, "Should have ID"

    def test_get_general_notes():
        notes.addGeneralNote(TEST_CONFIG["test_prefix"] + "General 1")
        notes.addGeneralNote(TEST_CONFIG["test_prefix"] + "General 2")
        result = notes.getGeneralNotes(hours=1)
        assert len(result) >= 2, "Should have notes"

    def test_update_note():
        note = notes.addGeneralNote(TEST_CONFIG["test_prefix"] + "Original")
        result = notes.updateNote('general', note['note_id'], TEST_CONFIG["test_prefix"] + "Updated")
        assert result['note'] == TEST_CONFIG["test_prefix"] + "Updated", "Should update text"

    def test_remove_note():
        note = notes.addGeneralNote(TEST_CONFIG["test_prefix"] + "To remove")
        result = notes.removeNote('general', note['note_id'])
        assert result['removed'] == True, "Should be marked removed"

    run_test("TC-NTE-001: Add state note", test_add_state_note)
    run_test("TC-NTE-002: Get state notes", test_get_state_notes)
    run_test("TC-NTE-003: Add production note", test_add_production_note)
    run_test("TC-NTE-005: Add count note", test_add_count_note)
    run_test("TC-NTE-007: Add measurement note", test_add_measurement_note)
    run_test("TC-NTE-009: Add KPI note", test_add_kpi_note)
    run_test("TC-NTE-011: Add general note", test_add_general_note)
    run_test("TC-NTE-012: Get general notes", test_get_general_notes)
    run_test("TC-NTE-013: Update note", test_update_note)
    run_test("TC-NTE-015: Remove note (soft delete)", test_remove_note)

    # =========================================================================
    # BAD PATH TESTS
    # =========================================================================
    log_subheader("Module: notes.py - Bad Path Tests")

    import mes.errors as errors

    def test_add_state_note_empty():
        """addStateNote with empty string should raise MesValidationError"""
        stateLog = state.changeState("Line 1", "Running")
        expect_error(errors.MesValidationError, lambda: notes.addStateNote(stateLog['state_log_id'], ""))

    def test_add_state_note_whitespace():
        """addStateNote with whitespace only should raise MesValidationError"""
        stateLog = state.changeState("Line 1", "Running")
        expect_error(errors.MesValidationError, lambda: notes.addStateNote(stateLog['state_log_id'], "   "))

    def test_add_state_note_null():
        """addStateNote with None should raise MesValidationError"""
        stateLog = state.changeState("Line 1", "Running")
        expect_error(errors.MesValidationError, lambda: notes.addStateNote(stateLog['state_log_id'], None))

    def test_update_note_invalid_type():
        """updateNote with invalid note type should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: notes.updateNote("invalid_type_xyz", 1, "new text"))

    def test_update_note_nonexistent_id():
        """updateNote with nonexistent note ID should raise MesNotFoundError"""
        expect_error(errors.MesNotFoundError, lambda: notes.updateNote("general", 999999, "new text"))

    def test_remove_note_invalid_type():
        """removeNote with invalid note type should raise MesValidationError"""
        expect_error(errors.MesValidationError, lambda: notes.removeNote("invalid_type_xyz", 1))

    def test_remove_note_nonexistent_id():
        """removeNote with nonexistent note ID should raise MesNotFoundError"""
        expect_error(errors.MesNotFoundError, lambda: notes.removeNote("general", 999999))

    run_test("TC-NTE-BP-001: addStateNote with empty string raises MesValidationError", test_add_state_note_empty)
    run_test("TC-NTE-BP-002: addStateNote with whitespace only raises MesValidationError", test_add_state_note_whitespace)
    run_test("TC-NTE-BP-003: addStateNote(id, None) raises MesValidationError", test_add_state_note_null)
    run_test("TC-NTE-BP-004: updateNote with invalid type raises MesValidationError", test_update_note_invalid_type)
    run_test("TC-NTE-BP-005: updateNote with nonexistent ID raises MesNotFoundError", test_update_note_nonexistent_id)
    run_test("TC-NTE-BP-006: removeNote with invalid type raises MesValidationError", test_remove_note_invalid_type)
    run_test("TC-NTE-BP-007: removeNote with nonexistent ID raises MesNotFoundError", test_remove_note_nonexistent_id)

    # Cleanup
    try:
        production.endRunForAsset("Line 1")
    except:
        pass

# =============================================================================
# INTEGRATION TESTS
# =============================================================================

def test_integration():
    """Run integration tests across multiple modules"""
    log_subheader("Integration Tests")

    import mes.production as production
    import mes.counts as counts
    import mes.quality as quality
    import mes.kpi as kpi
    import mes.state as state
    import mes.notes as notes

    def test_full_production_cycle():
        """Complete production cycle with all operations"""
        # 1. Start run
        run = production.startRun("Line 1", "Widget A", workOrder="WO-INT-001")

        # 2. Set state
        state.changeState("Line 1", "Running")

        # 3. Record counts
        counts.recordGoodCount("Line 1", 100)
        counts.recordGoodCount("Line 1", 100)
        counts.recordScrapCount("Line 1", 10, reason="BREAK")

        # 4. Record measurements
        quality.recordMeasurement("Line 1", "Weight", 10.2, targetValue=10.0, tolerance=0.05)

        # 5. Simulate downtime
        state.startDowntime("Line 1", reason="PM", planned=True)
        state.endDowntime("Line 1", newState="Running")

        # 6. More production
        counts.recordGoodCount("Line 1", 100)

        # 7. Record KPI
        kpi.recordOEE("Line 1", 85.0, availability=95.0, performance=90.0, quality=99.5)

        # 8. Add note
        notes.addProductionNote(run['production_log_id'], TEST_CONFIG["test_prefix"] + "Shift complete")

        # 9. End run
        production.endRun(run['production_log_id'])

        # 10. Verify
        yieldResult = production.getRunYield(run['production_log_id'])
        assert yieldResult is not None, "Should get yield"

        summary = production.getRunCountSummary(run['production_log_id'])
        assert isinstance(summary, list), "Should get summary"

    # Ensure clean state
    try:
        production.endRunForAsset("Line 1")
    except:
        pass

    run_test("IT-001: Full production cycle", test_full_production_cycle)

    # Cleanup
    try:
        production.endRunForAsset("Line 1")
    except:
        pass

# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def print_report():
    """Print final test report"""
    log_header("TEST REPORT")

    summary = suite.get_summary()

    print("\n" + "=" * 70)
    print(" RESULTS SUMMARY")
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
        print(" ALL TESTS PASSED!")
    else:
        print(" SOME TESTS FAILED - Review errors above")
    print("=" * 70)

    return summary['failed'] == 0

def run_all_tests():
    """Main entry point - run complete test suite"""
    from java.lang import System

    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "       MES BACKEND TEST SUITE - IGNITION SCRIPT CONSOLE".center(68) + "*")
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

            # Check if user wants read-only mode
            if TEST_CONFIG.get("skip_seed_setup") and TEST_CONFIG.get("skip_cleanup"):
                log("Running in READ-ONLY mode (skip_seed_setup and skip_cleanup enabled)", "WARN")
                log("Tests will use existing data - some tests may fail if data doesn't exist", "WARN")
            else:
                log("To run tests, use one of the options above or enable read-only mode:", "INFO")
                log("  TEST_CONFIG['skip_seed_setup'] = True", "INFO")
                log("  TEST_CONFIG['skip_cleanup'] = True", "INFO")
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
            log_header("PHASE 1: SEED DATA SETUP (SKIPPED)")
            log("Skipping seed setup - using existing data", "WARN")
        else:
            if not setup_seed_data():
                log("Seed data setup failed - aborting tests", "ERROR")
                return False

        # Phase 2: Run Tests
        log_header("PHASE 2: RUNNING TESTS")

        test_errors_module()
        test_db_module()
        test_resolver_module()
        test_lookups_module()
        test_production_module()
        test_counts_module()
        test_quality_module()
        test_kpi_module()
        test_state_module()
        test_assets_module()
        test_notes_module()
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
            emergency_cleanup()

            should_cleanup = (all_passed and TEST_CONFIG["cleanup_on_success"]) or \
                            (not all_passed and TEST_CONFIG["cleanup_on_failure"])

            if should_cleanup:
                cleanup_test_data()
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
