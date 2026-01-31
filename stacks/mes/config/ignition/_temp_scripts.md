# MES UDT Tag Change Scripts

All scripts use domain wrappers (`mes.assets`, `mes.lookups`) instead of resolvers directly.

**Consistent Pattern:**
- `initialChange` check first (skip initial subscription)
- Quality check via `currentValue.quality.isNotGood()`
- Change detection via `previousValue.value == currentValue.value`
- Try/except with `MesResolutionError` for lookups
- Clear fields on error or invalid ID
- Logger via `gateway.logger.tag_path_to_logger(tagPath)`
- **Uses TABS for indentation**

---

## 1. Definition/Id (Asset) - valueChanged Script

**Apply to:** `Definition/Id`

```python
# Definition/Id (Asset) - valueChanged Script
# Uses: mes.assets.getAsset()

def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
	# Skip initial subscription
	if initialChange:
		return

	# Skip bad quality
	if currentValue.quality.isNotGood():
		return

	# Skip if no actual change
	if previousValue.value == currentValue.value:
		return

	from mes import assets
	from mes.errors import MesResolutionError

	# Create the Event Logger
	logger_name = gateway.logger.tag_path_to_logger(tagPath)
	logger = gateway.logger.create_logger(logger_name)

	def clearFields(parent_path):
		paths = [
			parent_path + '/Name',
			parent_path + '/Description',
			parent_path + '/TypeId',
			parent_path + '/TypeName',
			parent_path + '/TagPath',
			parent_path + '/ParentId'
		]
		values = ['', '', None, '', '', None]
		system.tag.writeBlocking(paths, values)

	parent_path = '/'.join(tagPath.split('/')[:-1])
	tag_value = currentValue.value

	# Clear if null or invalid
	if tag_value is None or tag_value <= 0:
		clearFields(parent_path)
		return

	try:
		asset = assets.getAsset(tag_value)

		paths = [
			parent_path + '/Name',
			parent_path + '/Description',
			parent_path + '/TypeId',
			parent_path + '/TypeName',
			parent_path + '/TagPath',
			parent_path + '/ParentId'
		]
		values = [
			asset.get('asset_name', ''),
			asset.get('asset_description', '') or '',
			asset.get('asset_type_id'),
			asset.get('asset_type_name', '') or '',
			asset.get('tag_path', '') or '',
			asset.get('parent_asset_id')
		]
		system.tag.writeBlocking(paths, values)
		logger.debug("Asset loaded: {} (ID: {})".format(asset.get('asset_name'), tag_value))

	except MesResolutionError:
		clearFields(parent_path)
		logger.warn("Asset ID {} not found - fields cleared".format(tag_value))
	except Exception as e:
		clearFields(parent_path)
		logger.error("Asset lookup failed for {}: {} - fields cleared".format(tag_value, e))
```

---

## 2. State/Id - valueChanged Script

**Apply to:** `State/Id`

```python
# State/Id - valueChanged Script
# Uses: mes.lookups.getState(), mes.state.changeState()

def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
	# Skip initial subscription
	if initialChange:
		return

	# Skip bad quality
	if currentValue.quality.isNotGood():
		return

	# Skip if no actual change
	last_value = previousValue.value
	tag_value = currentValue.value
	if last_value == tag_value:
		return

	from mes import lookups
	from mes import state as mes_state
	from mes.errors import MesResolutionError

	# Create the Event Logger
	logger_name = gateway.logger.tag_path_to_logger(tagPath)
	logger = gateway.logger.create_logger(logger_name)

	def clearFields(parent_path):
		paths = [
			parent_path + '/Name',
			parent_path + '/TypeId',
			parent_path + '/TypeName',
			parent_path + '/IsDowntime',
			parent_path + '/Color',
			parent_path + '/LogId',
			parent_path + '/LastChangedOn',
			parent_path + '/FromId',
			parent_path + '/FromName'
		]
		values = ['', None, '', False, '', None, None, None, '']
		system.tag.writeBlocking(paths, values)

	parent_path = '/'.join(tagPath.split('/')[:-1])
	equipment_path = '/'.join(tagPath.split('/')[:-2])

	# Clear if null or invalid
	if tag_value is None or tag_value <= 0:
		clearFields(parent_path)
		return

	# Get asset_id from Definition sibling
	asset_id_path = equipment_path + '/Definition/Id'
	asset_id = system.tag.readBlocking([asset_id_path])[0].value

	if asset_id is None or asset_id <= 0:
		logger.error("Cannot log state - Definition/Id not set at {}".format(asset_id_path))
		clearFields(parent_path)
		return

	try:
		# Lookup state info
		state_info = lookups.getState(tag_value)

		# Log state change to database
		result = mes_state.changeState(asset=asset_id, newState=tag_value)

		if result is None:
			clearFields(parent_path)
			logger.error("changeState returned None for state {}".format(tag_value))
			return

		# Get from_name from previous state
		from_name = ''
		if last_value and last_value > 0:
			try:
				from_state = lookups.getState(last_value)
				from_name = from_state.get('state_name', '')
			except:
				pass

		paths = [
			parent_path + '/Name',
			parent_path + '/TypeId',
			parent_path + '/TypeName',
			parent_path + '/IsDowntime',
			parent_path + '/Color',
			parent_path + '/LogId',
			parent_path + '/LastChangedOn',
			parent_path + '/FromId',
			parent_path + '/FromName'
		]
		values = [
			state_info.get('state_name', ''),
			state_info.get('state_type_id'),
			state_info.get('state_type_name', '') or '',
			state_info.get('is_downtime', False) or False,
			state_info.get('color', '') or '',
			result.get('state_log_id'),
			system.date.now(),
			result.get('from_state_id') or last_value,
			from_name
		]
		system.tag.writeBlocking(paths, values)
		logger.debug("State logged: {} (ID: {}, LogId: {})".format(
			state_info.get('state_name'), tag_value, result.get('state_log_id')))

	except MesResolutionError:
		clearFields(parent_path)
		logger.warn("State ID {} not found - fields cleared".format(tag_value))
	except Exception as e:
		clearFields(parent_path)
		logger.error("State logging failed for {}: {} - fields cleared".format(tag_value, e))
```

