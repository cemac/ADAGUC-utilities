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
import math
import json
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



def cellToFeature(dataSet, numCell, fct, conf, DecTime, level=0):
    '''
    Encodes a level from one individual cell as geoJSON
    :param dataSet: the dataset to be procesed
    :param numCell: the cell number [0, 1, 2,...]
    :param fct: range of the dataset, 000: measured, another ### value: forecasted
    :param conf: configuration dictionary read from  the "rdt.conf" file
    :param DecTime: an array storing, for each cell, the time gap between nominal and radiometer
    :param level: level of the contour
    :return: encoded geoJSON text
    '''
    labelPhaseLife = ({0: 'Triggering', 1: 'Triggering from Split',
                       2: 'Growing', 3: 'Maturity', 4: 'Decaying'})
    labelSeverityIntensity = ({0: 'Not defined', 1: 'Low', 2: 'Moderate',
                               3: 'High', 4: 'Very High'})

    labelSeverityType = ({0: 'No_activity', 1: 'Turbulence', 2: 'Lightning',
                          3: 'Icing', 4: 'High_altitude_icing', 5: 'Hail',
                          6: 'Heavy_rainfall', 7: 'Type_not_defined',
                          dataSet.variables['SeverityType'][:].fill_value: '--', None: '---'})
    cell_mask = np.ma.masked_array(dataSet.variables['LatContour'][numCell, level, :]).mask
    try:
        number_masked = sum(cell_mask)
    except:
        number_masked = 0
    number_of_vertex = len(dataSet.variables['LatContour'][numCell, level, :]) - number_masked

    cellPhase = labelPhaseLife[dataSet.variables['PhaseLife'][:].tolist()[numCell]]
    cellSeverityIntensity = labelSeverityIntensity[dataSet.variables['SeverityIntensity'][:].tolist()[numCell]]

    if fct == '000':
        configuration = conf['CELL']
    else:
        configuration = conf['CELL+']

    # reading the platform
    platform = conf['PLATFORM']['viewer']

    if platform == 'ADAGUC':
        header = '''", "Time": "'''
        newItem = '''", "'''
        equal = '''": "'''
        end = ''''''
    elif platform == 'LEAFLET':
        header = '''", "popupContent": "<p>'''
        newItem = '''<br/>'''
        equal = ''': '''
        end = "</p>"
    # obtaining the cell time
    tStr = dataSet.getncattr('nominal_product_time').split('_')[0]
    datetime_object = (datetime.strptime(tStr, '%Y-%m-%dT%H:%M:%SZ')
                       + timedelta(seconds=(60 * int(fct) +
                                            DecTime[numCell])))

    content = datetime_object.time().isoformat() + newItem + '''level''' + equal + str(level) + newItem

    for key in configuration.keys():
        if configuration[key] in dataSet.variables.keys():
            if configuration[key] == 'PhaseLife':
                content = (content + key + equal +
                           labelPhaseLife[dataSet.variables[configuration[key]][:].tolist()[numCell]] + newItem)

            elif configuration[key] == 'SeverityIntensity':
                content = (content + key + equal +
                           labelSeverityIntensity[dataSet.variables[configuration[key]][:].tolist()[numCell]] + newItem)

            elif configuration[key] == 'SeverityType':
                content = (content + key + equal +
                           labelSeverityType[dataSet.variables[configuration[key]][:].tolist()[numCell]] + newItem)

            else:
                value = dataSet.variables[configuration[key]][:].tolist()[numCell]
                content = (content + key + equal + str(value) + " " +
                           dataSet.variables[configuration[key]].units + newItem)
        else:
            content = (content + key + equal + " ---" + newItem)
    # suppressing the last newItem string separator element
    # adding code for styling the code is #<level><fct><PhaseLife><SeverityIntensity>
    # by example #100021 mean cell in level 1, fct=000, PhaseLife=2 ('Growing') and SeverityIntensity=1 ('Low')
    code = (str(level) + fct + str(dataSet.variables['PhaseLife'][:].tolist()[numCell]) +
            str(dataSet.variables['SeverityIntensity'][:].tolist()[numCell]))
    content = content + '''#code''' + equal + code

    content = content + end

    text = ('''{ "type": "Feature", 
            "properties": {"ObjectType": "cell-''' + fct +
            '''", "Status": "''' + cellPhase +
            '''", "severityIntensity": "''' + cellSeverityIntensity +
            header + content + ''' "},''' +
            '''
          "geometry": {
              "type": "Polygon",
              "coordinates": [[''')

    # writing the coordinates of the polygon vertexes
    for vertex in range(number_of_vertex):
        text = (text + "[" + str(dataSet.variables['LonContour'][numCell, level, :][vertex])
                + ","
                + str(dataSet.variables['LatContour'][numCell, level, :][vertex])
                + "],")

    # adding the first line point at the end to construct a closed line
    text = (text + "[" + str(dataSet.variables['LonContour'][numCell, level, :][0])
            + ","
            + str(dataSet.variables['LatContour'][numCell, level, :][0])
            + """]]]
                  }
                }""")

    return text


