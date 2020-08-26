FIRST STEPS

1- COPY THE FOLDERS IN A CONVENIENT PLACE ON YOUR SYSTEM
2- LOCATE THE rdt.conf FILE
3- EDIT THE rdt.conf FILE WITH THE PATHS TO YOUR IN AND OUT DIRS
4- CHANGE TO .../RDT DIR AND EXECUTE python3 nwcpy_rdt_to_geoJSON1.0.py -h
5- TO TEST IF YOU NEED SOMETHING MORE IN YOUR PLATFORM, IN .../RDT DIR EXECUTE python3 nwcpy_rdt_to_geoJSON.py -d (SEE THE ERRORS)
6- WHEN FINALLY IT WORKS DOUBLE CLICK debug.html TO SEE HOW IT LOOKS LIKE ON LEAFLET, CLICK ON THE POLYGONS TO CHECK.
7- IF OK CHANGE rdt.conf TO ADAGUC PLATFORM..........

WARMINGS:

The rdt.conf file needs to be placed on or under the working directory
You need python3 with the modules netCDF4, cv2 (if it is not installed, please install with: install pip3 install opencv-python), numpy, datetime, time, os, sys,
geographiclib, pandas, geopandas, shapely 

FULL SUPPORT ADAGUC and LEAFLET in versions <2
Version 2.0 only supports ADAGUC, v2 support for LEAFLET TBD

# *************************************************************************/
# **
# * \file nwcpy_rdt_to_geoJSON1.0.py
# *
# *\geoJSON encoder for the NWC/GEO RDT product
# *
# * \par Copyright 2018, EUMETSAT, All Rights Reserved
# *
# * \par PRODUCED BY :  AEMET.
# *                     This SW was developed by AEMET within the
# *                     context of the EUMETSAT Satellite Application
# *                     Facility Co-operation Agreement for Support to
# *                     Nowcasting and Very Short Range Forecasting,
# *                     dated 7 December 2016 between EUMETSAT
# *                     and AEMET.
# *
# * \par PROJECT     :  NWC SAF
# *
# * \par UNIT NAME   :  NWCPY
# *
# * \par FILE        :  nwcpy_rdt_to_geoJSON.py
# *
# * \par TYPE        :  source
# *
# * \par FUNCTION    :
#
#
# Usage example: python nwcpy_rdt_to_geoJSON1.1.py <options>
#
# This script plots thunderstorm contours from a RDT product in nc format (until 5 files).
# The sets of files have to be copied in inDir, then execute the script with or without
# options. The final file is named <file>.geoJSON and stored in the outDir.
# If the script is executed with the option -d, sample files will be processed
# they are stored in ./debug_data and the output will be stored  in ./debug_geoJSON
#
#
# CONFIGURATION ADJUSTABLE IN rdt.conf FILE
#
# Execution examples:
#
# execute:      python3 nwcpy_rdt_to_geoJSON2.0.py -d   for debug mode, it uses the provided nc example files
#
# execute:      python3 nwcpy_rdt_to_geoJSON2.0.py  without any argument for live mode
#
# In live mode the script will scan inDIr directory and produce geoJSON output in the outDir.
# THE CONFIGURATION IS AVAILABLE IN rdt.conf FILE, PLACE IT ON OR UNDER THE WORKING DIRECTORY
#
# **************************************************************************/
# * HISTORY
# *
# *  DATE      	    VERSION   AUTHOR     REASONS
# * December 2018    alpha    AEMET      Alpha version
# * January 2019     beta     AEMET      script run options added
# * February 2019    1        AEMET      Management of the configuration improved
# * March 2019       1.1      AEMET      Forecasted trajectories correctly displayed,
# *                                      Only significant cells kept, OT plotting routine
# *                                      fixed.
# * March 2019       2.0      AEMET      Time performance increased. New paradigm based
# *                                      on geopandas
# ****************************************************************************/