---

## 3. Product/ProductId - valueChanged Script

**Apply to:** `Product/ProductId`

```python
# Product/ProductId - valueChanged Script
# Uses: mes.lookups.getProduct()

def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
	# Skip initial subscription
	if initialChange:
		return

	# Skip bad quality
	if currentValue.quality.isNotGood():
		return

	# Skip if no actual change
	if previousValue.value == currentValue.value:
		return

	from mes import lookups
	from mes.errors import MesResolutionError

	# Create the Event Logger
	logger_name = gateway.logger.tag_path_to_logger(tagPath)
	logger = gateway.logger.create_logger(logger_name)

	def clearFields(parent_path):
		paths = [
			parent_path + '/ProductName',
			parent_path + '/ProductDescription',
			parent_path + '/ProductFamilyId',
			parent_path + '/ProductFamilyName',
			parent_path + '/UnitsOfMeasure',
			parent_path + '/Tolerance',
			parent_path + '/IdealCycleTime'
		]
		values = ['', '', None, '', '', 0.0, 0.0]
		system.tag.writeBlocking(paths, values)

	parent_path = '/'.join(tagPath.split('/')[:-1])
	tag_value = currentValue.value

	# Clear if null or invalid
	if tag_value is None or tag_value <= 0:
		clearFields(parent_path)
		return

	try:
		product = lookups.getProduct(tag_value)

		paths = [
			parent_path + '/ProductName',
			parent_path + '/ProductDescription',
			parent_path + '/ProductFamilyId',
			parent_path + '/ProductFamilyName',
			parent_path + '/UnitsOfMeasure',
			parent_path + '/Tolerance',
			parent_path + '/IdealCycleTime'
		]
		values = [
			product.get('product_name', ''),
			product.get('product_description', '') or '',
			product.get('product_family_id'),
			product.get('product_family_name', '') or '',
			product.get('unit_of_measure', '') or '',
			product.get('tolerance', 0.0) or 0.0,
			product.get('ideal_cycle_time', 0.0) or 0.0
		]
		system.tag.writeBlocking(paths, values)
		logger.debug("Product loaded: {} (ID: {})".format(product.get('product_name'), tag_value))

	except MesResolutionError:
		clearFields(parent_path)
		logger.warn("Product ID {} not found - fields cleared".format(tag_value))
	except Exception as e:
		clearFields(parent_path)
		logger.error("Product lookup failed for {}: {} - fields cleared".format(tag_value, e))
```

---

## 3a. ProductLiquid/ProductId - valueChanged Script

**Apply to:** `ProductLiquid/ProductId` (extends Product UDT with liquid attributes)

**UDT Type:** `Models/Objects/Product` (ProductLiquid variant)

**Additional tags populated:**
- `Density` - Liquid density in kg/m³
- `DensityUnitsOfMeasure` - UOM string (default: 'kg/m³')
- `Viscosity` - Dynamic viscosity in mPa·s (centiPoise)
- `ViscosityUnitsOfMeasure` - UOM string (default: 'mPa·s')

```python
# ProductLiquid/ProductId - valueChanged Script
# Uses: mes.lookups.getProduct(), mes.custom.getLiquidAttributesByProduct()
# Extends base Product script with liquid attribute lookup

def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
	# Skip initial subscription
	if initialChange:
		return

	# Skip bad quality
	if currentValue.quality.isNotGood():
		return

	# Skip if no actual change
	if previousValue.value == currentValue.value:
		return

	from mes import lookups
	from mes import custom
	from mes.errors import MesResolutionError

	# Create the Event Logger
	logger_name = gateway.logger.tag_path_to_logger(tagPath)
	logger = gateway.logger.create_logger(logger_name)

	def clearFields(parent_path):
		paths = [
			# Base product fields
			parent_path + '/ProductName',
			parent_path + '/ProductDescription',
			parent_path + '/ProductFamilyId',
			parent_path + '/ProductFamilyName',
			parent_path + '/UnitOfMeasure',
			parent_path + '/Tolerance',
			parent_path + '/IdealCycleTime',
			# Liquid attribute fields
			parent_path + '/Density',
			parent_path + '/DensityUnitsOfMeasure',
			parent_path + '/Viscosity',
			parent_path + '/ViscosityUnitsOfMeasure'
		]
		values = ['', '', None, '', '', 0.0, 0.0, 0.0, '', 0.0, '']
		system.tag.writeBlocking(paths, values)

	parent_path = '/'.join(tagPath.split('/')[:-1])
	tag_value = currentValue.value

	# Clear if null or invalid
	if tag_value is None or tag_value <= 0:
		clearFields(parent_path)
		return

	try:
		# Get base product info
		product = lookups.getProduct(tag_value)

		paths = [
			parent_path + '/ProductName',
			parent_path + '/ProductDescription',
			parent_path + '/ProductFamilyId',
			parent_path + '/ProductFamilyName',
			parent_path + '/UnitOfMeasure',
			parent_path + '/Tolerance',
			parent_path + '/IdealCycleTime'
		]
		values = [
			product.get('product_name', ''),
			product.get('product_description', '') or '',
			product.get('product_family_id'),
			product.get('product_family_name', '') or '',
			product.get('unit_of_measure', '') or '',
			product.get('tolerance', 0.0) or 0.0,
			product.get('ideal_cycle_time', 0.0) or 0.0
		]
		system.tag.writeBlocking(paths, values)
		logger.debug("Product loaded: {} (ID: {})".format(product.get('product_name'), tag_value))

		# Get liquid attributes (may be None if product has no liquid properties)
		# Note: Use custom.xref.* to access functions directly from submodule
		liquid = custom.xref.getLiquidAttributesByProduct(tag_value)

		if liquid is not None:
			liquid_paths = [
				parent_path + '/Density',
				parent_path + '/DensityUnitsOfMeasure',
				parent_path + '/Viscosity',
				parent_path + '/ViscosityUnitsOfMeasure'
			]
			liquid_values = [
				liquid.get('density', 0.0) or 0.0,
				liquid.get('density_uom', '') or '',
				liquid.get('viscosity', 0.0) or 0.0,
				liquid.get('viscosity_uom', '') or ''
			]
			system.tag.writeBlocking(liquid_paths, liquid_values)
			logger.debug("Liquid attributes loaded: density={} {}, viscosity={} {}".format(
				liquid.get('density'), liquid.get('density_uom'),
				liquid.get('viscosity'), liquid.get('viscosity_uom')))
		else:
			# No liquid attributes - clear liquid fields only
			liquid_paths = [
				parent_path + '/Density',
				parent_path + '/DensityUnitsOfMeasure',
				parent_path + '/Viscosity',
				parent_path + '/ViscosityUnitsOfMeasure'
			]
			liquid_values = [0.0, '', 0.0, '']
			system.tag.writeBlocking(liquid_paths, liquid_values)
			logger.debug("No liquid attributes for product ID {}".format(tag_value))

	except MesResolutionError:
		clearFields(parent_path)
		logger.warn("Product ID {} not found - fields cleared".format(tag_value))
	except Exception as e:
		clearFields(parent_path)
		logger.error("Product lookup failed for {}: {} - fields cleared".format(tag_value, e))
```

