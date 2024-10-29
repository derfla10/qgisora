import sys
import cx_Oracle
from qgis.PyQt import QtGui
from qgis.utils import iface
########################################################
myhost     = "localhost"
mydb       = "oracledb"
myport     = "1520"
myusername = "QGISUSER"
mypassword = "password"
displaymsg = False 
########################################################
myconnectdb = myusername+"/"+mypassword+"@"+myhost+":"+myport+"/"+mydb
oraconn = cx_Oracle.connect(myconnectdb)
iface.messageBar().pushMessage("Database", "Succesfully connected to "+myusername+" at "+mydb, level=Qgis.Info)
print (oraconn)
timeselect = False
qlist    = []
qid       = QInputDialog()
qmode    = QLineEdit.Normal
qdefault = mytable_name
qtitle   = "Spatial Table to display"
qlabel   = "Spatial Table Name"
sql = "SELECT distinct table_name, owner from all_sdo_geom_metadata where owner != user UNION select table_name, owner from all_tables where table_name like 'GRID_%DD_%' order by 2,1"
stablelist = oraconn.cursor()
stablelist.execute(sql)
stablelistrow = stablelist.fetchall()
for stable in stablelistrow:
	qlist.append(stable[0])
qtext, qok = QInputDialog.getItem(qid, qtitle, qlabel,qlist)

if (qok):
	mytable_name = qtext
	sql = "SELECT owner FROM all_sdo_geom_metadata where table_name = '"+mytable_name+"' UNION select owner from all_tables where table_name = '"+mytable_name+"'"
	getowner = oraconn.cursor()
	getowner.execute(sql)
	getownerrow = getowner.fetchone()
	myowner = getownerrow[0]

if (("GRID_" in mytable_name) and ("DD" in mytable_name) and (len(mytable_name) > 11)):
	myspatial_table_name = mytable_name.split('DD_')[0] + "DD"
	sqlconstraint = "SELECT column_name FROM all_constraints c, all_ind_columns i WHERE c.constraint_name = i.index_name AND c.constraint_type = 'P' AND c.owner = i.table_owner AND c.table_name = UPPER('"+mytable_name+"') order by column_position asc"
	if displaymsg:
		print(sqlconstraint)
	constraint_return = oraconn.cursor()
	constraint_return.execute(sqlconstraint)
	constraint_row = constraint_return.fetchall()
	myrel_column_name = "0"
	myyear_col = "0"
	for rel in constraint_row:
		if (rel[0] == "YEAR"):
			timeselect = True
			myyear_col = rel[0]
		else:
			myrel_column_name = rel[0]
	if displaymsg:
		print("Found relation column with "+myrel_column_name)
	sql = "SELECT distinct '"+myowner+"' || ' ' || initcap(replace('"+mytable_name+"','_',' ')) layer_name, 'POLYGON' , to_char(srid) srid, column_name  FROM all_sdo_geom_metadata WHERE owner = 'GRIDREF' and table_name = UPPER('"+myspatial_table_name+"') order by column_name desc"
	if (myyear_col == "YEAR"):
		spatialsql = "SELECT id, corr_cell, f.* from gridref."+myspatial_table_name+", " + myowner + "." + mytable_name + " f where id = f."+myrel_column_name+" and f.year = to_char(sysdate -30,'YYYY')"
	else:
		spatialsql = "SELECT id, corr_cell, f.* from gridref."+myspatial_table_name+", " + myowner + "." + mytable_name + " f where id = f."+myrel_column_name
else:
	sql = "SELECT owner || ' ' || initcap(replace(table_name,'_',' ')) layer_name, decode(column_name,'POLYGONS','POLYGON','CELL','POLYGON','CORR_CELL','POLYGON','CELLS','POLYGON','BLOCKY_POLYGON','POLYGON','LINES','POLYLINE','SHAPE','POLYGON','DIRECTEDLINE','POLYLINE','LINE','POLYLINE','LINE_SIMPLE','POLYLINE','GEOMETRY','POLYGON',column_name) geometry_type, to_char(srid) srid, COLUMN_NAME FROM all_sdo_geom_metadata WHERE owner = UPPER('" + myowner + "') and table_name = UPPER('" + mytable_name + "') order by COLUMN_NAME"
	spatialsql =  "SELECT * FROM " + myowner + "." + mytable_name
	myspatial_table_name = mytable_name

