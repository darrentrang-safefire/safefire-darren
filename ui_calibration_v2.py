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
from metadata import MetaData

#error code 9: user chose to cancel current operation
#error code 101: warning no meta.data file found during initial startup


pr = cProfile.Profile()
pr.enable()

class CalUI:
    def __init__(self):
        self.log_file =  open('ui_calibration.log', 'a')
        time = misc.now_string()
        self.log_file.write(time + " : Starting UI" + "\n")
        md = MetaData()
        if not md.load():
            self.handle_error("WARNING: No meta.data file found")
        self.md = md

    def run(self):
        self.main_menu()

    def handle_error(self, code):
        #sys.exit(arg) --> arg can be an int or a string
        if type(code) is int and code == 909:
            msg = "meta.data file found with no resume or overwrite flag. delete this file or set resume or overwrite flag."
            print msg
            self.log_file.write(misc.now_string() + " : " + msg + "\n")
        elif type(code) is int and code == 101:
            msg = "No meta.data file detected. Does meta.data file have attribute 'serial'?"
            self.log_file.write(misc.now_string() + " : " + msg + "\n")
        elif type(code) is int and code == 9:
            msg = "User chose to cancel current operation."
            self.log_file.write(misc.now_string() + " : " + msg + "\n")
        if type(code) is str:
            print code
            self.log_file.write(misc.now_string() + " : " + code + "\n")

    def isKeyCompleted(self, key):
        temp_key = key + "s"
        temp_completed_key = key + "s_completed"

        key_list = []
        key_completed = {}

        if hasattr(self.md, temp_key):
            key_list = getattr(self.md, temp_key)
        else:
            sys.exit("key: {0}s not found in metadata".format(temp_key))

        if hasattr(self.md, temp_completed_key):
            key_completed = getattr(self.md, temp_completed_key)
        else:
            return "no completed key"

        if(len(key_completed) < len(key_list)):
            return "continue or overwrite"


        for i in range(len(key_list)):
            found = key_completed.get(key_list[i])
            if found is None:
                return "continue or overwrite"

        return "completed"


    def run_command(self, command):
        command += "\n" #need this because prompt asks for "more?"
        # print r'running command: ', (command.encode('string-escape'))
        process = subprocess.Popen('cmd.exe', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = process.communicate(command)
        if command != '\n':
            process.stdout.flush()
            print stdout

    def pre_calibration(self, input):
        print "doing precalibration stuff"
        # if input >= 1 and input <= 6:
        #     self.run_command("start motor")
        #     self.run_command("start showprogress")
        #     time.sleep(10);

    def get_autocal_info(self, autocal_info):
        camSN = raw_input("Enter Camera Serial Number: ")
        camSN = camSN.upper()
        autocal_info["camSN"] = camSN

    def get_autocal_info_all(self, autocal_info):
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

        if hasattr(self.md, "serial"):
            resume = raw_input("meta.data file detected. Resume/Overwrite or Cancel? (r/o/c): ")
        else:
            self.handle_error(101)

        if resume.upper() == 'R':
            autocal_info["resume"] = True
            autocal_info["overwrite"] = False
        elif resume.upper() == "O":
            autocal_info["resume"] = False
            autocal_info["overwrite"] = True
        elif resume.upper() == "C":
            sys.exit(9)


    def get_autogrid_info(self, autogrid_info):
        overwrite = None
        resume = None

        key = raw_input("Enter key value (from meta.data ie. 'gain' or 'spot'): ").strip()
        completed = self.isKeyCompleted(key)
        if completed == "completed":
            overwrite = raw_input("'{0}s' was already completed. Overwrite? (y/n): ".format(key)).strip()
            if overwrite == "y" or overwrite == "Y":
                overwrite = True
            else:
                overwrite = False
        elif completed == "continue or overwrite":
            choice = raw_input("'{0}s_completed' found partially completed. Resume/Overwrite or Cancel? (r/o/c): ".format(key)).lower().strip()
            if choice == "r":
                resume = True
            elif choice == "o":
                overwrite = True
            elif choice == "c":
                sys.exit(9)
        elif completed == "no completed key":
            #first time running autogrid on this key
            overwrite = None
            resume = None


        autogrid_info['key'] = key
        autogrid_info['resume'] = resume
        autogrid_info['overwrite'] = overwrite

    def get_cookgrid_gain_info(self, cookgrid_info):
        temp_key = raw_input("Enter key value (from meta.data ie. 'gains' or 'spots'): ").strip()
        cookgrid_info['key'] = temp_key

    def get_cookgrid_temp_info(self, cookgrid_info):
        temp_key = raw_input("Enter key value (from meta.data ie. 'gains' or 'spots'): ").strip()
        cookgrid_info['key'] = temp_key


    def main_menu(self):
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
        while True:
            try:
                print menu
                ok = raw_input(prompt)
                if ok == 'q' or ok == 'Q':
                    self.log_file.write("\n" + misc.now_string() + " :" + "Goodbye!" + "\n")
                    print '\nGoodbye!'
                    return False
                ok = int(ok)
                if ok >= 0 and ok <= 7:
                    self.log_file.write(misc.now_string() + " :" + " main menu. user chose: {0}".format(ok) + "\n")

                    if ok == 0:
                        custom_command = raw_input("Enter custom command: ")
                        self.run_command(custom_command);
                    if ok == 1:
                        self.pre_calibration(ok)

                        #autocal -find -ctl ..\example.cal <CamSN>
                        autocal_info = {"cal":"..\example.cal", "camSN": ""}
                        self.get_autocal_info(autocal_info)
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
                        #self.pre_calibration(ok)
                        autocal_info = {"cal": "", "camSN": ""}
                        self.get_autocal_info_all(autocal_info)
                        autocal.autocal(autocal_info["cal"], autocal_info["camSN"], autocal_info["rect"], autocal_info["resume"], autocal_info["overwrite"])
                    if ok == 3:
                        self.pre_calibration(ok)
                        autogrid_info = {"resume": None, "overwrite": None, "key": ""}
                        self.get_autogrid_info(autogrid_info)
                        if len(autogrid_info["key"]) > 0:
                            autogrid.autogrid(autogrid_info['resume'], autogrid_info['overwrite'], autogrid_info["key"])
                        else:
                            print "Error! key is blank."
                    if ok == 4:
                        cookgrid_info = {"key": ""}
                        self.get_cookgrid_gain_info(cookgrid_info)
                        if len(cookgrid_info["key"]) > 0:
                            cookgrid.cookgrid_gain(cookgrid_info['key'])
                        else:
                            print "Error! key is blank."
                    if ok == 5:
                        cookgrid_info = {"key": ""}
                        self.get_cookgrid_temp_info(cookgrid_info)
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
                msg = "Caught RuntimeError in ui_calibration_v2.py"
                err_msg = rte.message
                err_args = rte.args.__str__()
                print msg
                print rte.message
                self.log_file.write(misc.now_string() + " :" + msg + "\n")
                self.log_file.write(misc.now_string() + " :" + err_msg + "\n")
                self.log_file.write(misc.now_string() + " :" + err_args + "\n")
                pass
            except ValueError as ve:
                msg = "Error: Enter numbers only or (q/Q) to quit"
                err_msg = ve.message
                err_args = ve.args.__str__()
                self.log_file.write(misc.now_string() + " :" + msg + "\n")
                self.log_file.write(misc.now_string() + " :" + err_msg + "\n")
                self.log_file.write(misc.now_string() + " :" + err_args + "\n")
                pass
            except SystemExit as e:
                self.handle_error(e.code)
                pass
            except Exception as ex:
                err_msg = ex.message
                err_args = ex.args.__str__()
                print ex.message, ex.code
                self.log_file.write(misc.now_string() + " :" + err_msg + "\n")
                self.log_file.write(misc.now_string() + " :" + err_args + "\n")

    def close_log_file(self):
        self.log_file.close()

def main(args):
    try:
        # bad pixels
        # Firmware updater
        # NIR parameter tweaker
        calui = CalUI()
        calui.run()

        #main_menu(log_file)

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

        calui.close_log_file()


if __name__ == '__main__':
    if main(sys.argv[1:]):
        print __doc__