---

## 4. Downtime/ReasonId - valueChanged Script

**Apply to:** `Downtime/ReasonId`

```python
# Downtime/ReasonId - valueChanged Script
# Uses: mes.lookups.getDowntimeReason()

def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
	# Skip initial subscription
	if initialChange:
		return

	# Skip bad quality
	if currentValue.quality.isNotGood():
		return

	# Skip if no actual change
	if previousValue.value == currentValue.value:
		return

	from mes import lookups
	from mes.errors import MesResolutionError

	# Create the Event Logger
	logger_name = gateway.logger.tag_path_to_logger(tagPath)
	logger = gateway.logger.create_logger(logger_name)

	def clearFields(parent_path):
		paths = [
			parent_path + '/ReasonCode',
			parent_path + '/ReasonName'
		]
		values = ['', '']
		system.tag.writeBlocking(paths, values)

	parent_path = '/'.join(tagPath.split('/')[:-1])
	tag_value = currentValue.value

	# Clear if null or invalid
	if tag_value is None or tag_value <= 0:
		clearFields(parent_path)
		return

	try:
		reason = lookups.getDowntimeReason(tag_value)

		paths = [
			parent_path + '/ReasonCode',
			parent_path + '/ReasonName'
		]
		values = [
			reason.get('downtime_reason_code', ''),
			reason.get('downtime_reason_name', '')
		]
		system.tag.writeBlocking(paths, values)
		logger.debug("Downtime reason loaded: {} (ID: {})".format(
			reason.get('downtime_reason_name'), tag_value))

	except MesResolutionError:
		clearFields(parent_path)
		logger.warn("Downtime Reason ID {} not found - fields cleared".format(tag_value))
	except Exception as e:
		clearFields(parent_path)
		logger.error("Downtime lookup failed for {}: {} - fields cleared".format(tag_value, e))
```

---

## 5. Count/TypeId - valueChanged Script

**Apply to:** `Counts/Infeed/TypeId`, `Counts/Outfeed/TypeId`, `Counts/Waste/TypeId`

```python
# Count/TypeId - valueChanged Script
# Uses: mes.lookups.getCountType()

def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
	# Skip initial subscription
	if initialChange:
		return

	# Skip bad quality
	if currentValue.quality.isNotGood():
		return

	# Skip if no actual change
	if previousValue.value == currentValue.value:
		return

	from mes import lookups
	from mes.errors import MesResolutionError

	# Create the Event Logger
	logger_name = gateway.logger.tag_path_to_logger(tagPath)
	logger = gateway.logger.create_logger(logger_name)

	count_folder_path = tagPath.rsplit("/", 1)[0]
	type_name_path = count_folder_path + "/TypeName"
	tag_value = currentValue.value

	# Clear if null or invalid
	if tag_value is None or tag_value <= 0:
		system.tag.writeBlocking([type_name_path], [""])
		return

	try:
		count_type = lookups.getCountType(tag_value)

		system.tag.writeBlocking([type_name_path], [count_type.get('count_type_name', '')])
		logger.debug("Count type loaded: {} (ID: {})".format(
			count_type.get('count_type_name'), tag_value))

	except MesResolutionError:
		system.tag.writeBlocking([type_name_path], [""])
		logger.warn("Count Type ID {} not found - field cleared".format(tag_value))
	except Exception as e:
		system.tag.writeBlocking([type_name_path], [""])
		logger.error("Count type lookup failed for {}: {} - field cleared".format(tag_value, e))
```

---

## 6. Edge Count Tags - valueChanged Script

**Apply to:** `Edge/CountInfeed`, `Edge/CountOutfeed`, `Edge/CountDefect`

