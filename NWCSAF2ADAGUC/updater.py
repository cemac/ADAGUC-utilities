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
import numpy as np
import time
import calendar
import sys
import os
import re
sys.path.append('.')


def readConf():
    '''
    Reads the configuration from the file TM.conf
    :return: a dictionary with the configuration
    '''
    conf = {}
    work_dir = os.getcwd()

    conf_dir = os.getenv("NWCSAF2ADAGUC_PATH")

    if conf_dir is None:
        conf_dir = work_dir

    TM_file_path = conf_dir + os.sep + "TM.conf"

    try:
        confFile = TM_file_path
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

        conf = ({'SETTINGS': {'timeout': '300', 'tone_down_time': '2',  'slotsToKeep': '500', 'rdtSlotsToKeep': '450'},
                 'PATH': {'inDir': './in_data', 'outDir': '/data/adaguc-autowms',
                          'ADAGUCdatasets': '/data/adaguc-datasets'},
                 'XML': {'CMA': "['cma_dust.xml', 'cma_volcanic.xml', 'cma_cloudsnow.xml', 'cma_smoke.xml', 'cma.xml']",
                         'CT': "['ct.xml', 'ct_multilayer.xml', 'ct_cumuliform.xml']",
                         'CTTH': "['ctth_pres.xml', 'ctth_effectiv.xml', 'ctth_tempe.xml', 'ctth_alti.xml']",
                         'CMIC': "['cmic_cot.xml',  'cmic_iwp.xml', 'cmic_lwp.xml', 'cmic_reff.xml', 'cmic_phase.xml']",
                         'PC': "['pc.xml']", 'PC-Ph': "['pcph.xml']",
                         'CRR': "['crr.xml', 'crr_intensity.xml']",
                         'CRR-Ph': "['crrph_accum.xml', 'crrph_iqf.xml', 'crrph_intensity.xml']",
                         'RDT-CW': "['RDT_NOW.xml']",
                         'CI': "['ci_prob90.xml', 'ci_prob60.xml', 'ci_prob30.xml']",
                         'iSHAI': "['IR_band', 'ishai_diffshw.xml', 'ishai_diffli.xml', 'ishai_diffbl.xml',"
                                  " 'ishai_ki.xml', 'ishai_diffki.xml', 'ishai_diffhl.xml', 'ishai_difftoz.xml',"
                                  " 'ishai_li.xml', 'ishai_hl.xml', 'ishai_toz.xml', 'ishai_shw.xml',"
                                  " 'ishai_residual.xml', 'ishai_diffskt.xml', 'ishai_ml.xml', 'ishai_tpw.xml',"
                                  " 'ishai_skt.xml', 'ishai_bl.xml', 'ishai_diffml.xml', 'ishai_difftpw.xml']",
                         'ASII-GW': "['asii_turb_wave_prob.xml']",
                         'ASII-TF': "['asii_turb_trop_prob.xml']",
                         'HRW': "['PL500_PL400HRW.xml', 'FL50_FL100HRW.xml', 'PL400_PL300HRW.xml', 'PL200_PL100HRW.xml',"
                                " 'HRW.xml', 'FL200_FL250HRW.xml', 'FL400_FL450HRW.xml', 'PL800_PL700HRW.xml',"
                                " 'FL350_FL400HRW.xml', 'PL600_PL500HRW.xml', 'FL450_FL500HRW.xml', 'PL900_PL800HRW.xml',"
                                " 'FL100_FL150HRW.xml', 'FL300_FL350HRW.xml', 'FL250_FL300HRW.xml', 'FL0_FL50HRW.xml',"
                                " 'FL500_FL550HRW.xml', 'FL150_FL200HRW.xml', 'PL300_PL200HRW.xml',"
                                " 'PL1000_PL900HRW.xml', 'PL700_PL600HRW.xml']",
                         'L1SD': "['data.xml']"}})

    return conf


def update_db(product_name, conf):
    app_dir = os.getenv("NWCSAF2ADAGUC_PATH")
    if app_dir is None:
        app_dir = os.sep + "home" + os.sep + os.getenv("USER") 
    lock_name = app_dir + os.sep + "NWCSAFADAGUC" + os.sep + "blocked.by.dbupdt"

    while os.path.isfile(lock_name):
        f = open(lock_name, 'r')
        lines = f.readlines()
        exec_local_time = calendar.timegm(time.strptime(time.asctime()))
        lock_local_time = calendar.timegm(time.strptime(lines[1]))
        if exec_local_time - lock_local_time > 30:
            break
        time.sleep(0.5)
    os.makedirs(os.path.dirname(lock_name), exist_ok=True)
    f = open(lock_name, 'w')
    f.write(' blocked by: ' + product_name + '\n')
    f.write(time.asctime())
    f.close()
    os.sync()
    # updating the ADAGUC db

    os.environ["ADAGUC_TMP"] = "/tmp"
    os.environ["ADAGUC_PATH"] = "/src/KNMI/adaguc-server/"

    # loading xml file names from the configuration TM.conf
    xml_files = (conf['XML'][product_name].replace('[', '').replace(']', '').
                 replace("""'""", '').
                 replace(' ', '').
                 split(','))
    # removing from the filter list the filters non present in adaguc-dataset
    xml_files = [xml for xml in xml_files if os.path.isfile(conf['PATH']['ADAGUCdatasets'] + os.sep + xml)]
    # updating for each xml file present in adaguc-dataset
    for xml in xml_files:
        #print(conf['PATH']['ADAGUCdatasets'] + os.sep + xml)
        redirected_stdout_to = " > adaguc.log"
        order = (
                    '/src/KNMI/adaguc-server/bin/adagucserver --updatedb --config /src/KNMI/adaguc-server/data/config/adaguc.vm.xml,' +
                    xml + redirected_stdout_to)
        os.system(order)

        # ensuring one by one update of the database
        while True:
            adaguc_log_file = open('adaguc.log', 'r')
            content = adaguc_log_file.read()
            if "***** Finished DB Update *****" in content or 'errors *****' in content:
                time.sleep(tone_down_time)
                if ('RDT' in product_name) or ('HRW' in product_name):
                    time.sleep(tone_down_time)
                break
            time.sleep(tone_down_time)
        os.sync()
    try:
        os.remove(lock_name)
        os.sync()
    except OSError:
        pass
    
    return

