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
import sys
import os
import time
import calendar
import numpy as np
import numpy.ma as ma
sys.path.append('..')
from facilities import services as srv

def readConf():
    '''
    Reads the configuration from the file exim.conf
    :return: a dictionary with the configuration
    '''

    import os
    work_dir = os.getcwd()
    conf = {}
    pixel_file_path = ""
    pixel_file_path_app = ""

    # scanning working dir and subdirs looking for the exim.conf file
    for name_subdir, name_dirs, all_files in os.walk(work_dir):
        for name_file in all_files:
            if name_file.endswith("exim.conf"):
                pixel_file_path = name_subdir + os.sep + name_file
                break
    conf_dir = os.getenv("NWCSAF2ADAGUC_PATH")

    if conf_dir is None:
        conf_dir = work_dir
    for name_subdir, name_dirs, all_files in os.walk(conf_dir):
        for name_file in all_files:
            if name_file.endswith("exim.conf"):
                found_file = name_subdir + os.sep + name_file
                if found_file != pixel_file_path:
                        pixel_file_path_app = name_subdir + os.sep + name_file
                        break
    #print(pixel_file_path_app, pixel_file_path)
    if pixel_file_path == pixel_file_path_app and pixel_file_path != "":
        print("       ........................................................")
        print("       ........................................................")
        print("       Running file adapter under the configuration file: " + pixel_file_path)
        print("       To change the the settings please edit exim.conf         ")
        print("       ........................................................")
        print("       ........................................................")

    if pixel_file_path != "" and pixel_file_path_app == "":
        print("       ........................................................")
        print("       ........................................................")
        print("       Running file adapter under the configuration file: " + pixel_file_path)
        print("       To change the the settings please edit exim.conf         ")
        print("       ........................................................")
        print("       ........................................................")

    if pixel_file_path == "" and pixel_file_path_app != "":
        print("       ........................................................")
        print("       ........................................................")
        print("       Running file adapter under the configuration file: " + pixel_file_path_app)
        print("       To change the the settings please edit exim.conf         ")
        print("       ........................................................")
        print("       ........................................................")
        pixel_file_path = pixel_file_path_app

    if pixel_file_path != pixel_file_path_app and pixel_file_path != "" and pixel_file_path_app != "":
        print("       ........................................................")
        print("       ........................................................")
        print("       WARMING  WARMING WARMING WARMING WARMING  WARMING WARMING")
        print("       Two configuration files found:                           ")
        print("       First configuration file: " + pixel_file_path)
        print("       Second configuration file: " + pixel_file_path_app)
        print("       Running file adapter under the configuration file: " + pixel_file_path_app)
        print("       To change the the settings please edit: " + pixel_file_path_app)
        print("       ........................................................")
        print("       ........................................................")
        pixel_file_path = pixel_file_path_app

    if pixel_file_path == "" and pixel_file_path_app == "":
        print("       ........................................................ ")
        print("       CONFIGURATION NOT FOUND!                                 ")
        print("       ........................................................ ")
        print("                                                                ")
        time.sleep(3)
        print("       ONE OF THE TWO FOLLOWING ACTIONS IS NEEDED:              ")
        print("                                                                ")
        print("       1- Please execute in the command line: export NWCSAF2ADAGUC_PATH=< your application path>")
        print("                                                                ")
        print("       2- Or copy exim.conf under the directory: " + work_dir)
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
        confFile = pixel_file_path
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
                'PATH': {'inDir': './in_data', 'outDir': './out_data', 'debugInDir': './debug_in_data',
                        'debugOutDir': './debug_out_data' },
                 'LEGEND': {'UPDATE': 'true', 'inDir': './legend', 'outDir':'./legend'}})

    return conf



###########################################################################################################
#  colour assignation and palette loading
###########################################################################################################

