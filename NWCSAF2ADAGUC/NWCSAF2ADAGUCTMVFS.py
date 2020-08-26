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

import logging
from logging.handlers import RotatingFileHandler
import multiprocessing
import time
import datetime
import sys
import os
sys.path.append('.')
sys.path.append('./NWCSAF2ADAGUC')

from HRW import nwcpy_hrw_to_csv as hrw
from RDT import nwcpy_rdt_to_geoJSON as rdt
from PIXEL import process_to_ADAGUC as pix
from EXIM import process_exim_to_ADAGUC as exim
from datetime import datetime, timedelta
from multiprocessing import Process
from facilities import services as srv

def readConf():
    '''
    Reads the configuration from the file TM.conf
    :return: a dictionary with the configuration
    '''

    import os
    work_dir = os.getcwd()
    conf = {}
    TM_file_path = ""
    TM_file_path_app = ""

    # scanning working dir and subdirs looking for the TM.conf file
    for name_subdir, name_dirs, all_files in os.walk(work_dir):
        for name_file in all_files:
            if name_file.endswith("TM.conf"):
                TM_file_path = name_subdir + os.sep + name_file
                break
    conf_dir = os.getenv("NWCSAF2ADAGUC_PATH")

    if conf_dir is None:
        conf_dir = work_dir
    for name_subdir, name_dirs, all_files in os.walk(conf_dir):
        for name_file in all_files:
            if name_file.endswith("TM.conf"):
                found_file = name_subdir + os.sep + name_file
                if found_file != TM_file_path:
                        TM_file_path_app = name_subdir + os.sep + name_file
                        break

    if TM_file_path == TM_file_path_app and TM_file_path != "":
        print("       ........................................................")
        print("       ........................................................")
        print("       Running TM under the configuration file: " + TM_file_path)
        print("       To change the the settings please edit TM.conf         ")
        print("       ........................................................")
        print("       ........................................................")

    if TM_file_path != "" and TM_file_path_app == "":
        print("       ........................................................")
        print("       ........................................................")
        print("       Running TM under the configuration file: " + TM_file_path)
        print("       To change the the settings please edit TM.conf         ")
        print("       ........................................................")
        print("       ........................................................")

    if TM_file_path == "" and TM_file_path_app != "":
        print("       ........................................................")
        print("       ........................................................")
        print("       Running TM under the configuration file: " + TM_file_path_app)
        print("       To change the the settings please edit TM.conf         ")
        print("       ........................................................")
        print("       ........................................................")
        TM_file_path = TM_file_path_app

    if TM_file_path != TM_file_path_app and TM_file_path != "" and TM_file_path_app != "":
        print("       ........................................................")
        print("       ........................................................")
        print("       WARMING  WARMING WARMING WARMING WARMING  WARMING WARMING")
        print("       Two configuration files found:                           ")
        print("       First configuration file: " + TM_file_path)
        print("       Second configuration file: " + TM_file_path_app)
        print("       Running TM under the configuration file: " + TM_file_path_app)
        print("       To change the the settings please edit: " + TM_file_path_app)
        print("       ........................................................")
        print("       ........................................................")
        TM_file_path = TM_file_path_app

    if TM_file_path == "" and TM_file_path_app == "":
        print("       ........................................................ ")
        print("       CONFIGURATION NOT FOUND!                                 ")
        print("       ........................................................ ")
        print("                                                                ")
        time.sleep(3)
        print("       ONE OF THE TWO FOLLOWING ACTIONS IS NEEDED:              ")
        print("                                                                ")
        print("       1- Please execute in the command line: export NWCSAF2ADAGUC_PATH=< your application path>")
        print("                                                                ")
        print("       2- Or copy TM.conf under the directory: " + work_dir)
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
        print("                                                             ")
        conf = ({'SETTINGS': {'timeout': '30', 'tone_down_time': '2'},
                 'PATH': {'inDir': './in_data', 'outDir': '/data/adaguc-autowms','ADAGUCdatasets': '/data/adaguc-datasets'},
                 'XML': {'CMA': "['cma_dust.xml', 'cma_volcanic.xml', 'cma_cloudsnow.xml', 'cma_smoke.xml', 'cma.xml']",
                         'CT': "['ct.xml', 'ct_multilayer.xml', 'ct_cumuliform.xml']",
                         'CTTH': "['ctth_pres.xml', 'ctth_effectiv.xml', 'ctth_tempe.xml', 'ctth_alti.xml']",
                         'CMIC': "['cmic_cot.xml',  'cmic_iwp.xml', 'cmic_lwp.xml', 'cmic_reff.xml', 'cmic_phase.xml']",
                         'PC': "['pc.xml']", 'PC-Ph': "['pcph.xml']",
                         'CRR': "['crr.xml', 'crr_intensity.xml']",
                         'CRR-Ph': "['crrph_accum.xml', 'crrph_iqf.xml', 'crrph_intensity.xml']",
                         'RDT-CW': "['RDT_MAIN.xml']",
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


def poll(paths):
    detected_files = set()

    for path in paths:
        yesterday = datetime.now() - timedelta(days=1)
        today = datetime.now()
        today_path = path + os.sep + str(today.timetuple().tm_year) + format(today.timetuple().tm_yday, '03')
        yesterday_path = path + os.sep + str(yesterday.timetuple().tm_year) + format(yesterday.timetuple().tm_yday, '03')


        if os.path.isdir(yesterday_path):
            path_list = [yesterday_path, today_path]
        else:
            path_list = [path]

        for day_path in path_list:
            for name_subdir, name_dirs, all_files in os.walk(day_path):
                for name_file in all_files:
                    file_to_add = name_subdir + os.sep + name_file
                    # avoiding hided or temporary files
                    if file_to_add.startswith('.'):
                        pass
                    else:
                        detected_files.add(file_to_add)

    return detected_files


def process_file(file):

    if 'HRW' in file and file.endswith('Z.nc') and 'NWC' in file:
        log.info(file + ' assumed as HRW product')
        time.sleep(tone_down_time)
        p = Process(target=hrw.process_one_file, args=(file, hrwConf, True,))
        p.start()
        proc_dict[p.pid] = [time.time(), p, file]
        time.sleep(tone_down_time)
    elif 'RDT' in file and file.endswith('Z.nc') and 'NWC' in file:
        log.info(file + ' assumed as RDT product')
        time.sleep(tone_down_time)
        p = Process(target=rdt.process_one_set, args=(file, rdtConf, True,))
        p.start()
        proc_dict[p.pid] = [time.time(), p, file]
        time.sleep(tone_down_time)
    elif 'EXIM' in file and file.endswith('Z_015.nc') and 'NWC' in file:
        log.info(file + ' assumed as EXIM product')
        time.sleep(tone_down_time)
        p = Process(target=exim.process_one_set, args=(file, eximConf, True,))
        p.start()
        proc_dict[p.pid] = [time.time(), p, file]
        time.sleep(tone_down_time)
    elif 'RDT' not in file and 'HRW' not in file and file.endswith('Z.nc') and 'NWC' in file:
        log.info(file + ' assumed as pixel product')
        time.sleep(tone_down_time)
        p = Process(target=pix.process_one_file, args=(file, pixConf, True,))
        p.start()
        proc_dict[p.pid] = [time.time(), p, file]
        time.sleep(tone_down_time)

    else:
        log.info('New item: ' + file + ' not recognized.')
        #print(file)
    return


def add_new_file_created(file_name):
    '''
    Filters the file names only process files ended with Z.nc, , avoiding locks and temporary files
    :param file_name: file  to test
    :return:
    '''

    if (file_name.endswith('Z.nc') or
            file_name.endswith('.h5') or
            file_name.endswith('.bufr') or
            file_name.endswith('.txt') or
            file_name.endswith('.csv') or
            (('EXIM' in file_name) and file_name.endswith('Z_015.nc'))):
        to_do_files.append(file_name)
    return


def compare(past_set, foo, now_set):
    new_elements = now_set - past_set
    #print(new_elements)
    for file_name in new_elements:
        add_new_file_created(file_name)
        log.info(" File: " + file_name + " added.")
    return


if __name__ == '__main__':

    try:
        os.remove('TM.stop')
    except OSError:
        pass

    f = open('TM.howTo.stop', 'w')
    f.write(' TO STOP THE TM change the name of this file to: TM.stop ')
    f.close()

    log_name = 'NWCSAF2ADAGUC.log'
    logging.basicConfig(filename=log_name, level=logging.INFO)
    log = logging.getLogger()
    if (log.hasHandlers()):
        log.handlers.clear()
        
    handler = RotatingFileHandler(log_name, maxBytes=500 * 1024, backupCount=1)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    conf = readConf()
    hrwConf = hrw.readHrwConf()
    rdtConf = rdt.readRdtConf()
    pixConf = pix.readConf()
    eximConf = exim.readConf()
    timeout = int(conf['SETTINGS']['timeout'])
    # path = conf['PATH']['inDir']
    # loading the set of paths TM.conf
    paths = (conf['PATH']['inDir'].replace('[', '').replace(']', '').
                 replace("""'""", '').
                 replace(' ', '').
                 split(','))
    tone_down_time = float(conf['SETTINGS']['tone_down_time'])
    past_files = poll(paths)
    to_do_files = []
    proc_dict = {}

    try:
        while not os.path.isfile('TM.stop'):

            time.sleep(1)
            # launching processes if allowed
            # reading the current active files
            now_files = poll(paths)

            compare(past_files, "with", now_files)
            #print(to_do_files)
            past_files = now_files
            doing_files = [proc_dict[key][2] for key in proc_dict.keys()]
            num_active_proc = len(doing_files)
            max_active_proc = 1  # max(multiprocessing.cpu_count() - 2, 1)
            while num_active_proc < max_active_proc:
                if len(to_do_files) > 0:
                    if 'RDT' in to_do_files[0]:
                        to_do_files.reverse()
                    # launching the first file from the to_do list
                    file_to_send = to_do_files[0]
                    del to_do_files[0]
                    process_file(file_to_send)
                    num_active_proc = num_active_proc + 1
                else:
                    break

            # checking and refreshing processes status
            stopped = []
            timed_out = []

            for proc_pid in proc_dict.keys():
                init_time = proc_dict[proc_pid][0]
                proc = proc_dict[proc_pid][1]

                if not proc.is_alive():
                    stopped.append(proc_pid)

                if (time.time() - init_time) > timeout and proc_pid not in stopped:
                    timed_out.append(proc_pid)

            # cleaning ended processes from active process list
            for stopped_proc in stopped:
                log.info("\nProcess " + str(stopped_proc) +
                         " stopped, removing from active process list, corresponds to the file: "
                         + proc_dict[stopped_proc][2] +
                         " \n")
                stopped_file_name = proc_dict[stopped_proc][2]
                srv.wait_until_unlocked(stopped_file_name)
                product_name = stopped_file_name.split(os.sep)[-1].split('_')[2]

                # and updating the ADAGUC db
                os.sync()
                time.sleep(10 * tone_down_time)
                # removing the stopped process from the proc dictionary
                del (proc_dict[stopped_proc])
                log.info("\n Active processes list updated \n")
            # killing timed_out processes
            for hanged_proc in timed_out:
                proc_dict[hanged_proc][1].terminate()
                log.info("Process " + str(hanged_proc) +
                         " hanged, killing and removing from active process list, file: " + proc_dict[hanged_proc][2])
                del (proc_dict[hanged_proc])
                log.info("\n Active processes list updated \n")
    except KeyboardInterrupt:
        pass