**Required sibling tags in Edge folder:**
- `CountInfeedLast`, `CountOutfeedLast`, `CountDefectLast` (Memory, Int8) ✓ exists
- `CountInfeedLastAt`, `CountOutfeedLastAt`, `CountDefectLastAt` (Memory, DateTime) ⚠️ ADD THESE

```python
# Edge Count - valueChanged Script
#
# Detects delta from cumulative edge values and writes to Counts UDT.
# Reads last value from persistent CountXxxLast tag (survives gateway restart).
# Stores timestamp in CountXxxAt tag.
# On rollover/reset (negative delta), we DROP the reading.
# NOTE: For production, consider rollover handling if max counter is known.

def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
	# Skip initial subscription
	if initialChange:
		return

	# Skip bad quality
	if currentValue.quality.isNotGood():
		return

	new_value = currentValue.value

	# Skip if null
	if new_value is None:
		return

	# Create the Event Logger
	logger_name = gateway.logger.tag_path_to_logger(tagPath)
	logger = gateway.logger.create_logger(logger_name)

	# Determine tag name and build sibling paths
	tag_name = tagPath.rsplit("/", 1)[1]
	edge_folder_path = tagPath.rsplit("/", 1)[0]

	last_path = edge_folder_path + "/" + tag_name + "Last"
	last_at_path = edge_folder_path + "/" + tag_name + "LastAt"

	try:
		# Read last value from persistent tag
		last_result = system.tag.readBlocking([last_path])[0]
		old_value = last_result.value if last_result.quality.isGood() else None

		# Skip if no valid last value (first read - just store current)
		if old_value is None:
			system.tag.writeBlocking([last_path, last_at_path], [new_value, system.date.now()])
			logger.debug("First read for {} - stored baseline: {}".format(tag_name, new_value))
			return

		# Skip if no actual change
		if new_value == old_value:
			return

		# Calculate delta
		delta = new_value - old_value

		# DROP on rollover - negative delta means counter reset
		# NOTE: For production, consider recovery if max counter value is known
		if delta <= 0:
			# Still update last/at so we track the new baseline
			system.tag.writeBlocking([last_path, last_at_path], [new_value, system.date.now()])
			logger.debug("Rollover detected for {} - new baseline: {} (was: {})".format(tag_name, new_value, old_value))
			return

		# Map source tag to destination Counts folder
		counts_folder_map = {
			"CountInfeed": "Infeed",
			"CountOutfeed": "Outfeed",
			"CountDefect": "Waste"
		}

		counts_folder = counts_folder_map.get(tag_name)
		if counts_folder is None:
			logger.warn("Unknown edge count tag: {}".format(tag_name))
			return

		# Build target paths
		work_unit_path = edge_folder_path.rsplit("/", 1)[0]

		quantity_path = work_unit_path + "/Counts/" + counts_folder + "/Quantity"
		trigger_path = work_unit_path + "/Counts/" + counts_folder + "/LogTrigger"

		# Write delta and trigger FIRST
		results = system.tag.writeBlocking([quantity_path, trigger_path], [delta, True])

		# Check write succeeded before updating Last/At
		if all(r.isGood() for r in results):
			system.tag.writeBlocking([last_path, last_at_path], [new_value, system.date.now()])
			logger.debug("Count delta {} written to {}, trigger set".format(delta, counts_folder))
		else:
			logger.error("Failed to write count delta to {} - Last/At not updated".format(counts_folder))

	except Exception as e:
		logger.error("Edge count processing failed for {}: {}".format(tag_name, e))
```

---

## 7. Counts/LogTrigger - valueChanged Script

**Apply to:** `Counts/Infeed/LogTrigger`, `Counts/Outfeed/LogTrigger`, `Counts/Waste/LogTrigger`

**NOTE:** This script supports **Unknown product fallback**. If `Product/ProductId` is not set (0 or null), `counts.recordCount()` will use the reserved "Unknown" product (ID=1) and log a data quality warning. Counts are **never lost** due to missing product info.

```python
# Counts/LogTrigger - valueChanged Script
# Uses: mes.counts.recordCount()
# NOTE: Product validation removed - counts.py handles Unknown product fallback (ID=1)

def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
	# Skip initial subscription
	if initialChange:
		return

	# Skip bad quality
	if currentValue.quality.isNotGood():
		return

	# Only fire on rising edge (False -> True)
	if currentValue.value != True:
		return

	# Reset trigger immediately to prevent re-firing
	system.tag.writeBlocking([tagPath], [False])

	from mes import counts

	# Create the Event Logger
	logger_name = gateway.logger.tag_path_to_logger(tagPath)
	logger = gateway.logger.create_logger(logger_name)

	# Build paths
	count_folder_path = tagPath.rsplit("/", 1)[0]
	counts_path = count_folder_path.rsplit("/", 1)[0]
	work_unit_path = counts_path.rsplit("/", 1)[0]

	asset_id_path = work_unit_path + "/Definition/Id"
	product_id_path = work_unit_path + "/Product/ProductId"
	type_id_path = count_folder_path + "/TypeId"
	quantity_path = count_folder_path + "/Quantity"
	log_id_path = count_folder_path + "/LogId"

	# Read required values
	tag_values = system.tag.readBlocking([asset_id_path, product_id_path, type_id_path, quantity_path])
	asset_id = tag_values[0].value
	product_id = tag_values[1].value
	type_id = tag_values[2].value
	quantity = tag_values[3].value

	# Validate asset_id (required - cannot fallback)
	if not asset_id or asset_id <= 0:
		logger.warn("Cannot log count - Definition/Id not set at {}".format(work_unit_path))
		return

	# NOTE: product_id validation removed - counts.py handles Unknown product fallback
	# If product_id is missing, counts.recordCount() will use Unknown product (ID=1)
	# and log a warning for data quality tracking

	# Validate type_id (required - cannot fallback)
	if not type_id or type_id <= 0:
		logger.warn("Cannot log count - TypeId not set at {}".format(count_folder_path))
		return

	# Validate quantity (skip zero/negative)
	if quantity is None or quantity <= 0:
		return

	# Convert product_id: 0 or negative means no product - pass None to let counts.py handle fallback
	product_param = product_id if (product_id and product_id > 0) else None

	try:
		result = counts.recordCount(
			asset=asset_id,
			countType=type_id,
			quantity=quantity,
			product=product_param
		)

		log_id = result.get('count_log_id') if result else None
		system.tag.writeBlocking([log_id_path], [log_id])
		logger.debug("Count logged: qty={}, type={}, asset={}, product={}, LogId={}".format(
			quantity, type_id, asset_id, product_param or 'Unknown', log_id))

	except Exception as e:
		logger.error("Count log error at {}: {}".format(count_folder_path, e))
```

