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

import h5py
import numpy as np
import sys
import os
import time
import cv2
from scipy.interpolate import interp1d
sys.path.append('..')
from facilities import services as srv

###################################################################################################################
# minimal standard ATM converter
###################################################################################################################

Altitudes = [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000, 14000.00, 15000.00,
             16000.00, 17000.00, 18000.00, 19000.00, 20000.0, 21000.0, 22000.0, 23000.0, 24000.0, 25000.0, 26000.0,
             27000.0, 28000.0, 29000.0, 30000.0, 31000.0, 32000.0, 33000.0, 34000.0, 35000.0, 36000.0, 37000.0, 38000.0,
             39000.0, 40000.0, 41000.0, 42000.0, 43000.0, 44000.0, 45000.0, 46000.0, 47000.0, 48000.0, 49000.0, 50000.0,
             51000.0, 52000.0, 53000.0, 54000.0, 55000.0, 56000.0, 57000.0, 58000.0, 59000.0, 60000.0, 61000.0, 62000.0,
             63000.0, 64000.0, 65000.0, 66000.0, 67000.0, 68000.0, 69000.0, 70000.0, 71000.0, 72000.0, 73000.0, 74000.0,
             75000.0, 76000.0, 77000.0, 78000.0, 79000.0, 80000.0, 81000.0, 82000.0, 83000.0, 84000.0, 85000.0, 86000.0,
             87000.0, 88000.0, 89000.0, 90000.0, 91000.0, 92000.0, 93000.0, 94000.0, 95000.0, 96000.0, 97000.0, 98000.0,
             99000.0, 100000, 101000, 102000, 103000]

Pressures = [101325, 97716.6, 94212.9, 90811.7, 87510.5, 84307.3, 81199.6, 78185.4, 75262.4, 72428.5, 69681.7, 67019.8,
             64440.9, 61942.9, 59523.9, 57182.0, 54915.2, 52721.8, 50599.8, 48547.6, 46563.3, 44645.1, 42791.5, 41000.7,
             39271.0, 37600.9, 35988.8, 34433.1, 32932.4, 31485.0, 30089.6, 28744.7, 27448.9, 26200.8, 24999.0, 23842.3,
             22729.3, 21662.7, 20646.2, 19677.3, 18753.9, 17873.9, 17035.1, 16235.7, 15473.8, 14747.7, 14055.6, 13396.0,
             12767.4, 12168.3, 11597.3, 11053.0, 10534.4, 10040.0, 9568.87, 9119.83, 8691.87, 8283.99, 7895.25, 7524.75,
             7171.64, 6835.10, 6514.35, 6208.65, 5917.30, 5639.62, 5375.00, 5123.08, 4883.29, 4655.03, 4437.75, 4230.89,
             4033.94, 3846.41, 3667.84, 3497.80, 3335.86, 3181.62, 3034.72, 2894.78, 2761.48, 2634.49, 2513.50, 2398.22,
             2288.38, 2183.71, 2083.96, 1988.89, 1898.28, 1811.92, 1729.59, 1651.11, 1576.29, 1504.95, 1436.93, 1372.08,
             1310.23, 1251.24, 1194.99, 1141.34, 1090.16, 1041.34, 994.768, 950.338]

AltitudesRev = Altitudes[::-1]
PressuresRev = Pressures[::-1]


