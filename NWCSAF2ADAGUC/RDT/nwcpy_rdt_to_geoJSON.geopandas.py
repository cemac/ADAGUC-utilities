# -*- coding: utf-8 -*-
# *************************************************************************/
# Copyright 2019-2020, ADAGUC-utilities contributors
# This file is part of ADAGUC-utilities.
#
#     ADAGUC-utilities is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Lesser General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     ADAGUC-utilities is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Lesser General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with ADAGUC-utitlities.  If not, see <https://www.gnu.org/licenses/>.
# ****************************************************************************/


import netCDF4
from datetime import datetime, timedelta
from geographiclib.geodesic import Geodesic
import sys
import os
import cv2
import numpy as np
import time
import pandas as pd
import geopandas
import json
from shapely.geometry import Polygon, LineString
sys.path.append('..')
from facilities import services as srv


def update_legend(text, conf):
    '''
    :param text: string to put in the legend
    :param conf: configuration dictionary
    :return: nothing
    writes the time in the draft_legend png file, writes a new file with the time stamp.
    '''
    in_legend_image = conf['LEGEND']['inDir'] + "/legend_RDT_draft.png"
    img_BGRA = cv2.imread(in_legend_image)

    font = cv2.FONT_HERSHEY_DUPLEX
    bottomLeftCornerOfText = (int(img_BGRA.shape[1] / 2), 100)
    fontScale = 1
    fontColor = (0, 0, 0, 255)
    lineType = 2

    cv2.putText(img_BGRA, text,
                bottomLeftCornerOfText,
                font,
                fontScale,
                fontColor,
                lineType)
    # adding transparency

    b_channel, g_channel, r_channel = cv2.split(img_BGRA)

    alpha_channel = np.ones(b_channel.shape, dtype=b_channel.dtype) * 255  # creating a dummy alpha channel image.

    # now adding transparencies in the white areas
    thereshold = 220
    white = np.where((b_channel > thereshold) & (g_channel > thereshold) & (r_channel > thereshold))
    alpha_channel[white] = 0

    final_legend = cv2.merge((b_channel, g_channel, r_channel, alpha_channel))

    out_legend = conf['LEGEND']['inDir'] + "/legend_RDT.png"
    cv2.imwrite(out_legend, final_legend)

    return


def features(feature_collection):
    '''
    :param feature_collection: encoded feature collection
    :return: the features without the header
    '''

    features = feature_collection[43:-2]

    return features


def plotTraj(dataSet, conf):
    '''
    Encodes the measured gravity center trajectory and the
    forecasted trajectories as geoJSON features
    :param dataSet: the dataset to be procesed
    :return: encoded features as geoJSON text
    '''
    geod = Geodesic.WGS84
    conv_type = dataSet.variables['ConvType'][:]
    cells_to_keep = np.where((conv_type > 0) & (conv_type < 8))[0]
    numb_cells_to_keep = len(cells_to_keep)
    dict = {}

    dict["ObjectType"] = ["PastCGTraj", "FcstCGTraj"] * numb_cells_to_keep
    dict['coordinates'] = []

    lons_matrix = dataSet.variables['LonTrajCellCG'][:]
    lats_matrix = dataSet.variables['LatTrajCellCG'][:]

    for i in range(numb_cells_to_keep):

        cell_lons = lons_matrix[i][lons_matrix[i] > -180]
        cell_lats = lats_matrix[i][lats_matrix[i] > -180]
        coord = tuple(zip(cell_lons, cell_lats))
        if len(coord) == 1:
            coord = coord + coord
        yellow_line = LineString(coord)
        dict['coordinates'].append(yellow_line)

        lat1 = dataSet.variables['LatG'][i][0]
        lon1 = dataSet.variables['LonG'][i][0]
        azi1 = dataSet.variables['MvtDirection'][i]
        s12 = dataSet.variables['MvtSpeed'][i] * 60 * 15

        if not np.ma.is_masked(azi1):
            black_line = geod.Direct(lat1, lon1, azi1, s12)
            dict['coordinates'].append(LineString(((black_line['lon1'], black_line['lat1']), (black_line['lon2'], black_line['lat2']))))
        else:
            #print(lon1, lat1)
            dict['coordinates'].append(LineString(((lon1, lat1), (lon1,lat1))))
    df = pd.DataFrame(dict)

    gdf = geopandas.GeoDataFrame(df, geometry='coordinates')
    # now removing empty geometries
    gdf = gdf[gdf['coordinates'].notnull()]

    text = features(gdf.to_json(na='drop'))

    return text


