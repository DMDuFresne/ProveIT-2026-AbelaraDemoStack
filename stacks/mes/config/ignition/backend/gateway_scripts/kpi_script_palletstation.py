"""
Gateway Event - Scheduled Script: PalletStation KPI Calculation
KPIs: OEE, Availability, Performance, Quality, MTBF, MTTR, RejectRate
"""
from mes import kpiCalc, assets

ASSET_TYPE = "PalletStation"
HOURS = 8

logger = system.util.getLogger("KPI_" + ASSET_TYPE)

# Snap endTime to the exact hour boundary (floor to current hour)
now = system.date.now()
endTime = system.date.setTime(now, system.date.getHour24(now), 0, 0)
startTime = system.date.addHours(endTime, -HOURS)

assetList = assets.getAssetsByType(ASSET_TYPE)
logger.debug("Processing %d %s assets" % (len(assetList), ASSET_TYPE))

for asset in assetList:
	tagPath = asset.get('tag_path')
	assetId = asset.get('asset_id')
	assetName = asset.get('asset_name', 'Unknown')

	if not tagPath:
		logger.warn("Asset '%s' has no tag_path, skipping" % assetName)
		continue

	kpis = {
		'OEE': kpiCalc.getOEE,
		'Availability': kpiCalc.getAvailability,
		'Performance': kpiCalc.getPerformanceEfficiency,
		'Quality': kpiCalc.getQualityRatio,
		'MTBF': kpiCalc.getMTBF,
		'MTTR': kpiCalc.getMTTR,
		'RejectRate': kpiCalc.getRejectRate,
	}

	for kpiName, calcFunc in kpis.items():
		try:
			value = calcFunc(assetId, startTime=startTime, endTime=endTime)
			if value is None:
				continue

			basePath = "[MES]" + tagPath + "/KPIs/" + kpiName

			# Step 1: Write KPI values first
			valuePaths = [basePath + "/Value", basePath + "/StartTimestamp", basePath + "/EndTimestamp"]
			valueData = [value, startTime, endTime]
			results = system.tag.writeBlocking(valuePaths, valueData)

			if not all(r.isGood() for r in results):
				logger.warn("Value write failed: %s/%s" % (assetName, kpiName))
				continue

			# Step 2: Set LogTrigger AFTER values committed
			triggerResult = system.tag.writeBlocking([basePath + "/LogTrigger"], [True])

			if all(r.isGood() for r in triggerResult):
				logger.debug("%s/%s = %.2f" % (assetName, kpiName, value))
			else:
				logger.warn("Trigger write failed: %s/%s" % (assetName, kpiName))
		except Exception, e:
			logger.error("%s/%s error: %s" % (assetName, kpiName, str(e)))