def clean(product_name, TM_conf):
    '''
    :param product_name:
    :param TM_conf:
    :return: True.
    '''

    done = False
    to_clean_dir = TM_conf['PATH']['outDir'] + os.sep + product_name
    products = set()

    for name_subdir, name_dirs, all_files in os.walk(to_clean_dir):
        for name_file in all_files:
            dir_to_add = os.path.dirname(name_subdir + os.sep + name_file)
            products.add(dir_to_add)

    for subdir_to_clean in products:
        for name_subdir, name_dirs, all_files in os.walk(subdir_to_clean):
            files_with_time = []
            for i in range(len(all_files)):

                try:
                    time_string = re.search('[0,1,2,3,4,5,6,7,8,9]*T[0,1,2,3,4,5,6,7,8,9,.]*Z', all_files[i]).group()
                    formatted_time_string = (time_string[0:4] + '-' + time_string[4:6] + '-' + time_string[6:11] +
                                             ':' + time_string[11:13] + ':' + time_string[13:15] + 'Z')
                    struct_time = time.strptime(formatted_time_string, '%Y-%m-%dT%H:%M:%SZ')

                    files_with_time = files_with_time + [[calendar.timegm(struct_time), name_subdir + os.sep + all_files[i]]]
                except:
                    # anomalous file detected (with the time not set in the name)
                    erroneous_file = name_subdir + os.sep + all_files[i]
                    os.remove(erroneous_file)

            files_with_time = np.array(files_with_time)
            
            files_with_time = np.sort(files_with_time, axis=0)
            nb_slots_to_keep = int(TM_conf['SETTINGS']['slotsToKeep'])
            if ('RDT' in product_name) or ('HRW' in product_name):
                nb_slots_to_keep = int(TM_conf['SETTINGS']['rdtSlotsToKeep'])
            files_to_erase = files_with_time[0:-nb_slots_to_keep, :]
            remaining_files = files_with_time[-nb_slots_to_keep:, :]

            for name_of_file_to_erase in files_to_erase[:, 1]:
                try:
                    moved_file = (TM_conf['PATH']['outDir'].replace('adaguc-autowms', '')
                                  + 'TRASH' + os.sep + os.path.basename(name_of_file_to_erase))
                    os.makedirs(os.path.dirname(moved_file), exist_ok=True)
                    os.system('mv ' + name_of_file_to_erase + ' ' + moved_file)
                    os.system('rm ' + moved_file)
                    os.sync()
                    done = True
                except OSError:
                    pass

            os.rename(remaining_files[0, 1], remaining_files[0, 1].replace('hide', ''))
            # forcing the database update if not file has been erased.
            if not done:
                try:
                    if 'hide' in remaining_files[1, 1]:
                        os.rename(remaining_files[1, 1], remaining_files[1, 1].replace('hide', ''))
                        os.rename(remaining_files[2, 1], remaining_files[2, 1] + 'hide')
                    else:
                        os.rename(remaining_files[1, 1], remaining_files[1, 1] + 'hide')
                        os.rename(remaining_files[2, 1], remaining_files[2, 1].replace('hide', ''))
                except:
                    pass

    done = True
    return done


if __name__ == '__main__':
    TM_conf = readConf()
    dir_to_clean = TM_conf['PATH']['outDir']
    tone_down_time = float(TM_conf['SETTINGS']['tone_down_time'])
    products = set()

    for name_subdir, name_dirs, all_files in os.walk(dir_to_clean):
        name_subdir = name_subdir.replace(dir_to_clean, '')
        dir_list = name_subdir.split(os.sep)
        if len(dir_list) > 1:
            # avoiding to process non configured dirs or static dirs
            if dir_list[1] in TM_conf['XML'].keys():
                products.add(dir_list[1])

    for product in products:
        file_has_been_cleaned_in_current_exec = clean(product, TM_conf)

        if file_has_been_cleaned_in_current_exec:
            os.sync()
            time.sleep(tone_down_time)
            update_db(product, TM_conf)