def plotOT(dataSet, conf):
    '''
    Encodes the overshooting tops
    :param dataSet: the dataset to be procesed
    :param conf: the global configuration
    :return: encoded geoJSON text
    '''
    if 'NumIdCellOT' not in dataSet.variables:
        return ''

    dict = {}
    number_of_points = len(dataSet.variables['LatPixOT'])
    dict["ObjectType"] = []
    configuration = conf['OT']

    for key in configuration:
        dict[key] = []
    dict['coordinates'] = []


    for num in range(number_of_points):
        if not np.ma.is_masked(dataSet.variables['LonPixOT'][num]):
            dict["ObjectType"].append("OT")
            for key in configuration:
                value = dataSet.variables[configuration[key]][num]
                if isinstance(value, np.ma.core.MaskedConstant):
                    dict[key].append(-9999)
                else:
                    dict[key].append(value)

                # writing the coordinates of the OT polygon
                # d is the distance from OT to the triangle vertexes
            d = 0.05
            ot_lon = dataSet.variables['LonPixOT'][num]
            ot_lat = dataSet.variables['LatPixOT'][num]
            #print(ot_lat, ot_lon)
            triangle = tuple(((ot_lon, ot_lat + d), (ot_lon - d, ot_lat - 0.5 * d), (ot_lon + d, ot_lat - 0.5 * d)))

            dict['coordinates'].append(Polygon(triangle))


    df = pd.DataFrame(dict)

    gdf = geopandas.GeoDataFrame(df, geometry='coordinates')
    # now removing empty geometries
    gdf = gdf[gdf['coordinates'].notnull()]

    text = features(gdf.to_json(na='drop'))

    return text