query_return = oraconn.cursor()
query_return.execute(sql)
query_returnrow = query_return.fetchall()
if not (query_returnrow):
	iface.messageBar().pushMessage("Query failed", sql, level=Qgis.Warning)
else:
	iface.messageBar().pushMessage("Query successful", str(query_returnrow[0]), level=Qgis.Success)
sql = "SELECT decode(c.table_name,'COUNTRIES','geo_sort',column_name) column_name FROM all_constraints c, all_ind_columns i WHERE c.constraint_name = i.index_name AND c.constraint_type = 'P' AND c.owner = i.table_owner AND c.table_name = i.table_name AND c.table_name = '"+ myspatial_table_name + "'"
if displaymsg:
	print (sql)
print("Unique Identifier Test...")
query_identifier = oraconn.cursor()
query_identifier.execute(sql)
query_identifierrow = query_identifier.fetchall()
if (query_identifierrow == "" ):
	iface.messageBar().pushMessage("No Unique Identifier", "Table not suited for displaying in QGIS", level=Qgis.Warning)
else:
	iface.messageBar().pushMessage("Unique Identifier", query_identifierrow[0][0] + " found for "+mytable_name, level=Qgis.Success)
	uri = QgsDataSourceUri()
	uri.setConnection(myhost, myport, mydb, myusername, mypassword)
	print(query_identifierrow[0][0])
	print(query_returnrow[0][3])
	print(query_returnrow[0][1])
	if (timeselect):
		print("In time select...")
		uri.setDataSource(myusername, mytable_name+"_ACTUAL", query_returnrow[0][3],"",query_identifierrow[0][0])
	elif(mytable_name == "GRID_025DD_LANDCOVER"):
		uri.setDataSource(myusername, mytable_name, query_returnrow[0][3],"",query_identifierrow[0][0])
	else:
		uri.setDataSource(myowner, mytable_name, query_returnrow[0][3],"",query_identifierrow[0][0])