---

## 8. Measurement/TypeId - valueChanged Script

**Apply to:** `Temperature/TypeId`, `Pressure/TypeId`, `FlowRate/TypeId` (any Measurement UDT instance)

```python
# Measurement/TypeId - valueChanged Script
# Uses: mes.lookups.getMeasurementType()

def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
	# Skip initial subscription
	if initialChange:
		return

	# Skip bad quality
	if currentValue.quality.isNotGood():
		return

	# Skip if no actual change
	if previousValue.value == currentValue.value:
		return

	from mes import lookups
	from mes.errors import MesResolutionError

	# Create the Event Logger
	logger_name = gateway.logger.tag_path_to_logger(tagPath)
	logger = gateway.logger.create_logger(logger_name)

	def clearFields(parent_path):
		paths = [
			parent_path + '/TypeName',
			parent_path + '/UnitsOfMeasure'
		]
		values = ['', '']
		system.tag.writeBlocking(paths, values)

	parent_path = tagPath.rsplit('/', 1)[0]
	tag_value = currentValue.value

	# Clear if null or invalid
	if tag_value is None or tag_value <= 0:
		clearFields(parent_path)
		return

	try:
		measurement_type = lookups.getMeasurementType(tag_value)

		paths = [
			parent_path + '/TypeName',
			parent_path + '/UnitsOfMeasure'
		]
		values = [
			measurement_type.get('measurement_type_name', ''),
			measurement_type.get('measurement_type_unit', '') or ''
		]
		system.tag.writeBlocking(paths, values)
		logger.debug('Measurement type loaded: {} (ID: {})'.format(
			measurement_type.get('measurement_type_name'), tag_value))

	except MesResolutionError:
		clearFields(parent_path)
		logger.warn('Measurement Type ID {} not found - fields cleared'.format(tag_value))
	except Exception as e:
		clearFields(parent_path)
		logger.error('Measurement type lookup failed for {}: {} - fields cleared'.format(tag_value, e))
```

---

## 9. Measurement/LogTrigger - valueChanged Script

**Apply to:** `Temperature/LogTrigger`, `Pressure/LogTrigger`, `FlowRate/LogTrigger` (any Measurement UDT instance)

```python
# Measurement/LogTrigger - valueChanged Script
# Uses: mes.quality.recordMeasurement()

def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
	# Skip initial subscription
	if initialChange:
		return

	# Skip bad quality
	if currentValue.quality.isNotGood():
		return

	# Only fire on rising edge (False -> True)
	if currentValue.value != True:
		return

	# Reset trigger immediately to prevent re-firing
	system.tag.writeBlocking([tagPath], [False])

	from mes import quality

	# Create the Event Logger
	logger_name = gateway.logger.tag_path_to_logger(tagPath)
	logger = gateway.logger.create_logger(logger_name)

	# Build paths
	measurement_path = tagPath.rsplit('/', 1)[0]
	equipment_path = measurement_path.rsplit('/', 1)[0]

	asset_id_path = equipment_path + '/Definition/Id'
	product_id_path = equipment_path + '/Product/ProductId'
	type_id_path = measurement_path + '/TypeId'
	value_path = measurement_path + '/ActualValue'
	target_value_path = measurement_path + '/TargetValue'
	tolerance_path = measurement_path + '/Tolerance'
	in_tolerance_path = measurement_path + '/InTolerance'
	unit_path = measurement_path + '/ActualUnitsOfMeasure'
	log_id_path = measurement_path + '/LogId'

	# Read required values
	tag_values = system.tag.readBlocking([
		asset_id_path, product_id_path, type_id_path, value_path,
		target_value_path, tolerance_path, in_tolerance_path, unit_path
	])
	asset_id = tag_values[0].value
	product_id = tag_values[1].value
	type_id = tag_values[2].value
	value = tag_values[3].value
	target_value = tag_values[4].value
	tolerance = tag_values[5].value
	in_tolerance = tag_values[6].value
	unit_of_measure = tag_values[7].value

	# Validate asset_id
	if not asset_id or asset_id <= 0:
		logger.warn('Cannot log measurement - Definition/Id not set at {}'.format(equipment_path))
		return

	# Validate type_id
	if not type_id or type_id <= 0:
		logger.warn('Cannot log measurement - TypeId not set at {}'.format(measurement_path))
		return

	# Validate value
	if value is None:
		logger.warn('Cannot log measurement - Value is null at {}'.format(measurement_path))
		return

	try:
		result = quality.recordMeasurement(
			asset=asset_id,
			measurementType=type_id,
			actualValue=value,
			product=product_id,
			targetValue=target_value,
			tolerance=tolerance,
			inTolerance=in_tolerance,
			unitOfMeasure=unit_of_measure
		)

		log_id = result.get('measurement_log_id') if result else None
		system.tag.writeBlocking([log_id_path], [log_id])
		logger.debug('Measurement logged: value={}, target={}, type={}, asset={}, LogId={}'.format(
			value, target_value, type_id, asset_id, log_id))

	except Exception as e:
		logger.error('Measurement log error at {}: {}'.format(measurement_path, e))
```