def FlyingLevelFromPressure(press):
    AltInFeets = interp1d(PressuresRev, AltitudesRev, bounds_error=False)(press)
    return int(AltInFeets // 100)


def PressureFromFlyingLevel(FL):

    FL = FL * 100
    PressInPas = interp1d(Altitudes, Pressures, bounds_error=False)(FL)
    return PressInPas

###################################################################################################################
# end of standard ATM converter
###################################################################################################################

###################################################################################################################
# configuration management part
###################################################################################################################

def which_version(hdf5_dataset):

    dataSet = hdf5_dataset["Wind"]
    ref = np.dtype(dataSet.dtype)
    if 'lat' in ref.names:
        version = 'GEOv2016'
    elif 'latitude' in ref.names:
        version = 'GEOv2018'
    else:
        version = 'unknown'

    return version


def updated_conf(configuration, version):
    if version == 'GEOv2018':
        pos = 0
    else:
        pos = 1

    new_dict = {}
    for key in configuration.keys():
        new_dict[key] = {}
    for key in configuration.keys():
        for sub_key in configuration[key].keys():
            new_dict[key][sub_key] = configuration[key][sub_key]

    for key in configuration['TO_CSV'].keys():
        new_dict['TO_CSV'][key] = configuration['TO_CSV'][key][pos]

    return new_dict


def readHrwConf():
    '''
    Reads the configuration from the file hrw.conf
    :return: a new_dictionary with the configuration
    '''

    
    work_dir = os.getcwd()
    conf = {}
    hrw_file_path = ""
    hrw_file_path_app = ""

    # scanning working dir and subdirs looking for the hrw.conf file
    for name_subdir, name_dirs, all_files in os.walk(work_dir):
        for name_file in all_files:
            if name_file.endswith("hrw.conf"):
                hrw_file_path = name_subdir + os.sep + name_file
                break
    conf_dir = os.getenv("NWCSAF2ADAGUC_PATH")

    if conf_dir is None:
        conf_dir = work_dir
    for name_subdir, name_dirs, all_files in os.walk(conf_dir):
        for name_file in all_files:
            if name_file.endswith("hrw.conf"):
                found_file = name_subdir + os.sep + name_file
                if found_file != hrw_file_path:
                        hrw_file_path_app = name_subdir + os.sep + name_file
                        break
    #print(hrw_file_path_app, hrw_file_path)
    if hrw_file_path == hrw_file_path_app and hrw_file_path != "":
        print("       ........................................................")
        print("       ........................................................")
        print("       Running HRW conveter under the configuration file: " + hrw_file_path)
        print("       To change the the settings please edit hrw.conf         ")
        print("       ........................................................")
        print("       ........................................................")

    if hrw_file_path != "" and hrw_file_path_app == "":
        print("       ........................................................")
        print("       ........................................................")
        print("       Running HRW conveter under the configuration file: " + hrw_file_path)
        print("       To change the the settings please edit hrw.conf         ")
        print("       ........................................................")
        print("       ........................................................")

    if hrw_file_path == "" and hrw_file_path_app != "":
        print("       ........................................................")
        print("       ........................................................")
        print("       Running HRW conveter under the configuration file: " + hrw_file_path_app)
        print("       To change the the settings please edit hrw.conf         ")
        print("       ........................................................")
        print("       ........................................................")
        hrw_file_path = hrw_file_path_app

    if hrw_file_path != hrw_file_path_app and hrw_file_path != "" and hrw_file_path_app != "":
        print("       ........................................................")
        print("       ........................................................")
        print("       WARMING  WARMING WARMING WARMING WARMING  WARMING WARMING")
        print("       Two configuration files found:                           ")
        print("       First configuration file: " + hrw_file_path)
        print("       Second configuration file: " + hrw_file_path_app)
        print("       Running HRW conveter under the configuration file: " + hrw_file_path_app)
        print("       To change the the settings please edit: " + hrw_file_path_app)
        print("       ........................................................")
        print("       ........................................................")
        hrw_file_path = hrw_file_path_app

    if hrw_file_path == "" and hrw_file_path_app == "":
        print("       ........................................................ ")
        print("       CONFIGURATION NOT FOUND!                                 ")
        print("       ........................................................ ")
        print("                                                                ")
        time.sleep(3)
        print("       ONE OF THE TWO FOLLOWING ACTIONS IS NEEDED:              ")
        print("                                                                ")
        print("       1- Please execute in the command line: export NWCSAF2ADAGUC_PATH=< your application path>")
        print("                                                                ")
        print("       2- Or copy hrw.conf under the directory: " + work_dir)
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
        configuration_file = hrw_file_path
        f = open(configuration_file, 'r')
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

                if group == 'TO_CSV':
                    # allow to process v2016 and v2018 wind files
                    value = [line.split('&')[3].strip(), line.split('&')[-1].strip()]
                else:
                    value = line.split('&')[3].strip()
                conf[group][key] = value
        # transforming the query group to numerical array first el corresponds to pressures in Pa
        # the second one corresponds to FL, or HPa
        for key in conf['QUERY'].keys():
            if key == 'FL':
                str_array = conf['QUERY'][key].split(',')
                nmb_array = [[float(PressureFromFlyingLevel(float(el))), float(el)] for el in str_array]
                conf['QUERY'][key] = nmb_array

            else:
                str_array = conf['QUERY'][key].split(',')
                nmb_array = [[float(el) * 100, float(el)] for el in str_array]

                conf['QUERY'][key] = nmb_array

        f.close()

    except:
        print(" Running HRW conveter under default configuration")
        conf = ({'PLATFORM': {'viewer': 'ADAGUC'},
                 'PATH': {'inDir': './data', 'outDir': './csv'},'QUERY':{'ONE': [[100000.0, 1000.0], [10000.0, 100.0]]},
                 'TO_CSV': {'lat': ['latitude', 'lat'], 'lon': ['longitude', 'lon'],
                            'pressure': ['air_pressure', 'pressure'], 'ff': ['wind_speed', 'wind_speed'],
                            'dd': ['wind_from_direction', 'wind_direction']}})



    return conf

###############################################################################################################
# xml updating function


def xml_update(conf):

   colours = (('#800080', '#0000FF', '#00FFFF', '#94b001', '#008000', '#FFFF00', '#FFA500', '#FF0000', '#FF00FF',
                '#FFC0CB', '#740E41'))

   header = ('''<?xml version="1.0" encoding="UTF-8" ?>
            <Configuration>
            <CacheDocs enabled="false"/>"
            <!-- Custom styles -->
            
            ''')

   style_template =('''<Style name="windbarbLAYER">
            <Legend fixedclasses="true" tickinterval="2" tickround="1">no2</Legend>
            <Min>0.0</Min>
            <Max>10</Max>
            <Vector vectorstyle="barb" linecolor= "L_COLOUR" />
            <Thinning radius="30"/>
            <LegendGraphic value="/data/legends/empty.png"/>
            <RenderMethod>barbthin</RenderMethod>
            </Style> 
            
            ''')

   layer_template = ('''<Layer  type = "database" >
           <FilePath  filter = "^.*\.csv$">/data/adaguc-autowms/HRW/KEY/LAYER/</FilePath>
           <Name>windLAYER</Name>
           <Title>Wind</Title>
           <Variable>ff</Variable>
           <Variable>dd</Variable>
           <Styles>windbarbLAYER</Styles>
           </Layer>
           
           ''')

   closure = ('''  
           <!-- End of configuration /-->
           </Configuration>''')


   for key in conf['QUERY'].keys():

       for i in range(len(conf['QUERY'][key]) - 1):
           content = header
           styles = ""
           layers = ""
           level0, label0 = conf['QUERY'][key][i]
           level1, label1 = conf['QUERY'][key][i + 1]

           strLayer = key + str(int(label0)) + '_' + key + str(int(label1))
           if key == 'HRW':
               strLayer = 'HRW'
               strkey = ''
           else:
               strkey = '/' + key

           styles = styles + style_template.replace("LAYER", strLayer).replace("L_COLOUR", colours[i])
           layers = layers + layer_template.replace("LAYER", strLayer).replace("/KEY", strkey)
           content = content + styles + layers + closure

           if key != 'HRW':
               strLayer = strLayer + 'HRW'


           f = open(conf['XML']['outDir'] + os.sep + strLayer + ".xml", 'w')
           f.write(content)
           f.close()

   return


def update_legend(text, conf):
    '''
    :param text: string to put in the legend
    :param conf: configuration dictionary
    :return: nothing
    writes the time in the draft_legend png file, writes a new file with the time stamp.
    '''
    colours = (('#800080', '#0000FF', '#00FFFF', '#94b001', '#008000', '#FFFF00', '#FFA500', '#FF0000', '#FF00FF',
                '#FFC0CB', '#740E41'))
    for key in conf['QUERY'].keys():
        in_legend_image = conf['LEGEND']['inDir'] + "/legend_HRW_draft.png"
        img_BGRA = cv2.imread(in_legend_image)


        font = cv2.FONT_HERSHEY_SIMPLEX
        bottomLeftCornerOfText = (15, img_BGRA.shape[0] - 15)
        fontScale = 1
        fontColor = (0, 0, 0, 255)
        lineType = 2

        cv2.putText(img_BGRA, text,
                    bottomLeftCornerOfText,
                    font,
                    fontScale,
                    fontColor,
                    lineType)

        cv2.putText(img_BGRA, "NWC GEO HRW",
                    (15, 40),
                    cv2.FONT_HERSHEY_DUPLEX,
                    fontScale,
                    fontColor,
                    lineType)
        # ading the colored rectangles
        columnas = 2
        items = len(conf['QUERY'][key]) - 1
        items_por_columna = int((items + 2) / columnas)
        for i in range(items):
            level0, label0 = conf['QUERY'][key][i]
            level1, label1 = conf['QUERY'][key][i + 1]
            alturaReglon = int(((img_BGRA.shape[0] - 120) * columnas) / items)
            reglon = img_BGRA.shape[0] - 60 - alturaReglon * (i % items_por_columna)
            columna = 100 + 300 * int(i / items_por_columna)

            bottomLeftCornerOfText = (columna, reglon)
            newText = key + str(int(label0)) + '_' + key + str(int(label1))
            cv2.putText(img_BGRA, newText,
                    bottomLeftCornerOfText,
                    font,
                    fontScale,
                    fontColor,
                    lineType)
            h = colours[i].lstrip('#')
            BGR = tuple(int(h[i:i + 2], 16) for i in (4, 2, 0))
            cv2.rectangle(img_BGRA, (columna - 70, reglon), (columna -20, reglon - int(alturaReglon / 2)), BGR, -1)

        # adding transparency
        b_channel, g_channel, r_channel = cv2.split(img_BGRA)

        alpha_channel = np.ones(b_channel.shape, dtype=b_channel.dtype) * 255  # creating a dummy alpha channel image.

        # now adding transparencies in the white areas
        thereshold = 220
        white = np.where((b_channel > thereshold) & (g_channel > thereshold) & (r_channel > thereshold))
        alpha_channel[white] = 0

        final_legend = cv2.merge((b_channel, g_channel, r_channel, alpha_channel))
        final_legend = cv2.resize(final_legend, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_LINEAR)
        out_legend = conf['LEGEND']['inDir'] + "/legend_" + key + "HRW.png"
        cv2.imwrite(out_legend, final_legend)

    return

###################################################################################################################
# end of configuration management part
###################################################################################################################


def wait_until_closed(hrw_file):

    while True:
        try:
            src = h5py.File(hrw_file, 'r')
            src.close()
            return
        except:
            time.sleep(1)
    return


def process_one_file(hrw_file, conf, underTM=False):
    '''
    Encodes an hrw file to csv
    :param hrw_file: main netcdf hrw file
    :param conf: dictionary storing the configuration
    write a file and...
    :return: nothing
    '''
    if underTM:
        outModDir = conf['PATH']['outDir']
        tempDir = conf['PATH']['tempDir']
    else:
        outModDir = outDir
        tempDir = conf['PATH']['tempDir']
        print('Processing file', hrw_file)

    out_dir = outModDir

    for key in conf['QUERY'].keys():

        os.makedirs(out_dir + os.sep + 'HRW' + os.sep + key, exist_ok=True)

    wait_until_closed(hrw_file)
    # Opens HRW input file
    #print("FILE: ", hrw_file)
    pf5 = h5py.File(hrw_file, 'r')
    # Reading the variables
    keys = list(pf5.keys())

    software_version = which_version(pf5)

    updt_conf = updated_conf(conf, software_version)

    # keeping only those which could store winds

    wind_group = []
    for i in range(len(keys)):
        if ('number' not in keys[i]) and ('nb' not in keys[i]) and ('Trajec' not in keys[i]) and ('Seg' not in keys[i]) and ('_' in keys[i]):
            wind_group.append(keys[i])

    # generating a dict to store the requested values

    data_dict = {}
    for key in updt_conf['TO_CSV']:
        data_dict[key] = []

    # filling the dictionary with the values in the netcdf
    for data_name in wind_group:

        wind_data = pf5[data_name]

        for key in data_dict:

            try:
                if key == 'ff':
                    a = wind_data[updt_conf['TO_CSV'][key]][:]
                    wind_ms = a * 1
                    # adaguc does the conversion from m per sec to knots
                    data_dict[key] = np.append(data_dict[key], wind_ms)
                else:
                    a = wind_data[updt_conf['TO_CSV'][key]][:]

                    data_dict[key] = np.append(data_dict[key], a)

            except:
                pass
    '''
    print(data_dict.keys())
    '''
    for key in data_dict.keys():
        if key in ['lat', 'lon']:
            str_from_val = ["%-.4f" % ele for ele in data_dict[key]]
            data_dict[key] = str_from_val

    try:
        formatted_time_string = str(pf5.attrs['nominal_product_time'])[2:-1]
    except:
        time_string = hrw_file.split('_')[-1].split('.')[0]
        formatted_time_string = (time_string[0:4] + '-' + time_string[4:6] + '-' + time_string[6:11] +
                                 ':' + time_string[11:13] + ':' + time_string[13:])

    pf5.close()
    # updating the legend
    if conf['LEGEND']['UPDATE'] == 'true':
        try:
            update_legend(formatted_time_string, conf)
        except:
            print(" WARMING: legend not updated.")
    # and formatting TBD: format as text lin 504
    data_dict['dd'] = np.trunc(data_dict['dd'])
    data_dict['dd'] = data_dict['dd'].astype(int)
    data_dict['ff'] = np.trunc(data_dict['ff'])
    data_dict['ff'] = data_dict['ff'].astype(int)


    data_frame = []

    for key in data_dict.keys():
        data_frame.append(data_dict[key])
    pressure_column = np.array(data_dict['pressure'])
    for key in conf['QUERY'].keys():
        for i in range(len(conf['QUERY'][key]) - 1):

            level0, label0 = conf['QUERY'][key][i]
            level1, label1 = conf['QUERY'][key][i + 1]
            prefix = key + str(int(label0)) + '_' + key + str(int(label1))
            if key == 'HRW':
                prefix = 'HRW'

            os.makedirs(tempDir + os.sep + 'HRW' + os.sep + key + os.sep +
                        prefix, exist_ok=True)
            os.makedirs(out_dir + os.sep + 'HRW' + os.sep + key + os.sep +
                        prefix, exist_ok=True)

            # filling the file with the dictionary in csv format
            temp_file = (tempDir + os.sep + 'HRW' + os.sep + key + os.sep +
                        prefix + os.sep + prefix + '_' +
                        hrw_file.split('.n')[-2].split('/')[-1] + '.csv')

            out_file = (out_dir + os.sep + 'HRW' + os.sep + key + os.sep +
                        prefix + os.sep + prefix + '_' +
                        hrw_file.split('.n')[-2].split('/')[-1] + '.csv')


            # cleaning first the file
            f = open(temp_file, 'w')
            f.close()


            valid_positions = np.where((pressure_column <= level0) & (pressure_column > level1))[0]
            number_of_winds = len(valid_positions)
            if number_of_winds > 0:
                # opening the out_file in append mode to add the first line with time dimension
                f = open(temp_file, 'a')

                # adding the time as a comment at the beginning of the csv
                f.write('# time=' + formatted_time_string + '\n')
                # writing the header
                header_elements = data_dict.keys()
                f.write(",".join(header_elements) + '\n')

                number_of_cols = len(header_elements)
                for i in valid_positions:
                    line = ''
                    for j in range(number_of_cols - 1):
                        line = line + str(data_frame[j][i]) + ','
                    line = line + str(data_frame[number_of_cols - 1][i]) + '\n'

                    f.write(line)
                '''
                # saving the data in the csv file
                for i in range(0, number_of_winds, chunk):
                    df[((df.pressure <= level0) & (df.pressure > level1))][i:(i +chunk)].to_csv(f, sep=',', header=False, index=False)
                    print(i, i + chunk)
                '''

                f.close()
                os.sync()
                srv.secure_move(temp_file, out_file)
                if not underTM:
                    print('Generated csv file: ' + out_file)
            else:
                # removing the out csv file if it is empty
                os.remove(out_file)
            

    if conf['XML']['UPDATE'] == 'true':
        xml_update(conf)

    if not underTM:
        print("File:  " + hrw_file + " processed")
    return


if __name__ == '__main__':

    main_configuration = readHrwConf()




    if len(sys.argv) == 1:
        # running software without options
        # in this mode the software scans the whole inDir
        inDir = main_configuration['PATH']['inDir']
        outDir = main_configuration['PATH']['outDir']
        hrw_files = []
        # scanning inDir
        for subdir, dirs, files in os.walk(inDir):
            for file in files:
                # storing all the found files in an array
                filepath = subdir + os.sep + file
                if file.endswith("Z.nc") and ('HRW' in file):
                    print(filepath)
                    hrw_files.append(filepath)

    elif len(sys.argv) == 4:
        # to execute the script with the following info
        # <Satellite> <area> < YYYY-MM-DDThh:mm:ssZ>
        # time format YYYY-MM-DDThh:mm:ssZ
        time_stamp = sys.argv[3].replace(":", "").replace("-", "")
        hrw_current_file = "S_NWC_HRW_" + sys.argv[1] + "_" + sys.argv[2] + "_" + time_stamp + ".nc"
        hrw_files = [main_configuration['PATH']['inDir'] + "/" + hrw_current_file]
        outDir = main_configuration['PATH']['outDir']

    elif sys.argv[1] == '-d':
        # running with debug option
        hrw_debug_file = '/debugHRWZ.nc'
        outDir = main_configuration['PATH']['debugOutDir']

        hrw_files = [main_configuration['PATH']['debugInDir'] + hrw_debug_file]
        print("       WARMING: DEBUGING WITH SAMPLE FILE " + main_configuration['PATH']['debugInDir'] + hrw_debug_file)

    elif sys.argv[1] == '-h':
        print("       ........................................................")
        print("       Help:")
        print("       TM Usage: python nwcpy_hrw_to_csv.py <Satellite> <area> < YYYY-MM-DDThh:mm:ssZ>  ")
        print("       As in:      ")
        print("       python3 nwcpy_hrw_to_csv.py MSG4 Europe-VISIR  2019-02-02T13:00:00Z  ")
        print("       To reach whole in dir recursive processing: python3 nwcpy_hrw_to_csv.py")
        print("       In order to test your platform: python3 nwcpy_hrw_to_csv.py -d")
        print("       This help: python3 nwcpy_hrw_to_csv.py -h")
        print("       CONFIGURATION IS AVAILABLE IN: hrw.conf FILE")
        print("       ........................................................")
        quit()

    else:
        print("       Unknown option(s)")
        print("       TM Usage: python nwcpy_hrw_to_csv.py <PGE id> <Satellite> <area> < YYYY-MM-DDThh:mm:ssZ>  ")
        print("       Whole in dir recursive processing: python3 nwcpy_hrw_to_csv.py")
        print("       Debug usage to test your platform: python3 nwcpy_hrw_to_csv.py -d")
        print("       Help: python3 nwcpy_hrw_to_csv.py -h")
        print("       Aborting.")
        quit()

    # processing each set of detected files
    for inputFile in hrw_files:

        process_one_file(inputFile, main_configuration)

    # end of the application
