import arcpy as ap

#Will take a record from existing table and put it in a new table with a new field for
#the full address of the record.
#0.33174596696233377ms of 100 trials
def transferRecordToStandaloneTable(TBL_NAME, id):
    #Create temp table
    TEMP_TBL_NAME = "tempTable"
    ap.CreateTable_management(ap.env.workspace, TEMP_TBL_NAME, TBL_NAME)
    #Copy record from original table to temp table and add full address field
    searchCursor = ap.SearchCursor(TBL_NAME, f"OBJECTID = {id}")    
    originalRow = searchCursor.next()
    fullAddress = originalRow.getValue("Address1") + ", " + originalRow.getValue("City")
    insertCursor = ap.InsertCursor(TEMP_TBL_NAME)
    insertCursor.insertRow(originalRow)
    del insertCursor
    del searchCursor
    ap.AddField_management(TEMP_TBL_NAME, "Address", "TEXT") #will contain the full address
    updateCursor = ap.UpdateCursor(TEMP_TBL_NAME)
    row = updateCursor.next()
    row.setValue("Address", fullAddress)
    updateCursor.updateRow(row)
    del updateCursor
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
    #ap.AddXY_management(FEATURESET_NAME)
    #Going to add the new point to a hard-coded feature set for now
    searchCursor = ap.SearchCursor(FEATURESET_NAME)
    row = searchCursor.next()
    serialNo = row.getValue("USER_SerialNo")
    shape = row.getValue("SHAPE")
    #x, y = row.getValue("DisplayX"), row.getValue("DisplayY")
    #spatialRef = row.getValue("SHAPE").spatialReference
    #pointLocation = ap.Point(x,y)
    #pointGeo = ap.PointGeometry(pointLocation)
    #pointGeo = pointGeo.projectAs(spatialRef)
    del searchCursor
    del row
    #Copy the record into feature class
    pathToFC = ap.Describe("License").catalogPath
    ap.Append_management(TEMP_TBL_NAME, pathToFC, "NO_TEST") #NO_TEST is loose schema enforcement; will drop non-matching fields from input
    updateCursor = ap.UpdateCursor("License", f"SERIALNO = '{serialNo}'")
    row = updateCursor.next()
    row.setValue("SHAPE", shape)
    updateCursor.updateRow(row)
    ap.Delete_management(ap.Describe(TEMP_TBL_NAME).catalogPath)
    ap.Delete_management(ap.Describe(FEATURESET_NAME).catalogPath)