---

## 10. KPI/Id - valueChanged Script

**Apply to:** `KPIs/*/Id` (any KPI UDT instance)

```python
# KPI/Id - valueChanged Script
# Uses: mes.lookups.getKPI()

def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
	# Skip initial subscription
	if initialChange:
		return

	# Skip bad quality
	if currentValue.quality.isNotGood():
		return

	# Skip if no actual change
	if previousValue.value == currentValue.value:
		return

	from mes import lookups
	from mes.errors import MesResolutionError

	# Create the Event Logger
	logger_name = gateway.logger.tag_path_to_logger(tagPath)
	logger = gateway.logger.create_logger(logger_name)

	def clearFields(parent_path):
		paths = [
			parent_path + '/Name',
			parent_path + '/UnitsOfMeasure',
			parent_path + '/Formula'
		]
		values = ['', '', '']
		system.tag.writeBlocking(paths, values)

	kpi_folder_path = tagPath.rsplit('/', 1)[0]
	tag_value = currentValue.value

	# Clear if null or invalid
	if tag_value is None or tag_value <= 0:
		clearFields(kpi_folder_path)
		return

	try:
		kpi = lookups.getKPI(tag_value)

		paths = [
			kpi_folder_path + '/Name',
			kpi_folder_path + '/UnitsOfMeasure',
			kpi_folder_path + '/Formula'
		]
		values = [
			kpi.get('kpi_name', ''),
			kpi.get('kpi_unit', '') or '',
			kpi.get('kpi_formula', '') or ''
		]
		system.tag.writeBlocking(paths, values)
		logger.debug('KPI loaded: {} (ID: {})'.format(kpi.get('kpi_name'), tag_value))

	except MesResolutionError:
		clearFields(kpi_folder_path)
		logger.warn('KPI ID {} not found - fields cleared'.format(tag_value))
	except Exception as e:
		clearFields(kpi_folder_path)
		logger.error('KPI lookup failed for {}: {} - fields cleared'.format(tag_value, e))
```

---

## 11. KPI/LogTrigger - valueChanged Script

**Apply to:** `KPIs/*/LogTrigger` (any KPI UDT instance)

```python
# KPI/LogTrigger - valueChanged Script
# Uses: mes.kpi.recordKPI()

def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
	# Skip initial subscription
	if initialChange:
		return

	# Skip bad quality
	if currentValue.quality.isNotGood():
		return

	# Only fire on rising edge (False -> True)
	if currentValue.value != True:
		return

	# Reset trigger immediately to prevent re-firing
	system.tag.writeBlocking([tagPath], [False])

	from mes import kpi

	# Create the Event Logger
	logger_name = gateway.logger.tag_path_to_logger(tagPath)
	logger = gateway.logger.create_logger(logger_name)

	# Build paths
	kpi_folder_path = tagPath.rsplit('/', 1)[0]
	equipment_path = kpi_folder_path.rsplit('/', 2)[0]

	asset_id_path = equipment_path + '/Definition/Id'
	kpi_id_path = kpi_folder_path + '/Id'
	value_path = kpi_folder_path + '/Value'
	start_ts_path = kpi_folder_path + '/StartTimestamp'
	end_ts_path = kpi_folder_path + '/EndTimestamp'
	log_id_path = kpi_folder_path + '/LogId'

	# Read required values
	tag_values = system.tag.readBlocking([
		asset_id_path, kpi_id_path, value_path, start_ts_path, end_ts_path
	])
	asset_id = tag_values[0].value
	kpi_id = tag_values[1].value
	value = tag_values[2].value
	start_timestamp = tag_values[3].value
	end_timestamp = tag_values[4].value

	# Validate asset_id
	if not asset_id or asset_id <= 0:
		logger.warn('Cannot log KPI - Definition/Id not set at {}'.format(equipment_path))
		return

	# Validate kpi_id
	if not kpi_id or kpi_id <= 0:
		logger.warn('Cannot log KPI - Id not set at {}'.format(kpi_folder_path))
		return

	# Validate value
	if value is None:
		logger.warn('Cannot log KPI - Value is null at {}'.format(kpi_folder_path))
		return

	try:
		result = kpi.recordKPI(
			asset=asset_id,
			kpiName=kpi_id,
			value=value,
			startTime=start_timestamp,
			endTime=end_timestamp
		)

		log_id = result.get('kpi_log_id') if result else None
		system.tag.writeBlocking([log_id_path], [log_id])
		logger.debug('KPI logged: value={}, kpiId={}, asset={}, LogId={}'.format(
			value, kpi_id, asset_id, log_id))

	except Exception as e:
		logger.error('KPI log error at {}: {}'.format(kpi_folder_path, e))
```

---

## Function Reference

| Script | Import | Function |
|--------|--------|----------|
| Definition/Id | `from mes import assets` | `assets.getAsset()` |
| State/Id | `from mes import lookups` | `lookups.getState()` |
| Product/ProductId | `from mes import lookups` | `lookups.getProduct()` |
| ProductLiquid/ProductId | `from mes import lookups, custom` | `lookups.getProduct()`, `custom.getLiquidAttributesByProduct()` |
| Downtime/ReasonId | `from mes import lookups` | `lookups.getDowntimeReason()` |
| Count/TypeId | `from mes import lookups` | `lookups.getCountType()` |
| Measurement/TypeId | `from mes import lookups` | `lookups.getMeasurementType()` |
| Counts/LogTrigger | `from mes import counts` | `counts.recordCount()` |
| Measurement/LogTrigger | `from mes import quality` | `quality.recordMeasurement()` |
| KPI/Id | `from mes import lookups` | `lookups.getKPI()` |
| KPI/LogTrigger | `from mes import kpi` | `kpi.recordKPI()` |
| Edge/WorkOrderId | *(triggers Production/Running)* | Cycles production on WO change |