def obtain_pallette_p(nc_fid, variable_name, scheme="RGB", alpha=255):
    '''
    :param nc_fid: netcdf Dataset
    :param prod_pal: name of the palette
    :param scheme: RGBA or BRGA
    :return: a palette under array form
    '''

    if 'ci_prob' in variable_name:
        var_pal = 'ci_pal'
    elif 'asii_turb_trop' in variable_name or 'asii_turb_wave_prob' in variable_name:
        var_pal = 'asii_turb_prob_pal'
    elif 'crrph_intensity' in variable_name or 'crrph_accum' in variable_name:
        var_pal = 'crrph_pal'
    elif 'asii_haic_mask' in variable_name:
        var_pal = 'asii_ice_pal'
    else:
        var_pal = variable_name + '_pal'

    varPal = nc_fid.variables[var_pal][:].data

    fill_value_colour = [varPal[-1, 0], varPal[-1, 1], varPal[-1, 2], 0.]

    #  each palette could has diferent lenght filling with [0, 0, 0] not used,
    #  see DOF documents NWC/CDOP3/GEO/AEMET/SW/DOF and NWC/CDOP3/PPS/SMHI/SW/DOF

    palette = []
    # first working with cathegorical variables
    if 'flag_values' in nc_fid.variables[variable_name].ncattrs():
        # working with cathegorical variables
        
        flag_values = nc_fid.variables[variable_name].getncattr('flag_values')
        for i in flag_values:
        # adding transparency removing last black colors [0, 0, 0]
            colour = [varPal[i, 0], varPal[i, 1], varPal[i, 2], alpha]
            palette.append(colour)
        
    else:
        # working with continous variables
        # determining the actual length of the palette.
        # see DOF documents NWC/CDOP3/GEO/AEMET/SW/DOF and NWC/CDOP3/PPS/SMHI/SW/DOF
        for i in reversed(range(255)):
            if (varPal[i, 0] != 0 or varPal[i, 1] != 0 or varPal[i, 2] != 0):
                pallete_actual_length = i
                break
        if variable_name == 'ctth_alti' or variable_name == 'imask_ctth_FL' or variable_name == 'imask_freezing_FL':
            pallete_actual_length = 255
        for i in range(pallete_actual_length + 1):
            # adding transparency 
            colour = [varPal[i, 0], varPal[i, 1], varPal[i, 2], alpha]
            palette.append(colour)
    #  the last element of the palette corresponds to fillValue
    if len(palette) < 256:
        palette.append(fill_value_colour)

    # cmic_phase pallette TB fixed in nwcsaf soft
    if variable_name == 'cmic_phase':
        palette = [[255, 100, 0, 255],
                  [0, 80, 215, 255],
                  [115, 80, 50, 255],
                  [0, 0, 0, 255],
                  [75, 40, 15, 255],
                  [100, 100, 100, 255]]
    # reordering if scheme is BGR
    if scheme == "BGR":
        for i in range(len(palette)):
            palette[i][0], palette[i][1], palette[i][2] = palette[i][2], palette[i][1], palette[i][0]

    np_palette = np.zeros((len(palette), 4))
    for i in range(len(palette)):
        np_palette[i, 0], np_palette[i, 1], np_palette[i, 2], np_palette[i, 3] = palette[i][0], palette[i][1], palette[i][2], palette[i][3]

    if scheme == "HEX":
        colors = []
        for i in range(np_palette.shape[0]):
            B = np.int(np_palette[i, 2])
            G = np.int(np_palette[i, 1])
            R = np.int(np_palette[i, 0])
            colors.append("#{0:02x}{1:02x}{2:02x}".format(R, G, B))
        np_palette = colors


    return np_palette