def rdtDataSetToJson(dataSet, conf, DecTime, fct='000'):
    '''
    Encodes a single  dataset to geoJSON
    :param dataSet: the dataset to be procesed
    :param conf: the global configuration
    :param DecTime: an array storing, for each cell, the time gap between nominal and radiometer
    :param fct: range of the dataset, 000: measured, 015, 030 ...value: forecasted
    :return: The encoded cells as geoJSON
    '''

    if fct == '000':
        levels = [0, 1]
    else:
        levels = [0]
    conv_type = dataSet.variables['ConvType'][:]
    cells_to_keep = np.where((conv_type > 0) & (conv_type < 8))[0]
    numb_cells_to_keep = len(cells_to_keep)

    isMainSet = ('CTHicgHzd' in dataSet.variables)

    labelPhaseLife = ({0: 'Triggering', 1: 'Triggering from Split',
                       2: 'Growing', 3: 'Maturity', 4: 'Decaying',
                       255: '--'})

    labelSeverityIntensity = ({0: 'Not defined', 1: 'Low', 2: 'Moderate',
                               3: 'High', 4: 'Very High',
                               255: '--'
                               })

    labelSeverityType = ({0: 'No_activity', 1: 'Turbulence', 2: 'Lightning',
                          3: 'Icing', 4: 'High_altitude_icing', 5: 'Hail',
                          6: 'Heavy_rainfall', 7: 'Not defined',
                          255: '--'})

    labelConvectiveType = ({0: 'Non convective', 1: 'Convective', 2: 'Convective inherited',
                          3: 'Convective forced overshoot', 4: 'Convective forced lightning',
                          5: 'Convective forced convective rain rate',
                          6: 'Convective cold tropical', 7: 'Convective forced inherited',
                          8: 'Declassified convective', 9: 'Not Defined',
                          255: '--'})

    if isMainSet:
        labelCTHicgHzd = ({0: 'Risk Not Defined', 1: 'Low risk', 2: 'Moderate risk',
                          3: 'Hight Risk', 4: 'Very hight Risk', 5: '--',
                          255: '--'})

    cellPhase = [labelPhaseLife[dataSet.variables['PhaseLife'][:].data[cell]] for cell in cells_to_keep]
    cellSeverityIntensity = [labelSeverityIntensity[dataSet.variables['SeverityIntensity'][:].data[cell]] for cell in cells_to_keep ]
    cellSeverityType = [labelSeverityType[dataSet.variables['SeverityType'][:].data[cell]] for cell in cells_to_keep ]
    cellConvectiveType = [labelConvectiveType[dataSet.variables['ConvType'][:].data[cell]] for cell in cells_to_keep]

    objectType = ['cell-' + fct] * numb_cells_to_keep
    tStr = dataSet.getncattr('nominal_product_time').split('_')[0]

    datetime_object = ([datetime.strptime(tStr, '%Y-%m-%dT%H:%M:%SZ')
                       + timedelta(seconds=(60 * int(fct) +
                                            DecTime[cell])) for cell in cells_to_keep])
    times = [(timeobj.time().isoformat() + "Z") for timeobj in datetime_object]

    dict = {}
    dict['time'] = []
    dict["Status"] = []

    if isMainSet:
        dict["HightIcing"] =[]

    dict["severityIntensity"] = []
    dict["severityType"] = []
    dict["level"] = []
    for key in conf['CELL'].keys():
        dict[key] = []
    dict["ObjectType"] = []
    dict["#code"] = []
    dict['coordinates'] = []
    # generating the text corresponding to each feature present in the dataSet

    for level in levels:
        dict['time'] = dict['time'] + times
        dict["Status"] = dict["Status"] + cellPhase

        if isMainSet:
            cellCTHicgHzd = [labelCTHicgHzd[dataSet.variables['CTHicgHzd'][:].data[cell, level]] for cell in cells_to_keep]
            dict["HightIcing"] = dict["HightIcing"] + cellCTHicgHzd
        # adding code for styling the code is #<level><fct><PhaseLife><SeverityIntensity>
        # by example #100021 mean cell in level 1, fct=000, PhaseLife=2 ('Growing') and SeverityIntensity=1 ('Low')
        code = ([(str(level) + fct + str(dataSet.variables['PhaseLife'][:].data[cell]) +
                str(dataSet.variables['SeverityIntensity'][:].data[cell])) for cell in cells_to_keep])
        dict["#code"] = dict["#code"] + code
        dict["severityIntensity"] = dict["severityIntensity"] + cellSeverityIntensity
        dict["severityType"] = dict["severityType"] + cellSeverityType
        dict["ObjectType"] = dict["ObjectType"] + objectType
        dict["level"] = dict["level"] + [str(level)] * numb_cells_to_keep
        for key in conf['CELL'].keys():
            
            data_all_cells = dataSet.variables[conf['CELL'][key]][:]
            data = data_all_cells[cells_to_keep]
            data = data.astype(float)
            dimensions = len(data.shape)
            data = np.array(data.data)

            if dimensions == 1:
                dict[key] = dict[key] + list(data)
            if dimensions == 2:

                dict[key] = dict[key] + list(data[:, level])

        lons_matrix = dataSet.variables['LonContour'][cells_to_keep, level, :].data
        lats_matrix = dataSet.variables['LatContour'][cells_to_keep, level, :].data

        for i in range(numb_cells_to_keep):

            cell_lons = lons_matrix[i][lons_matrix[i] > -180]
            cell_lats = lats_matrix[i][lats_matrix[i] > -180]

            if cell_lons != []:
                    coord = tuple(zip(cell_lons, cell_lats))
                    cell_polygon = Polygon(coord)
            else:
                    cell_polygon = "null"
            
            dict['coordinates'].append(cell_polygon)

    df = pd.DataFrame(dict)
    df = df[df['coordinates'] != "null"]
    gdf = geopandas.GeoDataFrame(df, geometry='coordinates')

    # now removing empty geometries
    gdf = gdf[gdf['coordinates'].notnull()]

    text = features(gdf.to_json(na='drop'))


    if fct == "000":
        text = text + ',' + plotTraj(dataSet, conf)

        OTfeatures = plotOT(dataSet, conf)
        if OTfeatures != "":
            text = text + ',' + OTfeatures

    return text