---

## Logger Pattern

All scripts use the tag path-based logger for better traceability:

```python
# Create the Event Logger
logger_name = gateway.logger.tag_path_to_logger(tagPath)
logger = gateway.logger.create_logger(logger_name)
```

This creates a logger specific to the tag that triggered the event, making it easier to trace issues in the Ignition logs.

---

## Scheduled Gateway Script: Log All Measurements

**Type:** Gateway Scheduled Script
**Schedule:** CRON expression (e.g., `0 0/15 * * * ?` for every 15 minutes)

```python
# Scheduled Gateway Script: Log All Measurements
# Finds all Measurement UDT instances and triggers their LogTrigger
# Schedule via Gateway > Scheduled Scripts with CRON expression

logger = system.util.getLogger('MES.ScheduledMeasurementLog')

# Configuration
TAG_PROVIDER = '[MES]'
MEASUREMENT_TYPE_ID = 'Models/Objects/Measurement'
EXCLUDE_PATHS = ['_types_']  # Exclude UDT definition folders

# Find all Measurement UDT instances (excluding _types_ folder)
measurements = []
try:
	results = system.tag.browse(TAG_PROVIDER, {'tagType': 'UdtInstance', 'recursive': True})
	for result in results.getResults():
		path = str(result['fullPath'])
		# Skip UDT definitions in _types_ folder
		if any(exclude in path for exclude in EXCLUDE_PATHS):
			continue
		if result['typeId'] == MEASUREMENT_TYPE_ID:
			measurements.append(path)
except Exception as e:
	logger.error('Error browsing tags: {}'.format(e))

if not measurements:
	logger.debug('No Measurement instances found')
else:
	# Build LogTrigger paths and trigger all
	trigger_paths = [path + '/LogTrigger' for path in measurements]
	trigger_values = [True] * len(trigger_paths)

	try:
		results = system.tag.writeBlocking(trigger_paths, trigger_values)
		success_count = sum(1 for r in results if r.isGood())
		fail_count = len(results) - success_count
		logger.info('Measurement log triggered: {} succeeded, {} failed'.format(success_count, fail_count))
	except Exception as e:
		logger.error('Batch trigger failed: {}'.format(e))
```

### CRON Expression Examples

| Expression | Description |
|------------|-------------|
| `0 0/15 * * * ?` | Every 15 minutes |
| `0 0 * * * ?` | Every hour on the hour |
| `0 0/5 * * * ?` | Every 5 minutes |
| `0 30 * * * ?` | Every hour at :30 |
| `0 0 6,18 * * ?` | Twice daily at 6 AM and 6 PM |
| `0 0 0 * * ?` | Once daily at midnight |

### Setup Instructions

1. Go to **Gateway > Config > Scheduled Scripts**
2. Click **Create new Scheduled Script**
3. Set **Type** to `CRON`
4. Enter your CRON expression
5. Paste the script above
6. Enable the script

---

## 12. Edge/WorkOrderId - valueChanged Script

**Apply to:** `Edge/WorkOrderId`

**Purpose:** When the work order changes (from Pilot UNS), automatically cycle production:
- If WorkOrder is cleared: Stop production (if running)
- If WorkOrder is set: Stop current production (if running) → Start new production

**Dependencies:**
- `Production/Running` script handles the actual DB logging
- `Product/ProductId` must be set before starting production (managed independently by operator or ItemId)

```python
# Edge/WorkOrderId - valueChanged Script
# When work order changes: Cycle production (end current -> start new)
# Product is managed independently via Product/ProductId
# NOTE: Do NOT wrap in def valueChanged() - Ignition provides parameters automatically

# Skip initial subscription
if initialChange:
	return

# Skip bad quality
if currentValue.quality.isNotGood():
	return

# Skip if no actual change
if previousValue.value == currentValue.value:
	return

logger = system.util.getLogger('MES.WorkOrder')

try:
	# Build paths
	edge_path = '/'.join(tagPath.split('/')[:-1])  # Edge folder
	equipment_path = '/'.join(tagPath.split('/')[:-2])  # WorkUnit/WorkCenter
	production_running_path = equipment_path + '/Production/Running'

	work_order_id = currentValue.value

	# Read current production state
	running_result = system.tag.readBlocking([production_running_path])[0]
	is_running = running_result.value == True

	# If WorkOrderId is null/empty - just stop production
	if work_order_id is None or str(work_order_id).strip() == '':
		if is_running:
			system.tag.writeBlocking([production_running_path], [False])
			logger.info('Production stopped - work order cleared')
		return

	# Cycle production: Stop current -> Start new
	if is_running:
		# Stop current run first
		system.tag.writeBlocking([production_running_path], [False])
		logger.info('Production ended for work order change')

	# Start new run (Production/Running script handles the actual DB logging)
	system.tag.writeBlocking([production_running_path], [True])
	logger.info('Production started for work order: {}'.format(work_order_id))

except Exception as e:
	logger.error('Error in Edge/WorkOrderId valueChanged: {}'.format(e))
```

**Edge Cases:**

| Scenario | Behavior |
|----------|----------|
| WO changes, not running | Start new production |
| WO changes, already running | End current → Start new |
| WO cleared (null/empty) | End current, don't start |
| WO same value (no change) | Skip (no action) |
| Product/ProductId not set | Production/Running script will reject start |

