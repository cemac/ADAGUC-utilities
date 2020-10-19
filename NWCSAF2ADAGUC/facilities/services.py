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
import os
import time
import netCDF4
import calendar

def wait_until_closed(inputFile):

    #print("----")
    # test1: this test is meant to give meaningfull results when netcdf files are produced locally
    while True:
        try:
            src = netCDF4.Dataset(inputFile, 'r')
            src.close()
            break
        except:
            time.sleep(0.2)
    # test1 passed

    #print('1')
    # test2: this test is meant to locate temporary files
    temporary_file = os.path.dirname(inputFile) + os.sep + '.' + os.path.basename(inputFile)
    while os.path.isfile(temporary_file):
        time.sleep(0.2)
    # test2 passed
    #print('2')

    # test3: this test is meant to detect if file is growing
    while True:
        source_size0 = os.path.getsize(inputFile)
        time.sleep(0.1)
        source_size1 = os.path.getsize(inputFile)
        if source_size1 == source_size0:
            break
    # test3 passed
    #print('3')

    return

def lock_file(file_name, conf=None):

    if 'RDT-CW' in file_name:
        product_name = 'RDT-CW'
    elif 'HRW' in file_name:
        product_name = 'HRW'
    else:
        product_name = file_name.split(os.sep)[-1].split('_')[2]
    if conf is not None:
        lock_dir = conf['PATH']['tempDir']
    else:
        lock_dir = '/data/adaguc-autowms'
    lock = lock_dir + os.sep + product_name  + os.sep + product_name + '.locked'

    return lock

def secure_copy(source, dest, conf=None):
    '''
    copies source to dest and generates a lock that indicates that the copy is still ongoing, when the copy is finished
    the lock is removed.
    :param source: source file with path
    :param dest: destination file with path
    :return: None
    '''

    if not os.path.exists(source):
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    lock = lock_file(dest, conf)

    locking_file = open(lock, 'w')
    locking_file.close()

    os.system('cp ' + source + ' ' + dest + '.tmp')
    os.sync()
    os.system('mv ' + dest + '.tmp' + ' ' + dest)
    os.sync()

    try:
        os.remove(lock)
    except:
        pass
    return None


def secure_move(source, dest, conf=None):
    '''
    moves source to dest and generates a lock indicating that the moving is still ongoing, when the process
     is finished the lock is removed.
    :param source: source file with path
    :param dest: destination file with path
    :return: None
    '''

    if not os.path.exists(source):
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    lock = lock_file(dest, conf)
    #print(lock,"<<<<<")
    locking_file = open(lock, 'w')
    locking_file.close()
    os.system('mv ' + source + ' ' + dest + '.tmp')
    os.sync()
    os.system('mv ' + dest + '.tmp' + ' ' + dest)
    os.sync()

    try:
        os.remove(lock)
    except:
        pass
    return None


def is_locked(file_name, conf=None):
    '''
    check if a file is locked
    :param file_name: a string with the file name and the path
    :return: boolean telling if the file is locked or not
    '''
    lock = lock_file(file_name, conf)

    if os.path.exists(lock):
        locked = True
    else:
        locked = False
    return locked


def wait_until_unlocked(file_name, conf=None):
    '''
    Waits until the file is unlocked
    :param file_name: a string with the file name and the path
    :return: None
    '''

    while is_locked(file_name, conf):
        time.sleep(1)

    return None


if __name__ == '__main__':
    pass