def readRdtConf():
    '''
    Reads the configuration from the file rdt.conf 
    :return: a dictionary with the configuration
    '''

    import os
    work_dir = os.getcwd()
    conf = {}
    rdt_file_path = ""
    rdt_file_path_app = ""

    # scanning working dir and subdirs looking for the rdt.conf file
    for name_subdir, name_dirs, all_files in os.walk(work_dir):
        for name_file in all_files:
            if name_file.endswith("rdt.conf"):
                rdt_file_path = name_subdir + os.sep + name_file
                break
    conf_dir = os.getenv("NWCSAF2ADAGUC_PATH")

    if conf_dir is None:
        conf_dir = work_dir
    for name_subdir, name_dirs, all_files in os.walk(conf_dir):
        for name_file in all_files:
            if name_file.endswith("rdt.conf"):
                found_file = name_subdir + os.sep + name_file
                if found_file != rdt_file_path:
                        rdt_file_path_app = name_subdir + os.sep + name_file
                        break

    if rdt_file_path == rdt_file_path_app and rdt_file_path != "":
        print("       ........................................................")
        print("       ........................................................")
        print("       Running RDT converter under the configuration file: " + rdt_file_path)
        print("       To change the the settings please edit rdt.conf         ")
        print("       ........................................................")
        print("       ........................................................")

    if rdt_file_path != "" and rdt_file_path_app == "":
        print("       ........................................................")
        print("       ........................................................")
        print("       Running RDT converter under the configuration file: " + rdt_file_path)
        print("       To change the the settings please edit rdt.conf         ")
        print("       ........................................................")
        print("       ........................................................")

    if rdt_file_path == "" and rdt_file_path_app != "":
        print("       ........................................................")
        print("       ........................................................")
        print("       Running RDT converter under the configuration file: " + rdt_file_path_app)
        print("       To change the the settings please edit rdt.conf         ")
        print("       ........................................................")
        print("       ........................................................")
        rdt_file_path = rdt_file_path_app

    if rdt_file_path != rdt_file_path_app and rdt_file_path != "" and rdt_file_path_app != "":
        print("       ........................................................")
        print("       ........................................................")
        print("       WARMING  WARMING WARMING WARMING WARMING  WARMING WARMING")
        print("       Two configuration files found:                           ")
        print("       First configuration file: " + rdt_file_path)
        print("       Second configuration file: " + rdt_file_path_app)
        print("       Running RDT converter under the configuration file: " + rdt_file_path_app)
        print("       To change the the settings please edit: " + rdt_file_path_app)
        print("       ........................................................")
        print("       ........................................................")
        rdt_file_path = rdt_file_path_app

    if rdt_file_path == "" and rdt_file_path_app == "":
        print("       ........................................................ ")
        print("       CONFIGURATION NOT FOUND!                                 ")
        print("       ........................................................ ")
        print("                                                                ")
        time.sleep(3)
        print("       ONE OF THE TWO FOLLOWING ACTIONS IS NEEDED:              ")
        print("                                                                ")
        print("       1- Please execute in the command line: export NWCSAF2ADAGUC_PATH=< your application path>")
        print("                                                                ")
        print("       2- Or copy rdt.conf under the directory: " + work_dir)
        print("       ........................................................ ")
        print("                                                                ")
        print("       The changes will be applied in the next execution        ")
        time.sleep(3)
        for i in range(2, 0, -1):
            sys.stdout.write("       The current execution wil run under DEFAULT values in " + str(i) + 'sec... \r')
            sys.stdout.flush()
            time.sleep(1)
        print("")


    try:
        confFile = rdt_file_path
        f = open(confFile, 'r')
        lines = f.readlines()

        for line in lines:
            if line[0] == '&':
                group = line.split('&')[1].strip()
                conf[group] = {}

        for line in lines:
            if line[0] == '&':
                line = line.replace('=', '&')
                group = line.split('&')[1].strip()
                key = line.split('&')[2].strip()
                value = line.split('&')[3].strip()
                conf[group][key] = value

        f.close()

    except:
        print("                                                             ")
        conf = ({'PLATFORM': {'viewer': 'ADAGUC'},
                'PATH': {'inDir': './data', 'outDir': './geoJSON', 'debugInDir': './debug_data',
                        'debugOutDir': './debug_geoJSON' },
                 'CELL': {'Fase': 'PhaseLife', 'Severidad': 'SeverityIntensity',
                         'Tipo': 'SeverityType'},
                 'CELL+': {'Fase': 'PhaseLife', 'Severidad': 'SeverityIntensity',
                          'Tipo': 'SeverityType'},
                 'OT': {'MinimumBT': 'BTminOT'},
                 'LEGEND': {'UPDATE': 'true', 'inDir': './legend', 'outDir':'./legend'}})

    return conf



