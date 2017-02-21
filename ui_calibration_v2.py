import sys
import imp
import string
import os
import time
import ConfigParser
import datetime
import subprocess
import cProfile
import re
import pstats
import StringIO

import autocal
import autogrid
import cookgrid
import metamap
import misc


pr = cProfile.Profile()
pr.enable()


def run_command(command):
    command += "\n" #need this because prompt asks for "more?"
    # print r'running command: ', (command.encode('string-escape'))
    process = subprocess.Popen('cmd.exe', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, stderr = process.communicate(command)
    if command != '\n':
        process.stdout.flush()
        print stdout

def pre_calibration(input):
    if input >= 1 and input <= 6:
        run_command("start motor")
        run_command("start showprogress")
        time.sleep(10);

def get_autocal_info(autocal_info):
    camSN = raw_input("Enter Camera Serial Number: ")
    camSN = camSN.upper()
    autocal_info["camSN"] = camSN

def get_autocal_info_all(autocal_info):
    camSN = raw_input("Enter Camera Serial Number: ")
    camSN = camSN.upper()
    autocal_info["camSN"] = camSN

    cal = raw_input("Enter path to .cal file: ")
    autocal_info["cal"] = cal

    while True:
        try:
            rectFlag = raw_input("Do you want to specify rectangle coordinates? (y/n): ")
            if rectFlag.upper() == 'Y':
                rect_l = raw_input("Enter left value of rect: ")
                rect_r = raw_input("Enter right value of rect: ")
                rect_t = raw_input("Enter top value of rect: ")
                rect_b = raw_input("Enter bottom value of rect: ")
                rect = [] #left, top, right, bottom
                rect.append(int(rect_l))
                rect.append(int(rect_t))
                rect.append(int(rect_r))
                rect.append(int(rect_b))
                autocal_info["rect"] = misc.rect4(rect)
                break
            else:
                autocal_info["rect"] = None
                break
        except ValueError as ve:
            print "Error: Enter numbers only"
            print ve.message
            pass


    resume = raw_input("Do you want to resume or overwrite? (r/o/n for neither): ")
    if resume.upper() == 'R':
        autocal_info["resume"] = True
        autocal_info["overwrite"] = False
    elif resume.upper() == "O":
        autocal_info["resume"] = False
        autocal_info["overwrite"] = True
    else:
        autocal_info["resume"] = False
        autocal_info["overwrite"] = False


def get_autogrid_info(autogrid_info):
    resume = raw_input("Resume? (y/n): ").strip()
    if resume == "y" or resume == "Y":
        resume = True
    else:
        resume = False

    overwrite = raw_input("Overwrite? (y/n): ").strip()
    if overwrite == "y" or overwrite == "Y":
        overwrite = True
    else:
        overwrite = False

    key = raw_input("Enter key value (from meta.data): ").strip()

    autogrid_info['key'] = key
    autogrid_info['resume'] = resume
    autogrid_info['overwrite'] = overwrite

def get_cookgrid_gain_info(cookgrid_info):
    temp_key = raw_input("Enter key value (from meta.data): ").strip()
    cookgrid_info['key'] = temp_key

def get_cookgrid_temp_info(cookgrid_info):
    temp_key = raw_input("Enter key value (from meta.data): ").strip()
    cookgrid_info['key'] = temp_key

def handle_error(code):
    #sys.exit(arg) --> arg can be an int or a string
    if type(code) is int and code == 909:
        print "meta.data file found with no resume or overwrite flag. delete this file or set resume or overwrite flag."
    if type(code) is str:
        print code

def main_menu():
    menu = '******************************************\n'
    menu += '* Choose command to run:                 *\n'
    menu += '* 1. Full Calibration                    *\n'
    menu += '* 2. Autocal                             *\n'
    menu += '* 3. Autogrid                            *\n'
    menu += '* 4. Cookgrid Gains                      *\n'
    menu += '* 5. Cookgrid Temp                       *\n'
    menu += '* 6. Make Metamap                        *\n'
    menu += '* 7. Exit                                *\n'
    menu += '*                                        *\n'
    menu += '* 0. Custom Command                      *\n'
    menu += '******************************************'
    prompt = '*>>> '
    errorlevel = None
    starting_point = 0
    while True:
        try:
            print menu
            ok = raw_input(prompt)
            if ok == 'q' or ok == 'Q':
                print '\nGoodbye!'
                return False
            ok = int(ok)
            if ok >= 0 and ok <= 7:

                if ok == 0:
                    custom_command = raw_input("Enter custom command: ")
                    run_command(custom_command);
                if ok == 1:
                    pre_calibration(ok)

                    #autocal -find -ctl ..\example.cal <CamSN>
                    autocal_info = {"cal":"..\example.cal", "camSN": ""}
                    get_autocal_info(autocal_info)
                    autocal.autocal(autocal_info["cal"], autocal_info["camSN"], rect=None, resume=None, overwrite=None)

                    #autogrid gain
                    autogrid_gain_info = {"resume":None, "overwrite":None, "key":"gain"}
                    autogrid.autogrid(autogrid_gain_info['resume'], autogrid_gain_info['overwrite'], autogrid_gain_info["key"])

                    #cookgrid -gain gains
                    cookgrid_info = {"key":"gains"}
                    cookgrid.cookgrid_gain(cookgrid_info['key'])

                    #autogrid spot
                    autogrid_spot_info = {"resume":None, "overwrite":None, "key":"spot"}
                    autogrid.autogrid(autogrid_spot_info['resume'], autogrid_spot_info['overwrite'], autogrid_spot_info["key"])

                    #metamap make
                    metamap.makeMetaMap()

                    #cookgrid -temp spots
                    cookgrid_info = {"key":"spots"}
                    cookgrid.cookgrid_temp(cookgrid_info['key'])
                if ok == 2:
                    pre_calibration(ok)
                    autocal_info = {"cal": "", "camSN": ""}
                    get_autocal_info_all(autocal_info)
                    autocal.autocal(autocal_info["cal"], autocal_info["camSN"], autocal_info["rect"], autocal_info["resume"], autocal_info["overwrite"])
                if ok == 3:
                    pre_calibration(ok)
                    autogrid_info = {"resume": None, "overwrite": None, "key": ""}
                    get_autogrid_info(autogrid_info)
                    if len(autogrid_info["key"]) > 0:
                        autogrid.autogrid(autogrid_info['resume'], autogrid_info['overwrite'], autogrid_info["key"])
                    else:
                        print "Error! key is blank."
                if ok == 4:
                    cookgrid_info = {"key": ""}
                    get_cookgrid_gain_info(cookgrid_info)
                    if len(cookgrid_info["key"]) > 0:
                        cookgrid.cookgrid_gain(cookgrid_info['key'])
                    else:
                        print "Error! key is blank."
                if ok == 5:
                    cookgrid_info = {"key": ""}
                    get_cookgrid_temp_info(cookgrid_info)
                    if len(cookgrid_info["key"]) > 0:
                        cookgrid.cookgrid_temp(cookgrid_info['key'])
                    else:
                        print "Error! key is blank."
                if ok == 6:
                    metamap.makeMetaMap()

                if ok == 7:
                    print '\nGoodbye!'
                    return False
            else:
                print "Error: Please pick 0-7 only"
        except RuntimeError as rte:
            print "Caught RuntimeError in ui_calibration_v2.py"
            print rte.message
            print rte.args
            pass
        except ValueError as ve:
            print "Error: Enter numbers only or (q/Q) to quit"
            print ve.message
            pass
        except SystemExit as e:
            handle_error(e.code)
            pass
        except Exception as ex:
            print ex.message, ex.code


def main(args):
    try:
        # bad pixels
        # Firmware updater
        # NIR parameter tweaker

        main_menu()

        # autogrid.autogrid(resume=None, overwrite=None, key="gain")
        # cookgrid.cookgain("gains")

        # spackle & hotspot fix

        # autogrid.autogrid(resume=None, overwrite=None, key="spot")
        # metamap.makeMetaMap()
        # cookgrid.cooktemps("spots")

        # checkspots

    finally:
        pr.disable()
        s = StringIO.StringIO()
        ps = pstats.Stats(pr, stream=s).strip_dirs()
        ps.sort_stats('cumtime')
        ps.print_stats()
        print s.getvalue()

        s2 = StringIO.StringIO()
        ps2 = pstats.Stats(pr, stream=s2).strip_dirs()
        ps2.sort_stats('calls')
        ps2.print_stats()

        file = open('statistics_info.log', 'w')
        file.write(s.getvalue())
        file.write('\n\n\n')
        file.write(s2.getvalue())


if __name__ == '__main__':
    if main(sys.argv[1:]):
        print __doc__