---

## 13. Production/Running - valueChanged Script

**Apply to:** `Production/Running`

**Reads from sibling UDTs:**
- `Definition/Id` - asset_id
- `Product/ProductId` - product_id

**Writes to sibling Production tags:**
- `LogId` - production_log_id returned from DB
- `StartTimestamp` - `system.date.now()` (gateway local time, like State UDT)
- `EndTimestamp` - `system.date.now()` (gateway local time, like State UDT)
- `TotalCount` - reset to 0 on start

**Expression tag (not written by script):**
- `DurationSeconds` - Expression: `if(isNull({[.]StartTimestamp}), 0.0, if(isNull({[.]EndTimestamp}), dateDiff({[.]StartTimestamp}, now(1000), "sec"), dateDiff({[.]StartTimestamp}, {[.]EndTimestamp}, "sec")))`

```python
# Production/Running - valueChanged Script
# Uses: mes.production.startRun(), mes.production.endRunForAsset()
# Rising edge (False -> True): Starts production run
# Falling edge (True -> False): Ends production run
# NOTE: Do NOT wrap in def valueChanged() - Ignition provides parameters automatically

# Helper function to clear production-specific fields only
# Note: DurationSeconds is an expression tag, not included here
def clearProductionFields(parent_path):
	tag_writes = [
		(parent_path + '/LogId', 0),
		(parent_path + '/StartTimestamp', None),
		(parent_path + '/EndTimestamp', None),
		(parent_path + '/TotalCount', 0.0)
	]
	paths = [t[0] for t in tag_writes]
	values = [t[1] for t in tag_writes]
	system.tag.writeBlocking(paths, values)

try:
	last_value = previousValue.value
	tag_value = currentValue.value
	tag_quality = str(currentValue.quality)

	# Create the logger using tag path for contextual logging
	logger_name = gateway.logger.tag_path_to_logger(tagPath)
	logger = gateway.logger.create_logger(logger_name)

	# Check if the tag has good quality
	if tag_quality == 'Good':

		# Check if the tag has actually changed
		if last_value != tag_value:

				# Get the parent path (Production folder) for writing sibling tags
				parent_path = '/'.join(tagPath.split('/')[:-1])

				# Get the equipment path (WorkUnit/WorkCenter) for accessing Definition and Product
				equipment_path = '/'.join(tagPath.split('/')[:-2])

				try:
					from mes import production as mes_production
					from mes.errors import MesConflictError, MesNotFoundError

					# Get asset_id from Definition sibling UDT
					asset_id_path = equipment_path + '/Definition/Id'
					asset_id_result = system.tag.readBlocking([asset_id_path])
					asset_id = asset_id_result[0].value if asset_id_result else None

					if asset_id is None or asset_id <= 0:
						logger.error("Cannot manage production - Definition.Id is not set at {}".format(asset_id_path))
						return

					if tag_value:  # Rising edge: Start production
						# Get product_id from sibling Product UDT
						product_id_path = equipment_path + '/Product/ProductId'
						product_id_result = system.tag.readBlocking([product_id_path])
						product_id = product_id_result[0].value if product_id_result else None

						if product_id is None or product_id <= 0:
							logger.error("Cannot start production - Product.ProductId is not set at {}".format(product_id_path))
							# Reset Running to False since we can't start
							system.tag.writeBlocking([tagPath], [False])
							return

						try:
							# Start production run using domain function
							result = mes_production.startRun(
								asset=asset_id,
								product=product_id
							)

							# Write production-specific fields only (product info is in sibling Product UDT)
							# Use system.date.now() for timestamps to match gateway timezone (like State UDT)
							tag_writes = [
								(parent_path + '/LogId', result.get('production_log_id', 0)),
								(parent_path + '/StartTimestamp', system.date.now()),
								(parent_path + '/EndTimestamp', None),
								(parent_path + '/TotalCount', 0.0)
							]
							paths = [t[0] for t in tag_writes]
							values = [t[1] for t in tag_writes]
							system.tag.writeBlocking(paths, values)

							logger.info("Production started: LogId={}, AssetId={}, ProductId={}".format(
								result.get('production_log_id'), asset_id, product_id))

						except MesConflictError as conflict:
							# Already an active run - reset Running to False
							logger.warn("Cannot start production - {}".format(conflict))
							system.tag.writeBlocking([tagPath], [False])

					else:  # Falling edge: End production
						try:
							# End production run using domain function
							result = mes_production.endRunForAsset(asset=asset_id)

							if result is not None:
								# Use system.date.now() for timestamps to match gateway timezone (like State UDT)
								system.tag.writeBlocking([parent_path + '/EndTimestamp'], [system.date.now()])
								logger.info("Production ended: LogId={}, AssetId={}".format(
									result.get('production_log_id'), asset_id))
							else:
								# No active run to end - reset state to allow fresh start
								clearProductionFields(parent_path)
								logger.info("No active production run to end for asset {} - state reset".format(asset_id))

						except (MesNotFoundError, MesConflictError) as e:
							# Run doesn't exist or already ended - reset state gracefully
							clearProductionFields(parent_path)
							logger.info("Production end handled gracefully: {} - state reset".format(e))

				except Exception as domainError:
					# Domain function failed - reset state on falling edge only
					if not tag_value:  # Falling edge (ending) - reset to prevent lock-up
						try:
							clearProductionFields(parent_path)
						except:
							pass  # Best effort reset
					logger.error("Production operation failed: {} - state reset attempted".format(domainError))

	except Exception as e:
		# Log an error message if an exception occurs
		logger.error("An error occurred in Production Running valueChanged: {}".format(e))
```