def process_one_set(rdtFile, conf, underTM=False):
    '''
    Encodes a set of files if one of the forecasted files is not present
    it is avoided
    :param rdtFile: main netcdf rdt file
    :return: encoded geoJSON
    if desired updates the legend
    '''
    time.sleep(250)
    # allows debug option
    if underTM:
        outModDir = conf['PATH']['outDir']
        tempDir = conf['PATH']['tempDir']
    else:
        outModDir = outDir
        tempDir = conf['PATH']['tempDir']
        print('Processing file', rdtFile)

    for key in conf['FCTS'].keys():

        os.makedirs(outModDir + os.sep + 'RDT-CW' + os.sep + key + os.sep, exist_ok=True)

        alcance_str = conf['FCTS'][key]
        alcance = alcance_str.replace(" ", "").replace("[", "").replace("]", "").split(",")

        ###########################################################################
        # Writing the geoJSON that corresponds to the selected netcdf files
        ###########################################################################
        if 'hard_out_name' in conf['PATH'].keys():
            tempFile = tempDir + os.sep + 'RDT-CW' + os.sep + key + os.sep + key + '_' + 'rdt.geojson'
            outFile = outModDir + os.sep + 'RDT-CW' + os.sep + key + os.sep + key + '_' + 'rdt.geojson'
        else:   
            tempFile = tempDir + os.sep + 'RDT-CW' + os.sep + key + os.sep + key + '_' + rdtFile.split('.n')[-2].split('/')[-1] + '.geojson'
            outFile = outModDir + os.sep + 'RDT-CW' + os.sep + key + os.sep + key + '_' + rdtFile.split('.n')[-2].split('/')[-1] + '.geojson'

        srv.wait_until_closed(rdtFile)
        dataSet = netCDF4.Dataset(rdtFile, 'r')
        string_time = dataSet.getncattr('nominal_product_time')
        text = ('''{
                        "type": "FeatureCollection",
                        "dimensions": { "time":{"value":"''' +
                        string_time +
                        '''", "units": "ISO8601" }, "elevation": {"value": "0", "units": "meter"}},
                            "features": [''')
        # updating the legend
        if conf['LEGEND']['UPDATE'] == 'true':
            try:
                update_legend(string_time, conf)
            except:
                if not underTM:
                    print(" WARMING: RDT legend not updated for time: ", string_time)

        # storing the DecTime for the each cell
        number_of_cells = int(dataSet.variables['NbSigCell'][:].data[0])
        DecTime =[]
        for i in range(number_of_cells):
            DecTime.append(int(dataSet.variables['DecTime'][:].data[i]))

        dataSet.close()

        # Encoding the following files as geoJSON

        for fct in alcance:

            index = rdtFile.find('.nc')
            if fct != '000':
                nextrdtFile = rdtFile[:index] + '_' + fct + rdtFile[index:]
            else:
                nextrdtFile = rdtFile

            if underTM:
                # waiting for the needed files in live mode
                while True:
                    if os.path.isfile(nextrdtFile):
                        srv.wait_until_closed(nextrdtFile)
                        break
                    time.sleep(0.1)


            dataSet = netCDF4.Dataset(nextrdtFile, 'r')
            text = text + rdtDataSetToJson(dataSet, conf, DecTime, fct=fct) + ','
            time.sleep(1)
            dataSet.close()

        # closing the feature collection
        geoJSON_text = text[:-1] + """ ] }"""
        try: 
             json_object = json.loads(geoJSON_text) 
             print ("Is valid json? true") 
        except ValueError as e: 
             print ("Is valid json? false") 
        # opening, writting and closing
        os.makedirs(os.path.dirname(tempFile), exist_ok=True)
        f = open(tempFile, 'w')
        f.write(geoJSON_text)
        f.close()
        os.sync()
        # copying to autowms
        time.sleep(0.1)
        srv.secure_copy(tempFile, outFile)
        time.sleep(0.1)
        srv.wait_until_unlocked(outFile)
        if not underTM:
            print('Wrote: ' + outFile)

    if not underTM:
        print("File:  " + rdtFile + " processed")

    return


