
The important thing here is that you need a PRIMARY or UNIQUE KEY on any column that you want indexed and especially if you want to use AUTO_INCREMENT.

Based on sample code behavior where 'id' is not explicitly handled by the code, we need AUTO_INCREMENT on the 'id' column so that the DB will manage its uniqueness.  However, to me the 'rfid_tag' column makes more sense as the PRIMARY KEY, since the sample code is constantly querying against that column.