def plotPastTrajCG(dataSet, numCell, conf):
    '''
    Encodes the measured gravity center trajectory
    :param dataSet: the dataset to be procesed
    :param numCell: the cell number [0, 1, 2,...]
    :return: encoded geoJSON text
    '''
    # reading the platform
    platform = conf['PLATFORM']['viewer']

    if platform == 'ADAGUC':
        header = '''"Cell": '''
        end = '''},'''
    elif platform == 'LEAFLET':
        header = '''"popupContent": "<p>Trajectory: '''
        end = '''</p>"},'''



    text = ('''{ "type": "Feature", 
                "properties": {"ObjectType": "PastCGTraj", "Status": "--",'''
            + header + str(numCell) + end +
            '''
          "geometry": {
              "type": "LineString",
              "coordinates": [''')

    # writing the coordinates of the line

    vert_mask = np.ma.masked_array(dataSet.variables['LonTrajCellCG'][numCell, :]).mask
    try:
        number_masked = sum(vert_mask)
    except:
        number_masked = 0
    number_of_vertex = len(dataSet.variables['LonTrajCellCG'][numCell, :]) - number_masked

    # A valid GeoJSON LineString should have two or more points
    if number_of_vertex >= 2:
        for vertex in range(number_of_vertex):

            text = (text + "[" + str(dataSet.variables['LonTrajCellCG'][numCell, :][vertex])
                    + ","
                    + str(dataSet.variables['LatTrajCellCG'][numCell, :][vertex])
                    + "],")
        text = text[:-1]

    text = (text + """]
                      }
                 },""")

    return text


def plotFcstTrajCG(dataSet, numCell, conf):
    '''
    Encodes the forecasted gravity center trajectory
    :param dataSet: the dataset to be procesed
    :param numCell: the cell number [0, 1, 2,...]
    :return: encoded geoJSON text
    '''
    # reading the platform
    platform = conf['PLATFORM']['viewer']

    if platform == 'ADAGUC':
        header = '''"Cell": '''
        end = '''},'''
    elif platform == 'LEAFLET':
        header = '''"popupContent": "<p>Trajectory: '''
        end = '''</p>"},'''

    text = ('''{ "type": "Feature", 
                "properties": {"ObjectType": "FcstCGTraj", "Status": "--",'''
            + header + str(numCell) + end +
            '''
          "geometry": {
              "type": "LineString",
              "coordinates": [''')

    # Calculating the course line
    geod = Geodesic.WGS84
    lat1 = dataSet.variables['LatG'][numCell][0]
    lon1 = dataSet.variables['LonG'][numCell][0]
    azi1 = dataSet.variables['MvtDirection'][numCell]
    s12 = dataSet.variables['MvtSpeed'][numCell] * 60 * 15
    if math.isnan(azi1) or math.isnan(s12):
        return ''
    black_line = geod.Direct(lat1, lon1, azi1, s12)
    # writing the first and last points
    text = (text + "[" + str(black_line['lon1']) + "," + str(black_line['lat1']) + "]," +
            "[" + str(black_line['lon2']) + "," + str(black_line['lat2']) + "]]}},"
            )
    #print(azi1, s12)
    return text


