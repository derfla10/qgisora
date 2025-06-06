# qgisora
Display Oracle Spatial data in QGIS using a datamodel allowing to store classifications and timeseries

<br>The application presumes that the library oracledb can be loaded.

<br>The application assumes some rules on the naming of tables and columns as well as the structure of color lookup tables and timeseries

<h3>Spatial Table naming convention</h3>

Every spatial table has a primary key, prefarably a number or a simple string.
The spatial data are stored in columns with as name explicit the geometry type that it helds.
The possible names for spatial columns are:
<ol><li>point</li>
<li>line</li>
<li>directedline</li>
<li>polygon</li>
<li>polygons</li>
<li>cell</li>
<li>corr_cell (an intersection between a cell and the coastline for example)</li>
</ol>

<h3>Classification Table stucture convention</h3>

Classification colors are stored in a table that contain the fields id, description, red, green, blue.
The ID field is primary key field referred to as foreign key in the spatial table helding the data to be classified.
The fields red, green and blue are of number(3). 
The application will reveal the lookup table using the foreign key existence and the field 'red'.

<br>Example:
<br>table welltypes(
 id           number(2) not null primary key
,description  varchar2(60)
,red          number(3) not null
,green        number(3) not null
,blue         number(3) not null)

<br>table wells(
 id           number(10) not null primary key
,welltype_id  number(2)
,point        mdsys.sdo_geometry not null)

<br>alter table wells add constraint foreign key wll_wte_fk welltype_id references welltypes(id)

<h3>Time series convention</h3>

Time series are stored per pixel per year. The time series relates to a spatial table containing grid cell data. The reference grid cell data tables have as name
GRID_xxDD where xx is the resolution, for example GRID_1DD is a 1 decimal degree grid, resulting in 64800 records for the whole planet.
The table related to this with a time series is GRID_1DD_parametername, in which every parameter moment is a column, for example the rain of january would be stored in column rain_01 for January. 

<br>Example:
<br>table GRID_1DD(
 id         number(5) not null primary key
,cell       mdsys.sdo_geometry not null
,corr_cell  mdsys.sdo_geometry)   # empty if ocean for example

<br>table GRID_1DD_MONTHLY_RAIN(
 g1d_id     number(5) not null
,year       number(4) not null
,rain_01    number
,rain_02    number
,rain_03    number
,rain_04    number
..
,rain_12    number)

<br>primary key on g1d_id and year
<br>foreign key of g1d_id refering to grid_1dd(id)

<br>Make sure to store the data in another schema than the user in QGIS is using to consult the data (by giving select grants)
In this QGIS selection schema Views are used, with the same name appended with '_ACTUAL' with a join to visualize the timeseries using the referred geometry.

<br>create or replace view GRID_1DD_MONTHLY_RAIN_ACTUAL as
SELECT id, corr_cell, r.*
  FROM schema_name.grid_1dd, schema_name.grid_1dd_monthly_rain r
 WHERE id     = r.g1d_id
   AND r.year = to_number(to_char(sysdate - 33),'YYYY')

<br>QGIS requires an entry in the USER_SDO_GEOM_METADATA system table in order to visualize this view.
You can create this record as QGIS selection user:

<br>insert into user_sdo_geom_metadata select 'GRID_1DD_MONTHLY_RAIN_ACTUAL',column_name, diminfo, srid
     from    all_sdo_geom_metadata where table_name = 'GRID_1DD' and column_name = 'CORR_CELL';

<br>The application will default for visualizing data to a selected column, and classify the minimum and maximum accordingly. 
  <ol><li> to minus <b>six</b> days from system date for daily data (convention MMDD)</li>
  <li>to minus <b>thirtysix</b> days from system date for monthly data (convention MM)</li>
  <li>to minus <b>sixteen</b> days from system date for 10 daily data (convention MMTT where TT is 01,11,21)</li> </ol>
This implies that the system expects data to be integrated with a maximum of six days delay. 
If data are missing then the application will search back to a maximum of a year.

<br>If a column contains the word 'RAIN' a graduated color scheme based on blue will be generated. The class for zero rainfall will be a separate class.
<br>If a column contains the word 'TEMP' a graduated color schema based on red will be generated.
<br>If a column contains the word 'ABSORBED' a graduated color schema based on green will be generated.
<br>If a column contains the word 'SPI' or 'ANOMALY' a fixed statistical color scheme will be generated from -2 and lower to +2 and higher.

<br>Note that Table and Column names should not be quoted or use other characters than the 26 base latin characters and/or numbers 0 to 10.
