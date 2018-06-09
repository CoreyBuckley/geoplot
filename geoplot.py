import arcpy as ap

# Returns dict(fields,values) for a row
def extractValues(TBL_NAME, id):
    fields = ap.ListFields(TBL_NAME)
    fields = [x.name for x in fields]
    values = []
    rows = ap.SearchCursor(TBL_NAME, f"OBJECTID = {id}")
    row = rows.next()
    for i in range(len(fields)):
        values.append(row.getValue(fields[i]))
    fieldMapping = dict(zip(fields, values))
    return fieldMapping

#Will take a record from existing table and put it in a new table with a new field for
#the full address of the record.
def transferRecordToStandaloneTable(TBL_NAME, id):
    fieldMapping = extractValues(TBL_NAME, id)
    fields = list(fieldMapping.keys())
    values = list(fieldMapping.values())
    TEMP_TBL_NAME = "tempTable"
    ap.CreateTable_management("in_memory", TEMP_TBL_NAME, TBL_NAME)
    ap.AddField_management(TEMP_TBL_NAME, "Address", "TEXT") #will contain the full address
    insertCursor = ap.InsertCursor(TEMP_TBL_NAME)
    newRow = insertCursor.newRow()
    for i in range(fields.index("Name"), len(fields)): #Don't need objectid or shape, so go to name onward
    	newRow.setValue(fields[i], values[i])
    searchCursor = ap.SearchCursor(TBL_NAME, f"OBJECTID = {id}")
    record = searchCursor.next()
    fullAddress = record.getValue("Address1") + ", " + record.getValue("City")
    newRow.setValue("Address", fullAddress)
    insertCursor.insertRow(newRow)
    del insertCursor
    del searchCursor
    return TEMP_TBL_NAME

def geocode(TBL_NAME, id):
	TEMP_TBL_NAME = transferRecordToStandaloneTable(TBL_NAME, id)
	FEATURESET_NAME = TBL_NAME + "Geocode"
	ap.GeocodeAddresses_geocoding(TEMP_TBL_NAME, 
								  'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer', 
								  'Address Address', 
								   FEATURESET_NAME, 
								  'STATIC', 
								  'US', 
								  'ADDRESS_LOCATION')
	ap.AddXY_management(FEATURESET_NAME)
	#Going to add the new point to a hard-coded feature set for now
	searchCursor = ap.SearchCursor(FEATURESET_NAME)
	row = searchCursor.next()
	x, y = row.getValue("POINT_X", "POINT_Y")
	pointLocation = ap.Point(x,y)