def update_xml(nc_fid, product, variable_list, conf):

    ncproduct = nc_fid.getncattr('product_name')
    if 'iSHAI' in product:
        product = 'iSHAI'

    header = ('''<?xml version="1.0" encoding="UTF-8" ?>
    <Configuration>
    <CacheDocs enabled="false"/>"
    <!-- Custom styles -->

               ''')

    style_template = ('''<Style name="VARIABLE">
    <Legend fixedclasses="true" tickinterval="10000" tickround="1">VARIABLE</Legend>
    <RenderMethod>nearest</RenderMethod>
    <Min>MIN</Min>
    <Max>MAX</Max>
    <ValueRange min="MIN" max="MAX"/>\n</Style> 
               ''')

    layer_template = ('''\n<Layer  type = "database" >
    <FilePath  filter = "^.*\.nc$">/data/adaguc-autowms/EXIM-PRODUCT/</FilePath>
    <Variable>VARIABLE</Variable>
    <Name>EXIM_PRODUCT_VARIABLE</Name>
    <Styles>VARIABLE</Styles>
    <ImageText>Produced by AEMET running NWCSAF software GEO v2018 version. Displayed under ADAGUC</ImageText>
    </Layer>

              ''')

    closure = ('''  
    <!-- End of configuration /-->
    </Configuration>''')

    body = ''

    for variable_name in variable_list:
        try:
            scale = nc_fid.variables[variable_name].getncattr("scale_factor")
        except:
            scale = 1

        try:
            offset = nc_fid.variables[variable_name].getncattr("add_offset")
        except:
            offset = 0
        # L1SD is an umbrella where store the satellite channels
        if ncproduct == 'L1SD':
            # generating the palette fo L1SD
            pal = []
            for i in reversed(range(240)):
                B = int(255 * i / 239)
                G = int(255 * i / 239)
                R = int(255 * i / 239)
                pal.append("#{0:02x}{1:02x}{2:02x}".format(R, G, B))

            if 'BT' in product:
                minimum = 200
                maximum = 350
            elif 'IR120-RAD' in product:
                minimum = 0
                maximum = 200
            elif 'VIS06-RAD' in product:
                minimum = 0
                maximum = 20
            elif 'WV62-RAD' in product:
                minimum = 0
                maximum = 10
            elif 'REFL' in product:
                minimum = 0
                maximum = 90
                pal = []
                # overwriting the palette
                for i in range(240):
                    B = int(255 * i / 239)
                    G = int(255 * i / 239)
                    R = int(255 * i / 239)
                    pal.append("#{0:02x}{1:02x}{2:02x}".format(R, G, B))
            else:
                minimum = np.nanmin(nc_fid.variables[variable_name][:])
                maximum = np.nanmax(nc_fid.variables[variable_name][:])
                print(product, minimum, maximum)

        else:
            # loading palette from the file
            minimum = nc_fid.variables[variable_name].valid_range[0] * scale + offset
            maximum = nc_fid.variables[variable_name].valid_range[1] * scale + offset
            pal = obtain_pallette_p(nc_fid, variable_name, scheme="HEX")
        # making blacks transparent if asked
        if 'show_black' in conf['XML'].keys():
            if 'a' in conf['XML']['show_black'] or 'A' in conf['XML']['show_black']:  # show black == false
                for i in range(len(pal)):
                    if pal[i] == '#000000':
                        pal[i] = '#00000000'



        nb_intervals = len(pal) - 1

        str_legend = '''\n<Legend name="VARIABLE" type="interval">\n'''

        for index in range(240): # 240 corresponds to the base of the upper triangle on the ADAGUC legend ie maximum val
            index_pal = int(nb_intervals * index / 240)
            str_legend = (str_legend + '''  <palette index="''' + str(index) + '''" color="''' + pal[index_pal] + '''"/>\n''')


        str_legend = str_legend + "</Legend>\n\n"


        os.makedirs(conf['XML']['outDir'], exist_ok=True)
        file = open(conf['XML']['outDir'] + os.sep + 'EXIM-' + product + '.xml', 'w')

        variable_paragraph = str_legend + style_template + layer_template
        variable_paragraph = (variable_paragraph.replace("VARIABLE", variable_name).replace("PRODUCT", product).
                   replace("MIN", str(minimum)).replace("MAX", str(maximum)))
        body = body + variable_paragraph

    content = header + body + closure
    file.write(content)
    file.close()

    return


def related_set(file_015):
    slot = file_015.split('.')[-2].replace('_015', '')
    forecasts = ['', '_015', '_030', '_045', '_060']
    expected_files = [file_015.replace('_015', fcts) for fcts in forecasts]
    origin_product = file_015.split('_')[2]
    expected_files[0] = expected_files[0].replace('EXIM/S', origin_product + '/S')
    return expected_files


def filled_variables_from(src):
    vars = src.variables.keys()

    if 'ci_prob30' in vars:
        variables = ['ci_prob30', 'ci_prob60', 'ci_prob90']
    elif 'asii_turb_trop_prob' in vars:
        variables = ['asii_turb_trop_prob']
    elif 'asii_turb_wave_prob' in vars:
        variables = ['asii_turb_wave_prob']
    elif 'crrph_intensity' in vars:
        variables = ['crrph_intensity', 'crrph_accum', 'crrph_iqf']
    elif 'data' in vars:
        # L1SD product
        variables = ['data']
    elif 'asii_haic_mask' in vars:
        variables = ['asii_haic_mask']
    else:
        variables = [x[:-4] for x in vars if 'pal' in x]

    filled_variables = []
    # ensuring that each variable exists
    for var_to_test in variables:
        try:
            src.variables[var_to_test]
            filled_variables.append(var_to_test)
        except:
            pass
    return filled_variables