def plotOT(dataSet, conf):
    '''
    Encodes the overshooting tops
    :param dataSet: the dataset to be procesed
    :param conf: the global configuration
    :return: encoded geoJSON text
    '''
    # reading the platform

    platform = conf['PLATFORM']['viewer']

    if platform == 'ADAGUC':
        header = '''"'''
        newItem = '''", "'''
        equal = '''": "'''
        end = ''''''
    elif platform == 'LEAFLET':
        header = ''' "popupContent": "<p>'''
        newItem = '''<br/>'''
        equal = ''': '''
        end = "</p>"

    text = ''
    if 'NumIdCellOT' not in dataSet.variables:
        return ''
    number_of_points = len(dataSet.variables['LatPixOT'])
    for num in range(number_of_points):
        if not math.isnan(dataSet.variables['LonPixOT'][num]):
            configuration = conf['OT']
            # adding the proprieties
            content = ""
            for key in configuration:
                value = dataSet.variables[configuration[key]][num]
                content = (content + key + equal + str(value) + " " +
                           dataSet.variables[configuration[key]].units + newItem)

            content = content[:-len(newItem)]
            content = content + end

            text = text + ('''{ "type": "Feature", 
                    "properties": {"ObjectType": "OT", "Status": "NotDefined", ''' +
                           header + content + '''"}, ''' +
                           '''
                
                         "geometry": {
                             "type":"Polygon",
                             "coordinates": [[''')
            # writing the coordinates of the OT polygon
            # d is the distance from OT to the triangle vertexes
            d = 0.05
            ot_lon = dataSet.variables['LonPixOT'][num]
            ot_lat = dataSet.variables['LatPixOT'][num]
            text = (text + "[" + str(ot_lon) + "," + str(ot_lat + d) + "],[" +
                    str(ot_lon - d) + "," + str(ot_lat - 0.5 * d) + "],[" +
                    str(ot_lon + d) + "," + str(ot_lat - 0.5 * d) + "],[" +
                    str(ot_lon) + "," + str(ot_lat + d) +
                    "]]]}},"

                    )
    text = text[:-1]
    return text


def rdtDataSetToJson(dataSet, conf, DecTime, fct='000'):
    '''
    Encodes a single  dataset
    :param dataSet: the dataset to be procesed
    :param conf: the global configuration
    :param DecTime: an array storing, for each cell, the time gap between nominal and radiometer
    :param fct: range of the dataset, 000: measured, another ### value: forecasted
    :return: encoded geoJSON text
    '''
    conv_type = dataSet.variables['ConvType'][:]
    cells_to_keep = np.where((conv_type > 0) & (conv_type < 8))[0]

    text = ''
    # generating the text corresponding to each feature in dataSet

    for i in cells_to_keep:
        # adding each cell
        text = text + cellToFeature(dataSet, i, fct, conf, DecTime, level=0) + ","

        cell_mask = np.ma.masked_array(dataSet.variables['LatContour'][i, 1, :]).mask
        try:
            number_masked = sum(cell_mask)
        except:
            number_masked = 0
        number_of_vertex_level_1 = len(dataSet.variables['LatContour'][i, 1, :]) - number_masked

        if number_of_vertex_level_1 != 0:
            text = text + cellToFeature(dataSet, i, fct, conf, DecTime, level=1) + ","
            # print(number_of_vertex_level_1)

        # adding the gravity center trajectories
        if 'LatTrajCellCG' in dataSet.variables:
            text = text + plotPastTrajCG(dataSet, i, conf)

        # adding the gravity center forecasted trajectories only for the main file
        if fct == '000':
            text = text + plotFcstTrajCG(dataSet, i, conf)

    # adding the overshooting tops
    if 'NumIdCellOT' in dataSet.variables:
            text = text + plotOT(dataSet, conf)
    else:
            text = text[:-1]
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
    #time.sleep(250)
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
        number_of_cells = int(dataSet.variables['NbSigCell'][:].tolist()[0])
        DecTime =[]
        for i in range(number_of_cells):
            DecTime.append(int(dataSet.variables['DecTime'][:].tolist()[i]))

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
            else:
                if not os.path.isfile(nextrdtFile):
                    print('File not found: ', nextrdtFile)
                    continue

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
        #print('inside')
        time.sleep(0.1)
        srv.secure_move(tempFile, outFile, conf)
        time.sleep(0.1)
        srv.wait_until_unlocked(outFile, conf)
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
        # <Satellite> <area> < YYYYMMDDThhmmssZ>
        # time format  YYYYMMDDThhmmssZ
        time_stamp = sys.argv[3].replace(":", "").replace("-", "")
        rdt_current_file = "S_NWC_RDT-CW_" + sys.argv[1] + "_" + sys.argv[2] + "_" + time_stamp + ".nc"
        rdtFiles = [configuration['PATH']['inDir'] + "/" + rdt_current_file]
        outDir = configuration['PATH']['outDir']

    elif sys.argv[1] == '-h':
        print("       ........................................................")
        print("       Help:")
        print("       TM Usage: python nwcpy_rdt_to_geoJSON2.0.py <Satellite> <area> < YYYY-MM-DDThh:mm:ssZ>  ")
        print("       As in:      ")
        print("       python3 nwcpy_rdt_to_geoJSONpy MSG4 Europe-VISIR  20190827T090000Z  ")
        print("       To reach whole in dir recursive processing, run without options: python3 nwcpy_rdt_to_geoJSON2.0.py")
        print("                                                                                                          ")
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
