"""
OEE Diagnostic Script - Paste into Ignition Script Console
Tests each step of the OEE calculation chain to find where 100% comes from.
"""
from mes import kpiCalc

# === CONFIGURATION ===
# Asset 25 = Filler on Line 1 (has count data through Feb 8)
ASSET_ID = 25
# Production runs ended Feb 4, so test BOTH windows:
HOURS_RECENT = 24       # Last 24h (likely no production_log entries)
DAYS_WITH_DATA = 14     # Last 14 days (covers production runs from Jan 27)

print("=" * 60)
print("OEE DIAGNOSTIC - Asset %d" % ASSET_ID)
print("=" * 60)

# ------------------------------------------------------------------
# TEST 1: Verify the count type fix is deployed
# ------------------------------------------------------------------
print("\n--- TEST 1: Count Type Fix Deployed? ---")
good = kpiCalc.getGoodQuantity(ASSET_ID, days=DAYS_WITH_DATA)
scrap = kpiCalc.getScrapQuantity(ASSET_ID, days=DAYS_WITH_DATA)
infeed = kpiCalc.getInfeedQuantity(ASSET_ID, days=DAYS_WITH_DATA)
produced = kpiCalc.getProducedQuantity(ASSET_ID, days=DAYS_WITH_DATA)
print("  GoodQuantity (14d):     %s" % good)
print("  ScrapQuantity (14d):    %s" % scrap)
print("  InfeedQuantity (14d):   %s" % infeed)
print("  ProducedQuantity (14d): %s" % produced)
if good == 0 and infeed == 0:
	print("  >>> FIX NOT DEPLOYED! All quantities are 0.")
	print("  >>> Redeploy scripts to the Ignition gateway.")
else:
	print("  >>> Fix is deployed. Quantities are non-zero.")

# ------------------------------------------------------------------
# TEST 2: Time elements (state-based)
# ------------------------------------------------------------------
print("\n--- TEST 2: Time Elements (14 day window) ---")
pot = kpiCalc.getPlannedOperationTime(ASSET_ID, days=DAYS_WITH_DATA)
pbt = kpiCalc.getPlannedBusyTime(ASSET_ID, days=DAYS_WITH_DATA)
apt = kpiCalc.getActualProductionTime(ASSET_ID, days=DAYS_WITH_DATA)
running = kpiCalc.getRunningTime(ASSET_ID, days=DAYS_WITH_DATA)
plannedDT = kpiCalc.getPlannedDowntime(ASSET_ID, days=DAYS_WITH_DATA)
unplannedDT = kpiCalc.getUnplannedDowntime(ASSET_ID, days=DAYS_WITH_DATA)
print("  POT (planned operation):   %.1f sec (%.1f hrs)" % (pot, pot/3600))
print("  PBT (planned busy):        %.1f sec (%.1f hrs)" % (pbt, pbt/3600))
print("  APT (actual production):   %.1f sec (%.1f hrs)" % (apt, apt/3600))
print("  Running Time:              %.1f sec (%.1f hrs)" % (running, running/3600))
print("  Planned Downtime:          %.1f sec (%.1f hrs)" % (plannedDT, plannedDT/3600))
print("  Unplanned Downtime:        %.1f sec (%.1f hrs)" % (unplannedDT, unplannedDT/3600))
if pbt <= 0:
	print("  >>> PBT=0 means Availability defaults to 100%!")

# ------------------------------------------------------------------
# TEST 3: OEE components (14 day window)
# ------------------------------------------------------------------
print("\n--- TEST 3: OEE Components (14 day window) ---")
avail = kpiCalc.getAvailability(ASSET_ID, days=DAYS_WITH_DATA)
perf = kpiCalc.getPerformanceEfficiency(ASSET_ID, days=DAYS_WITH_DATA)
qual = kpiCalc.getQualityRatio(ASSET_ID, days=DAYS_WITH_DATA)
oee = kpiCalc.getOEE(ASSET_ID, days=DAYS_WITH_DATA)
print("  Availability:  %.2f%%" % avail)
print("  Performance:   %.2f%%" % perf)
print("  Quality:       %.2f%%" % qual)
print("  OEE:           %.2f%%" % oee)

# Check WHY performance might be 100%
actualRate = kpiCalc.getActualRate(ASSET_ID, days=DAYS_WITH_DATA)
idealRate = kpiCalc.getIdealRate(ASSET_ID, days=DAYS_WITH_DATA)
print("\n  ActualRate:  %s units/hr" % actualRate)
print("  IdealRate:   %s units/hr" % idealRate)
if idealRate is None:
	print("  >>> IdealRate=None means Performance defaults to 100%!")
	print("  >>> This happens when no production_log entries exist in the time range.")
	print("  >>> Check: are production runs being created?")

# ------------------------------------------------------------------
# TEST 4: Compare 24h vs 14d to show time range effect
# ------------------------------------------------------------------
print("\n--- TEST 4: 24h vs 14d Comparison ---")
oee_24h = kpiCalc.getOEE(ASSET_ID, hours=HOURS_RECENT)
oee_14d = kpiCalc.getOEE(ASSET_ID, days=DAYS_WITH_DATA)
perf_24h = kpiCalc.getPerformanceEfficiency(ASSET_ID, hours=HOURS_RECENT)
perf_14d = kpiCalc.getPerformanceEfficiency(ASSET_ID, days=DAYS_WITH_DATA)
ideal_24h = kpiCalc.getIdealRate(ASSET_ID, hours=HOURS_RECENT)
ideal_14d = kpiCalc.getIdealRate(ASSET_ID, days=DAYS_WITH_DATA)
print("  OEE (24h):          %.2f%%   |  OEE (14d):          %.2f%%" % (oee_24h, oee_14d))
print("  Performance (24h):  %.2f%%   |  Performance (14d):  %.2f%%" % (perf_24h, perf_14d))
print("  IdealRate (24h):    %s   |  IdealRate (14d):    %s" % (ideal_24h, ideal_14d))

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