#	uri.setDataSource(myschema, mytable,mycolumn,"",myprim_key)
	uri.setSrid(query_returnrow[0][2])
	if (query_returnrow[0][1] == "POLYGON"):
		uri.setWkbType(3)
	elif (query_returnrow[0][1] == "POLYLINE"):
		uri.setWkbType(2)
	else:
		uri.setWkbType(1)
	mydblayer = QgsVectorLayer(uri.uri(), query_returnrow[0][0], "oracle")
	print("Spatial Table: "+query_returnrow[0][0])
	print("   Identifier: "+query_identifierrow[0][0])
	if not mydblayer.isValid():
		iface.messageBar().pushMessage(mytable_name, "Problem with making layer", level=Qgis.Warning)
	else:
		iface.messageBar().pushMessage(mydblayer.name(), "Determining classification", level=Qgis.Info)
		if (timeselect):
			sql = "SELECT COUNT(*) FROM all_tab_columns where owner = '"+myowner+"' and table_name = '"+mytable_name+"'" 
			print(sql)
			totcur = oraconn.cursor()
			totcur.execute(sql)
			totcurrow = totcur.fetchone()
			if (totcurrow[0] > 366):
				daysback = "6"
			elif (totcurrow[0] > 36) and (mytable_name != "GRID_1DD_SPI"):
				daysback = "16"
			elif (totcurrow[0] > 12):
				daysback = "36"
			else:
				daysback = "90"
			# note query can also have a \_ in the like
			print("Defaulting to "+daysback+ " day back from today")
			sql = "SELECT max(column_name) from all_tab_columns where owner = '"+myowner+"' and table_name = '"+mytable_name+"' and (column_name like '%N' || '_' || to_char(sysdate - "+daysback+",'MM') or column_name like '%' || to_char(sysdate - "+daysback+",'MM') || case when to_char(sysdate - "+daysback+",'DD') < 10 then '21' when to_char(sysdate - "+daysback+",'DD') < 20 then '01' else '11' end or column_name like '%' || to_char(sysdate - "+daysback+",'MMDD') or column_name like 'SPI_' || to_char(sysdate - "+daysback+",'MM') || '%') order by column_name "+ascending
			if displaymsg:
				print(sql)
			fieldcur = oraconn.cursor()
			fieldcur.execute(sql)
			fieldcurrow = fieldcur.fetchall()
			sql = "SELECT min("+fieldcurrow[0][0]+"),max("+fieldcurrow[0][0]+") from "+myowner+"."+mytable_name+" WHERE year = to_number(to_char(sysdate - "+daysback+",'YYYY'))"
			if displaymsg:
				print(sql)
			minmaxcur = oraconn.cursor()
			minmaxcur.execute(sql)
			minmaxcurrow = minmaxcur.fetchall()
			if displaymsg:
				print(minmaxcurrow)
			testresult = ""
			myrangelist = []
			if (minmaxcurrow[0][1] == None):
				print("No data found for "+fieldcurrow[0][0])
			else:
				mystep = round((minmaxcurrow[0][1] - minmaxcurrow[0][0]) / 7)
				testlist = ["TEMP","RAIN","SPI","ANOMALY","ABSORBED"]
				test = fieldcurrow[0][0]
				for teststring in range(0,len(test) - 1):
					for testcol in testlist:
						if (test[teststring] == testcol[0]):
							starttest = teststring
							if (test[starttest:(starttest+len(testcol))] == testcol):
								print(testcol + " column detected for "+ test)
								testresult = testcol
								break
				mymin  = minmaxcurrow[0][0]
				mymax  = minmaxcurrow[0][1]
				mytype = testresult
				myiterations = 7
				mystep = round((mymax - mymin) / myiterations)
				print ("Legend steps: "+str(mystep))
				myred     = 0
				mygreen   = 0
				myblue    = 0
				mycounter = 0
				mycolor   = 0
				localmax  = 0
				if (mytype == "RAIN" or mytype == "TEMP" or mytype == "ABSORBED"):
					if (mytype == "RAIN"):
						correctfirstclass = 1
					else:
						correctfirstclass = 0
					for myiter in range(int(mymin),int(mymax),mystep):
						localmin = myiter
						if (correctfirstclass == 1):
							localmax = localmin + 0.01
							correctfirstclass = 0
						elif (localmax < localmin):
							localmin = localmax
							localmax = localmin + mystep + 0.01
						else:
							localmax = myiter + mystep - 0.01
						if (localmax > mymax):
							localmax = mymax
						mylabel = (str(localmin)+ " -- "+str(localmax))
						mycounter = mycounter + 1
						mycolor = round((255 / myiterations) * mycounter)
						if (mycolor > 255):
							mycolor = 255
						if (mytype == "RAIN"):
							myred   = round((255 - mycolor) / 1)
							mygreen = round((255 - mycolor) / 1)
							myblue  = 255
						elif (mytype == "TEMP"):
							myred = 255
							mygreen = round((255 - mycolor) / 1)
							myblue  = round((255 - mycolor) / 2)
						elif (mytype == "ABSORBED"):
							myred   = round((255 - mycolor) / 1)
							mygreen = 255
							myblue  = round((255 - mycolor) / 1)
						mylabel  = str(localmin) + "--"+ str(localmax)
						mycolor  = QtGui.QColor()
						mycolor.setBlue(myblue)
						mycolor.setGreen(mygreen)
						mycolor.setRed(myred)
						mysymbol = QgsSymbol.defaultSymbol(mydblayer.geometryType())
						mysymbol.setColor(mycolor)
						mysymbol.symbolLayer(0).setStrokeColor(mycolor)
						myrange  = QgsRendererRange(localmin,localmax,mysymbol,mylabel)
						myrangelist.append(myrange)
				elif (mytype == "SPI" or mytype == "ANOMALY"):	
					for myiter in range(-5,5,1):
						localmin = myiter / 2
						if (localmin == -2.5):
							localmin = mymin
						localmax = (myiter / 2 ) + 0.5
						if (localmax > -0.5 and localmax <= 1):
							print("Skip: " + str(myiter))
						else:
							if (localmax == -0.5):
								localmax = 1
							elif (localmax == 2.5):
								localmax = mymax
							mylabel = (str(localmin)+ " -- "+str(localmax))
							print(mylabel)
							if (localmax == -2):
								myred = 255
								mygreen = 0
								myblue = 0
							elif(localmax == -1.5):
								myred = 255
								mygreen = 127
								myblue = 39
							elif(localmax == -1):
								myred = 255
								mygreen = 255
								myblue = 0
							elif (localmax == 1):
								myred = 255
								mygreen = 255
								myblue = 255
							elif (localmax == 1.5):
								myred = 255
								mygreen = 0
								myblue = 255
							elif (localmax == 2):
								myred = 128
								mygreen = 0
								myblue = 255
							else:
								myred = 128
								mygreen = 0
								myblue = 128
							mylabel  = str(localmin) + "--"+ str(localmax)
							mycolor  = QtGui.QColor()
							mycolor.setBlue(myblue)
							mycolor.setGreen(mygreen)
							mycolor.setRed(myred)
							mysymbol = QgsSymbol.defaultSymbol(mydblayer.geometryType())
							mysymbol.setColor(mycolor)
							mysymbol.symbolLayer(0).setStrokeColor(mycolor)
							myrange  = QgsRendererRange(localmin,localmax,mysymbol,mylabel)
							myrangelist.append(myrange)
			if (len(myrangelist) > 0):
				myrenderer = QgsGraduatedSymbolRenderer('',myrangelist)
				myclassificationmethod = QgsApplication.classificationMethodRegistry().method("EqualInterval")
				myrenderer.setClassificationMethod(myclassificationmethod)
				myrenderer.setClassAttribute(fieldcurrow[0][0])
				mydblayer.setRenderer(myrenderer)
		else:
			sql = "SELECT  a.column_name , c.owner, c.table_name FROM all_cons_columns a ,all_constraints  b ,all_constraints c WHERE  b.constraint_name = a.constraint_name AND a.table_name = UPPER('"+mytable_name+"') AND  b.table_name = a.table_name  AND  b.owner = a.owner AND  b.constraint_type = 'R' AND c.constraint_name = b.r_constraint_name AND c.table_name IN (SELECT table_name FROM all_tab_columns WHERE column_name = 'RED') order by 1 desc"
			if displaymsg:
				print(sql)
			classcur = oraconn.cursor()
			classcur.execute(sql)
			classcurrow = classcur.fetchall()
			if (len(classcurrow) > 0):
				sql = "SELECT id, nvl(description,id), red, green ,blue from "+classcurrow[0][1] +"."+classcurrow[0][2]+ " where red is not null ORDER BY 1 asc"
				myclass_renderer = QgsCategorizedSymbolRenderer()
				classcolor = oraconn.cursor()
				classcolor.execute(sql)
				classcolorrow = classcolor.fetchall()
				for classrec in classcolorrow:
					mycolor    = QtGui.QColor()
					mycolor.setRed(classrec[2])
					mycolor.setGreen(classrec[3])
					mycolor.setBlue(classrec[4])
					mysymbol   = QgsSymbol.defaultSymbol(mydblayer.geometryType())
					mysymbol.setColor(mycolor)
					mycategory = QgsRendererCategory(classrec[0], mysymbol, classrec[1])
					mysymbol.symbolLayer(0).setStrokeColor(mycolor)
					myclass_renderer.addCategory(mycategory)
				myclass_renderer.setClassAttribute(classcurrow[0][0])
				mydblayer.setRenderer(myclass_renderer)
			else:
				print("No classification found")
		mymeta = mydblayer.metadata()
		mymeta.setTitle(query_returnrow[0][0])
		mymeta.setIdentifier(mytable_name)
		mymeta.setParentIdentifier("https://drought.emergency.copernicus.eu")
		mymetacontacts = mymeta.contacts
		mymeta.setType(query_returnrow[0][1])
		mymeta.setLanguage("English")
		sql = "SELECT comments FROM all_tab_comments where owner = '"+myowner+"' AND table_name = '"+mytable_name+"'"
		mymetasql = oraconn.cursor()
		mymetasql.execute(sql)
		mymetasqlrow = mymetasql.fetchone()
		if (len(mymetasqlrow) > 0):
			mymeta.setAbstract(mymetasqlrow[0])
		mydblayer.setMetadata(mymeta)
		iface.messageBar().pushMessage(mydblayer.name(), "Added successful to the Table of Contents", level=Qgis.Success)
		QgsProject.instance().addMapLayer(mydblayer)
		iface.mainWindow().setWindowTitle("Drought QGIS")