def wait_until_set_completed(file_015):

    expected_files = related_set(file_015)
    completed_set = False
    while not completed_set:
        files_are_present = [os.path.exists(f) for f in expected_files]
        completed_set = all(files_are_present)
    existing_files = expected_files
    for f in existing_files:
        srv.wait_until_closed(f)

    return

def process_one_set(file_015, conf, underTM=False):

    wait_until_set_completed(file_015)
    file_set = related_set(file_015)
    src_000 = netCDF4.Dataset(file_set[0], 'r')
    src_015 = netCDF4.Dataset(file_set[1], 'r')
    src_030 = netCDF4.Dataset(file_set[2], 'r')
    src_045 = netCDF4.Dataset(file_set[3], 'r')
    src_060 = netCDF4.Dataset(file_set[4], 'r')
    Main_product = src_015.getncattr('product_name')
    if Main_product !='EXIM':
        # not exim product
        return
    summary = src_015.getncattr('summary')
    if 'Cloud Mask' in summary:
        product = 'CMA'
    elif 'Cloud Microphysics' in summary:
        product = 'CMIC'
    elif 'Cloud Top' in summary:
        product = 'CTTH'
    elif 'Cloud Type' in summary:
        product = 'CT'

    # allows debug option
    if underTM:
        outModDir = conf['PATH']['outDir']
        tempDir = conf['PATH']['tempDir']
    else:
        outModDir = outDir
        tempDir = conf['PATH']['tempDir']
        print('Processing file', file_015)
    output_file_name = file_015.split(os.sep)[-1].replace('_015', '').replace('NWC_', 'NWC_EXIM-')
    output_file = outModDir + os.sep + Main_product + '-' + product + os.sep + output_file_name
    tempFile = tempDir + os.sep + Main_product + os.sep + product + os.sep + output_file_name

    if not underTM:
        print('Writing: ' + tempFile)
        print('Writing: ' + output_file)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    os.makedirs(os.path.dirname(tempFile), exist_ok=True)

    if os.path.isfile(tempFile):
        os.remove(tempFile)

    # under TM running exists the possibility of two processess atempting to write in the same file
    try:
        output_dataset = netCDF4.Dataset(tempFile, 'w', format='NETCDF4')
    except:
        print('Already writing in the file: ', tempFile)
        return
    # we copy all the attributes to the output in a dictionary
    atributtes = {}
    for name_attr in src_015.ncattrs():
        atributtes[name_attr] = src_015.getncattr(name_attr)
    atributtes['history'] = 'original NWCSAF EXIM set of files modified to be compatible with ADAGUC'
    output_dataset.setncatts(atributtes)
    output_dataset.Conventions = 'CF-1.7'
    fc = np.linspace(0, 60, 5)
    # first we test if the imput has the time dimension if not we create it
    # and the variable

    dim_t = output_dataset.createDimension('time', None)
    dim_fct = output_dataset.createDimension('fct', None)

    # we iterate through all the imput dataset dimensions
    # and we recreate them in the output file.

    for name_dimension in src_015.dimensions:
        name = src_015.dimensions[name_dimension].name
        size = src_015.dimensions[name_dimension].size
        output_dataset.createDimension(name, size)

    '''
    Special (one dimension) variables creation: time, forecast, projection_definition, nx and ny
    '''
    var_fct = output_dataset.createVariable('fct', 'int32', ('fct'))
    var_fct.long_name = 'forecast'
    var_fct.units = 'min'
    var_fct[:] = fc
    # Creating the time variable

    var_t = output_dataset.createVariable('time', 'int32', ('time'))
    var_t.calendar = 'proleptic_gregorian'
    var_t.long_name = 'time'
    var_t.units = 'seconds since 1970-01-01 00:00:00'
    try:
        time_string_extended = src_015.getncattr('nominal_product_time')
        time_string = time_string_extended.split('_')[0]
    except:
        print("TIME FAILS IN: ", file_015)
        unformated_time_string = file_015.split('_')[-2].split('.')[0]
        time_string = (unformated_time_string[0:4] + '-' + unformated_time_string[4:6] + '-' + unformated_time_string[6:11] +
                      ':' + unformated_time_string[11:13] + ':' + unformated_time_string[13:])

    output_dataset.setncattr('nominal_product_time', time_string)
    time_striped = time.strptime(time_string, "%Y-%m-%dT%H:%M:%SZ")
    time_epoch = calendar.timegm(time_striped)
    var_t[:] = time_epoch

    # Creating the projection variable
    # Creating the projection variable

    projection = src_015.getncattr('gdal_projection')
    if ' +units=m' not in projection:
        projection = projection.replace(' +units=m', '')

    proj_list = projection.split(' ')
    proj_dict = {}
    for item in proj_list:
        try:
            proj_dict[item.split('=')[0]] = float(item.split('=')[1])
        except:
            proj_dict[item.split('=')[0]] = item.split('=')[1]
    h = proj_dict['+h']

    proj_dict['+a'] = proj_dict['+a'] / h
    proj_dict['+b'] = proj_dict['+b'] / h
    proj_dict['+h'] = 1.0
    projection_rad = ''
    for key in proj_dict.keys():
        projection_rad = projection_rad + key + '=' + str(proj_dict[key]) + ' '

    var_pr = output_dataset.createVariable('projection_definition', 'int32')
    var_pr.proj4 = projection_rad

    # compatibility with other viewers like mcIDAS, wct
    var_pr.grid_mapping_name = 'geostationary'
    var_pr.longitude_of_projection_origin = proj_dict['+lon_0']
    var_pr.latitude_of_projection_origin = 0.0
    var_pr.semi_major_axis = proj_dict['+a'] * h
    var_pr.semi_minor_axis = proj_dict['+b'] * h

    var_pr.perspective_point_height = h

    var_pr.sweep_angle_axis = proj_dict['+sweep']

    # rewriting the global file attributes
    output_dataset.gdal_projection = projection_rad
    output_dataset.gdal_xgeo_up_left = output_dataset.gdal_xgeo_up_left / h
    output_dataset.gdal_ygeo_up_left = output_dataset.gdal_ygeo_up_left / h
    output_dataset.gdal_xgeo_low_right = output_dataset.gdal_xgeo_low_right / h
    output_dataset.gdal_ygeo_low_right = output_dataset.gdal_ygeo_low_right / h
    output_dataset.gdal_geotransform_table = [item / h for item in output_dataset.gdal_geotransform_table]
    # Creating nx and ny variables in radians

    navigation_variables = ['nx', 'ny']
    for name in navigation_variables:
        variable = src_015.variables[name]
        x = output_dataset.createVariable(name, variable.datatype, variable.dimensions)
        # copy variable attributes all at once via dictionary

        output_dataset[name].setncatts(src_015[name].__dict__)
        if name == 'nx':
            output_dataset[name].long_name = 'scanning_x_angle_in_radians'
            output_dataset[
                name].comments = 'attribute standart name to be updated to projection_x_angular_coordinate and units to radian'
            output_dataset[name].axis = 'X'
            output_dataset[name].standard_name = 'projection_x_coordinate'
        else:
            output_dataset[name].long_name = 'scanning_y_angle_in_radians'
            output_dataset[
                name].comments = 'attribute standart name to be updated to projection_y_angular_coordinate and units to radian'
            output_dataset[name].axis = 'Y'
            output_dataset[name].standard_name = 'projection_y_coordinate'
        output_dataset[name].units = ''
        output_dataset[name][:] = src_015[name][:] / h


    '''
    Creating the raster and palette variables.
    Adding the time dimension if needed.
    '''
    toexclude = ['nx', 'ny', 'time', 'projection_definition', 'fct']
    filled_variables = filled_variables_from(src_015)
    # clonning only the bidimensional variables with an additional time dimension
    for name, variable in src_015.variables.items():
        if (name in filled_variables):
            data_000 = src_000[name][:]
            data_015 = src_015[name][:]
            data_030 = src_030[name][:]
            data_045 = src_045[name][:]
            data_060 = src_060[name][:]

            if '_FillValue' in variable.ncattrs():
                x = (output_dataset.createVariable(name, data_015.dtype, ('time', 'fct',) + variable.dimensions, zlib=True,
                                                   fill_value=variable.getncattr('_FillValue')))
                data_015 = ma.masked_where(data_015 == variable.getncattr('_FillValue'), data_015)
            else:
                x = (output_dataset.createVariable(name, variable.datatype, ('time', 'fct',) + variable.dimensions, zlib=True))

            # copy variable attributes all at once via dictionary
            attributes = src_015[name].ncattrs()
            for at in attributes:
                if at != '_FillValue':
                    output_dataset[name].setncatts({at: src_015[name].getncattr(at)})

            output_dataset[name].grid_mapping = 'projection_definition'
            output_dataset[name].coordinates = 'time fct ny nx'
            stacked_data = np.zeros((1, len(var_fct[:]), data_015.shape[0], data_015.shape[1]))
            #packing the data
            stacked_data[0, 0, :, :] = data_000
            stacked_data[0, 1, :, :] = data_015
            stacked_data[0, 2, :, :] = data_030
            stacked_data[0, 3, :, :] = data_045
            stacked_data[0, 4, :, :] = data_060
            # writing the data

            output_dataset[name][:] = stacked_data

    # flushing memory buffer
    output_dataset.close()

    if conf['XML']['UPDATE'] == 'true':
        filled_variables = filled_variables_from(src_015)
        update_xml(src_015, product, filled_variables, conf)

    src_015.close()
    src_030.close()
    src_045.close()
    src_060.close()

    # copying to autowms
    time.sleep(0.1)
    srv.secure_move(tempFile, output_file)
    time.sleep(0.1)

    if not underTM:
        print('Wrote: ' + output_file)
    return