if __name__ == '__main__':

    t0 = time.time()
    configuration = readRdtConf()

    if len(sys.argv) == 1:
        # running software without any option, scans the whole inDir and accumulate in rdtFiles
        # all the matches

        inDir = configuration['PATH']['inDir']
        outDir = configuration['PATH']['outDir']

        rdtFiles = []
        # scanning inDir
        for subdir, dirs, files in os.walk(inDir):
            for file in files:
                # storing all the found files in an array
                filepath = subdir + os.sep + file

                if file.endswith("Z.nc") and ('RDT' in file):

                    rdtFiles.append(filepath)

    elif len(sys.argv) == 4:
        # meant to execute the script with the following info:
        # <Satellite> <area> < YYYY-MM-DDThh:mm:ssZ>
        # time format YYYY-MM-DDThh:mm:ssZ or YYYYMMDDThhmmssZ
        time_stamp = sys.argv[3].replace(":", "").replace("-", "")
        rdt_current_file = "S_NWC_RDT-CW_" + sys.argv[1] + "_" + sys.argv[2] + "_" + time_stamp + ".nc"
        rdt_files = [configuration['PATH']['inDir'] + "/" + rdt_current_file]
        outDir = configuration['PATH']['outDir']

    elif sys.argv[1] == '-h':
        print("       ........................................................")
        print("       Help:")
        print("       TM Usage: python nwcpy_rdt_to_geoJSON2.0.py <Satellite> <area> < YYYY-MM-DDThh:mm:ssZ>  ")
        print("       As in:      ")
        print("       python3 nwcpy_rdt_to_geoJSON2.0.py MSG4 Europe-VISIR  2019-02-02T13:00:00Z  ")
        print("       To reach whole in dir recursive processing, run without options: python3 nwcpy_rdt_to_geoJSON2.0.py")
        print("       In order to test your platform: python3 nwcpy_rdt_to_geoJSON2.0.py -d")
        print("       To reach this help: python3 nwcpy_rdt_to_geoJSON2.0.py -h")
        print("       CONFIGURATION IS AVAILABLE IN: rdt.conf FILE")
        print("       ........................................................")
        print("       Quiting.")
        quit()

    elif sys.argv[1] == '-d':
        # running with debug option

        print(
            "       WARMING: DEBUGING WITH SAMPLE FILE ./debug_data/S_NWC_RDT-CW_MSG4_Europe-VISIR_20180418T130000Z.nc")
        print("       ........................................................")
        print("       Output geoJSON file fully readable on: " + configuration['PLATFORM']['viewer'])
        print("       To change the target platform edit rdt.conf")
        print("       ........................................................")
        rdtFile = '/S_NWC_RDT-CW_MSG4_Europe-VISIR_20180418T130000Z.nc'
        inDir = configuration['PATH']['debugInDir']
        outDir = configuration['PATH']['debugOutDir']
        rdtFiles = [inDir + rdtFile]

    else:
        print("       Unknown option")
        print("       ........................................................")
        print("       TM Usage: python nwcpy_rdt_to_geoJSON2.0.py <Satellite> <area> < YYYY-MM-DDThh:mm:ssZ>  ")
        print("       As in:      ")
        print("       python3 nwcpy_rdt_to_geoJSON2.0.py MSG4 Europe-VISIR  2019-02-02T13:00:00Z  ")
        print("       To reach whole in dir recursive processing, run without options: python3 nwcpy_rdt_to_geoJSON2.0.py")
        print("       In order to test your platform: python3 nwcpy_rdt_to_geoJSON2.0.py -d")
        print("       To reach this help: python3 nwcpy_rdt_to_geoJSON2.0.py -h")
        print("       CONFIGURATION IS AVAILABLE IN: rdt.conf FILE")
        print("       ........................................................")
        print("       Aborting.")
        quit()

    # processing each set of detected files, looping through the main rdt files in "rdtFiles"
    for inputFile in rdtFiles:

        process_one_set(inputFile, configuration, underTM=False)
        print(time.time() - t0)