if __name__ == '__main__':
    configuration = readConf()

    if len(sys.argv) == 1:
        # running software without any option, scans the whole inDir and accumulate in in_files
        # all the matches
        inDir = configuration['PATH']['inDir']
        outDir = configuration['PATH']['outDir']
        in_files = []
        # scanning inDir
        for subdir, dirs, files in os.walk(inDir):
            for file in files:
                # storing all the found files in an array
                filepath = subdir + os.sep + file
                if file.endswith("015.nc"):
                    in_files.append(filepath)

    elif len(sys.argv) == 5:
        # meant to execute the script with the following info:
        # <product> <Satellite> <area> < YYYY-MM-DDThh:mm:ssZ>
        # time format YYYY-MM-DDThh:mm:ssZ or YYYYMMDDThhmmssZ
        time_stamp = sys.argv[4].replace(":", "").replace("-", "")
        pixel_current_file = "S_NWC_" + sys.argv[1] + "_" + sys.argv[2] + "_" + sys.argv[3] + "_" + time_stamp + "_015.nc"
        pixel_files = [configuration['PATH']['inDir'] + "/" + pixel_current_file]
        outDir = configuration['PATH']['outDir']

    elif sys.argv[1] == '-h':
        print("       ........................................................")
        print("       Help:")
        print("       TM Usage: python process_exim_to_ADAGUC.py <product> <Satellite> <area> < YYYY-MM-DDThh:mm:ssZ>  ")
        print("       As in:      ")
        print("       python3 process_exim_to_ADAGUC.py CTTH MSG4 Europe-VISIR  2019-02-02T13:00:00Z  ")
        print("       To reach whole in dir recursive processing, run without options: python3 process_exim_to_ADAGUC.py")
        print("       In order to test your platform: python3 process_exim_to_ADAGUC.py -d")
        print("       To reach this help: python3 process_exim_to_ADAGUC.py -h")
        print("       CONFIGURATION IS AVAILABLE IN: exim.conf FILE")
        print("       ........................................................")
        print("       Quiting.")
        quit()

    elif sys.argv[1] == '-d':
        # running with debug option

        print(
            "       WARMING: DEBUGING WITH SAMPLE SET ")
        print("       ........................................................")
        print("       Output file fully readable on: " + configuration['PLATFORM']['viewer'])
        print("       To change the target platform edit exim.conf")
        print("       ........................................................")
        debug_in_File = '/EXIM/S_NWC_CMA_MSG4_AvTbed-VISIR_20180711T083000Z_015.nc'
        inDir = configuration['PATH']['debugInDir']
        outDir = configuration['PATH']['debugOutDir']
        in_files = [inDir + debug_in_File]

    else:
        print("       Unknown option")
        print("       ........................................................")
        print("       TM Usage: python process_exim_to_ADAGUC.py <product> <Satellite> <area> < YYYY-MM-DDThh:mm:ssZ>  ")
        print("       As in:      ")
        print("       python3 process_exim_to_ADAGUC.py CTTH MSG4 Europe-VISIR  2019-02-02T13:00:00Z  ")
        print("       To reach whole in dir recursive processing, run without options: python3 process_exim_to_ADAGUC.py")
        print("       In order to test your platform: python3 process_exim_to_ADAGUC.py -d")
        print("       To reach this help: python3 process_exim_to_ADAGUC.py -h")
        print("       CONFIGURATION IS AVAILABLE IN: exim.conf FILE")
        print("       ........................................................")
        print("       Aborting.")
        quit()

    # processing each detected files, looping through the pixel files in "in_files"
    for file_015 in in_files:

        process_one_set(file_015, configuration)

