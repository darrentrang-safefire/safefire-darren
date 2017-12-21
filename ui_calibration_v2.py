#now writing to master to create a merge conflict
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
import autocalx
from metadata import MetaData
import misc
from misc import PushDir
import checkspots
import badpixels

#error code 9: user chose to cancel current operation
#error code 101: warning no meta.data file found during initial startup

#running full calibration from main menu requirements:
#   example.cal must be located 1 directory back (../example.cal)
#   use default keys "gain" and "spot", do not prompt to ask
#   only thing asked for is the cam SN
#   THIS IS LIKE THIS SO THAT THE USER CAN KICK IT OFF AND COME BACK WHEN ITS DONE

#running start calibration from... from main menu requirements:
#   example.cal must be located 1 directory back (../example.cal)
#   use default keys "gain" and "spot", do not prompt to ask
#   only thing asked for is cam SN (IF USER ENTERED 1 IN SUB MENU)
#   THIS IS LIKE THIS SO THAT THE USER CAN KICK IT OFF AND COME BACK WHEN ITS DONE

# meta.data checks only occur when doing single commands from main menu

#file structure must be
# /camera SN
#       /cal40C     ---> meta.data and cal files stored in here
#       example.cal ---> this file must be here for autocal

#ask for path to /camSN user wants to work out of. look for meta.data in /camSN/cal40C/. doesnt matter if path
#ends with a "/" or not. path is not case sensitive


FOLDER_STRUCTURE = "/cal40C"
EXAMPLE_CAL = "example.cal"
NAS_BACKUP = "M:\\darren\\test backup dir"

pr = cProfile.Profile()
pr.enable()

class CalUI:
    def __init__(self):
        self.cal_path = self.get_working_directory()

        self.log_file = open(os.path.join(self.cal_path, 'ui_calibration.log'), 'a')
        self.log("\n\nStarting UI")
        self.log("working directory set to {0}".format(self.cal_path))

        self.md_path = self.cal_path + FOLDER_STRUCTURE
        self.load_md(self.md_path)

    def stop_profile(self, pr, logfile, append=False):
        pr.disable()
        s = StringIO.StringIO()
        ps = pstats.Stats(pr, stream=s).strip_dirs()
        ps.sort_stats('cumtime')
        ps.print_stats()
        #print s.getvalue()
        if append is True:
            file = open(os.path.join(self.md_path, logfile), 'a')
        else:
            file = open(os.path.join(self.md_path, logfile), 'w')
        file.write(s.getvalue())

    def get_working_directory(self):
        wd = ""
        while (True):
            wd = raw_input("Enter the path to cameraSN (ie. C:/safefire/X800000): ")
            #strip trailing / or \ if provided
            if wd[len(wd)-1] == "/" or wd[len(wd)-1] == "\\":
                wd = wd[:len(wd)-1]
            if not os.path.exists(wd):
                print "Could not find path {0}. Please try again.".format(wd)
            else:
                wd_cal40c = wd + FOLDER_STRUCTURE
                if not os.path.exists(wd_cal40c):
                    prompt = "Folder cal40C not found in {0}. Would you like to make one? (y/n): ".format(wd)
                    yorn = raw_input(prompt)
                    if yorn.lower() == 'y':
                        os.mkdir(wd_cal40c)
                        break
                    else:
                        print "Could not find directory cal40C in {0}. Please try again.".format(wd)
                else:
                    break
        return wd

    def load_md(self, path):
        self.log("Attempting to load meta data")
        md = MetaData()

        if os.path.isfile(os.path.join(path, "meta.data")):
            md.load_from_dir(path)
            print "meta.data successfully loaded from {0}".format(path)
            self.log("meta.data successfully loaded from {0}".format(path))
        else:
            self.handle_error("WARNING: No meta.data file found in {0}".format(path))

        self.md = md

    def log(self, msg):
        time = misc.now_string()
        self.log_file.write(time + " : " + msg + "\n")

    def run(self):
        time.sleep(.3)
        self.main_menu()

    def handle_error(self, code):
        #sys.exit(arg) --> arg can be an int or a string
        if type(code) is int and code == 909:
            msg = "meta.data file found with no resume or overwrite flag. delete this file or set resume or overwrite flag."
            print msg
            self.log(msg)
        elif type(code) is int and code == 101:
            msg = "No meta.data file detected. If this is the first time running Autocal, ignore this message. Does meta.data file have attribute 'serial'?"
            self.log(msg)
        elif type(code) is int and code == 9:
            msg = "User chose to cancel current operation."
            self.log(msg)
        if type(code) is str:
            print code
            self.log(code)

    def isKeyCompleted(self, key):
        temp_key = key + "s"
        temp_completed_key = key + "s_completed"

        key_list = []
        key_completed = {}

        if hasattr(self.md, temp_key):
            key_list = getattr(self.md, temp_key)
        else:
            sys.exit("key: {0} not found in metadata".format(temp_key))

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


    def run_command(self, command, prnt=True):
        self.log("attempting to run custom command: {0}".format(command))
        command += "\n" #need this because prompt asks for "more?"
        # print r'running command: ', (command.encode('string-escape'))
        process = subprocess.Popen('cmd.exe', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = process.communicate(command)
        if command != '\n':
            self.log("custom command success")
            if prnt:
                process.stdout.flush()
                print stdout

    def pre_calibration(self, input):
        print "doing precalibration stuff"
        self.log("doing precalibration stuff")
        # if input >= 1 and input <= 6:
        #     self.log("pre calibration - starting motor")
        #     print "starting motor"
        #     self.run_command("start motor")
        #     self.log("pre calibration - start showprogress")
        #     self.run_command("start showprogress")
        #     self.log("Sleep 10 seconds")
        #     print "Waiting for 10 seconds...Ctrl+C to stop program"
        #     time.sleep(10);

    def get_autocal_info(self, autocal_info):
        camSN = raw_input("Enter Camera Serial Number: ")
        camSN = camSN.upper()
        autocal_info["camSN"] = camSN
        self.log("Autocal - camSN = {0}".format(camSN))

    def get_autocal_info_all(self, autocal_info):
        camSN = raw_input("Enter Camera Serial Number: ")
        camSN = camSN.upper()
        autocal_info["camSN"] = camSN
        self.log("Autocal - camSN = {0}".format(camSN))

        cal = raw_input("Enter path to .cal file: ")
        autocal_info["cal"] = cal
        self.log("Autocal - .cal path = {0}".format(cal))

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
                    self.log("Autocal - setting rect. l = {0}, t = {1}, r = {2}, b = {3}".format(rect_l, rect_t, rect_r, rect_b))
                    break
                else:
                    autocal_info["rect"] = None
                    self.log("Autocal - no rect specified")
                    break
            except ValueError as ve:
                print "Error: Enter numbers only"
                print ve.message
                pass

        resume = ""
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
        self.log("Autocal resume/overwrite - resume = {0}, overwrite = {1}".format(autocal_info["resume"], autocal_info["overwrite"]))


    def get_autogrid_info(self, autogrid_info):
        overwrite = None
        resume = None
        use_default = False
        key = autogrid_info["key"]

        if "default" in autogrid_info.keys():
            use_default = autogrid_info["default"]

        if use_default == False:
            key = raw_input("Enter key value (from meta.data ie. 'gain' or 'spot'): ").strip()
            self.log("Autogrid - key set to {0}".format(key))

        completed = self.isKeyCompleted(key)
        if completed == "completed":
            overwrite = raw_input("'{0}s' was already completed. Overwrite? (y/n): ".format(key)).strip()
            if overwrite == "y" or overwrite == "Y":
                overwrite = True
            else:
                overwrite = False
            self.log("Autogrid key {0} completed. overwrite = {1}".format(key, overwrite))
        elif completed == "continue or overwrite":
            choice = raw_input("'{0}s_completed' found partially completed. Resume/Overwrite or Cancel? (r/o/c): ".format(key)).lower().strip()
            if choice == "r":
                resume = True
                overwrite = False
            elif choice == "o":
                overwrite = True
                resume = False
            elif choice == "c":
                sys.exit(9)
            self.log("Autogrid key {0} partially completed. overwrite = {1}, resume = {2}".format(key, overwrite, resume))
        elif completed == "no completed key":
            #first time running autogrid on this key
            overwrite = None
            resume = None
            self.log("Autogrid key {0} first time being processed.".format(key, overwrite))


        autogrid_info['key'] = key
        autogrid_info['resume'] = resume
        autogrid_info['overwrite'] = overwrite

    def get_cookgrid_gain_info(self, cookgrid_info):
        use_default = False
        temp_key = cookgrid_info["key"]

        if "default" in cookgrid_info.keys():
            use_default = cookgrid_info["default"]

        if use_default == False:
            temp_key = raw_input("Enter key value (from meta.data ie. 'gains'): ").strip()

        cookgrid_info['key'] = temp_key
        self.log("Cookgrid Gain - key = {0}".format(temp_key))

    def get_cookgrid_temp_info(self, cookgrid_info):
        use_default = False
        temp_key = cookgrid_info["key"]

        if "default" in cookgrid_info.keys():
            use_default = cookgrid_info["default"]

        if use_default == False:
            temp_key = raw_input("Enter key value (from meta.data ie. 'spots'): ").strip()

        cookgrid_info['key'] = temp_key
        self.log("Cookgrid Temp - key = {0}".format(temp_key))

    def use_defaults(self):
        while True:
            flag = raw_input("Use default keys 'gain' and 'spot'? (y/n): ")
            if flag.upper() == 'Y':
                return ('gain', 'spot', True);

            return ('','',False)


    def partial_calibration(self):
        sub_menu =  '******************************************\n'
        sub_menu += '* Calibrate starting from...:            *\n'
        sub_menu += '* 1. Autocal                             *\n'
        sub_menu += '* 2. Autogrid Gain                       *\n'
        sub_menu += '* 3. Cookgrid Gain                       *\n'
        sub_menu += '* 4. Autogrid Spot                       *\n'
        sub_menu += '* 5. Make Metamap                        *\n'
        sub_menu += '* 6. Cookgrid Spot                       *\n'
        sub_menu += '* 7. Checkspots                          *\n'
        sub_menu += '*                                        *\n'
        sub_menu += '* 8. Back                                *\n'
        sub_menu += '******************************************'
        prompt = '*>>> '
        while True:
            try:
                print sub_menu
                ok = raw_input(prompt)
                if ok == 'q' or ok == 'Q' or ok == '8':
                    self.log("User chose 8. Back in sub menu")
                    self.log("Back to Main Menu!")
                    print '\nBack to Main Menu!'
                    return False
                ok = int(ok)
                if ok >= 1 and ok <=8:
                    choice_str = self.get_choice_submenu_string(ok)
                    self.log("Sub menu, user chose: {0}".format(choice_str))
                    full_cal = False

                    os.chdir(self.md_path)

                    if ok == 1:
                        # Autocal
                        if not self.nir_tweaker_check():
                            raise SystemExit("Run NIR tweaker before full calibration. Returning to Main menu")
                        if not self.badpixels_check():
                            raise SystemExit("Run baxpixels before full calibration. Returning to Main menu")

                        full_cal=True
                        self.log("Partial calbration - Autocal")
                        autocal_info = {"cal": "../example.cal", "camSN": ""}
                        self.get_autocal_info(autocal_info)
                        if self.md_path != os.getcwd():
                            autocal_info["cal"] = os.path.join(self.cal_path, EXAMPLE_CAL)
                        pr_autocal = cProfile.Profile()
                        pr_autocal.enable()
                        autocal.autocal(autocal_info["cal"], autocal_info["camSN"], rect=None, resume=None, overwrite=None, cwd=self.md_path, full_cal=full_cal)
                        self.stop_profile(pr_autocal, "Autocal_stats.log", append=True)


                    if ok <= 2:
                        self.log("Partial calbration - Autogrid gain")
                        # Autogrid gain
                        autogrid_gain_info = {"resume": None, "overwrite": None, "key": "gain"}
                        #autogrid_gain_info = {"resume": True, "overwrite": None, "key": "gain"}
                        pr_autogrid_gain = cProfile.Profile()
                        pr_autogrid_gain.enable()
                        autogrid.autogrid(autogrid_gain_info['resume'], autogrid_gain_info['overwrite'], autogrid_gain_info["key"], cwd=self.md_path, full_cal=full_cal)
                        self.stop_profile(pr_autogrid_gain, "Autogrid_gain_stats.log", append=True)

                        # reload meta data
                        self.load_md(self.md_path)

                    if ok <= 3:
                        self.log("Patial calbration - Cookgrid gains")
                        # Cookgrid -gain gains
                        cookgrid_info = {"key": "gains"}
                        gains_completed_keys = []
                        if hasattr(self.md, cookgrid_info["key"] + "_completed"):
                            gains_completed = getattr(self.md, "{0}_completed".format(cookgrid_info["key"]))
                            gains_completed_keys = list(gains_completed.keys())
                        pr_cookgrid_gain = cProfile.Profile()
                        pr_cookgrid_gain.enable()
                        cookgrid.cookgrid_gain(cookgrid_info['key'], cwd=self.md_path, keys=gains_completed_keys)
                        self.stop_profile(pr_cookgrid_gain, "Cookgrid_gain_stats.log", append=True)

                        # reload meta data
                        self.load_md(self.md_path)

                    if ok <= 4:
                        self.log("Partial calbration - Autogrid spot")
                        # Autogrid spot
                        autogrid_spot_info = {"resume": None, "overwrite": None, "key": "spot"}
                        pr_autogrid_spot = cProfile.Profile()
                        pr_autogrid_spot.enable()
                        autogrid.autogrid(autogrid_spot_info['resume'], autogrid_spot_info['overwrite'], autogrid_spot_info["key"], cwd=self.md_path, full_cal=full_cal)
                        self.stop_profile(pr_autogrid_spot, "Autogrid_spot_stats.log", append=True)

                        # reload meta data
                        self.load_md(self.md_path)

                    if ok <= 5:
                        self.log("Partial calbration - Metamap make")
                        # Metamap make
                        pr_metamap = cProfile.Profile()
                        pr_metamap.enable()
                        metamap.makeMetaMap(cwd=self.md_path)
                        self.stop_profile(pr_metamap, "Metamap_stats.log", append=True)

                        # reload meta data
                        self.load_md(self.md_path)

                    if ok <= 6:
                        self.log("Partial calbration - Cookgrid spots")
                        # Cookgrid -temp spots
                        cookgrid_info = {"key": "spots"}
                        pr_cookgrid_spots = cProfile.Profile()
                        pr_cookgrid_spots.enable()
                        cookgrid.cookgrid_temp(cookgrid_info['key'], cwd=self.md_path)
                        self.stop_profile(pr_cookgrid_spots, "Cookgrid_spots_stats.log", append=True)

                        # reload meta data
                        self.load_md(self.md_path)

                    if ok <= 7:
                        self.log("Partial calibration - Checkspots")
                        pr_checkspots = cProfile.Profile()
                        pr_checkspots.enable()
                        # checkspots
                        cs_args = ['-p', '14', '-f', 'spots.*#1.tif', '-a', '#1', '-c']
                        checkspots.main(cs_args, cwd=self.md_path)
                        cs_args = ['-p', '14', '-f', 'spots.*#4.tif', '-a', '#4', '-c']
                        checkspots.main(cs_args, cwd=self.md_path)
                        cs_args = ['-p', '14', '-f', 'spots.*#12.tif', '-a', '#12', '-c']
                        checkspots.main(cs_args, cwd=self.md_path)
                        self.stop_profile(pr_checkspots, "Spotcheck_stats.log", append=True)

                    return True
                else:
                    print "Error: Please pick 0-8 only"

            except RuntimeError as rte:
                err_msg = rte.message
                err_args = rte.args.__str__()
                print msg
                print rte.message
                self.log(msg)
                self.log(err_msg)
                self.log(err_args)
                pass
            except ValueError as ve:
                msg = "Error: Enter numbers only"
                err_msg = ve.message
                err_args = ve.args.__str__()
                self.log(msg)
                self.log(err_msg)
                self.log(err_args)
                pass
            except SystemExit as e:
                self.handle_error(e.code)
                pass
            except Exception as ex:
                err_msg = ex.message
                err_args = ex.args.__str__()
                print ex.message
                self.log(err_msg)
                self.log(err_args)
                pass

    def get_choice_string(self, choice):
        if choice == 1:
            return "1. Full Calibration"
        elif choice == 2:
            return "2. Autocal"
        elif choice == 3:
            return "3. Autogrid"
        elif choice == 4:
            return "4. Cookgrid Gain"
        elif choice == 5:
            return "5. Cookgrid Temp"
        elif choice == 6:
            return "6. Make Metamap"
        elif choice == 7:
            return "7. Checkspots"
        elif choice == 8:
            return "8. Calibrate starting from..."
        elif choice == 9:
            return "9. Exit"
        elif choice == 0:
            return "0. Custom Command"
        else:
            return "Unable to find choice"

    def get_choice_submenu_string(self, choice):
        if choice == 1:
            return "1. Autocal"
        elif choice == 2:
            return "2. Autogrid Gain"
        elif choice == 3:
            return "3. Cookgrid Gain"
        elif choice == 4:
            return "4. Autogrid Spot"
        elif choice == 5:
            return "5. Make Metamap"
        elif choice == 6:
            return "6. Cookgrid Spot"
        elif choice == 7:
            return "7. Back"
        else:
            return "Unable to find choice"

    def backup_to_NAS_drive(self):
        camsn = self.cal_path[self.cal_path.rfind("/")+1:]
        print "Backing up Camera config files. \nSaving {0} to {1}/{2}\nThis may take a few minutes.".format(self.md_path, NAS_BACKUP, camsn)
        self.run_command("mkdir \"{0}\{1}\"".format(NAS_BACKUP, camsn))
        self.run_command("robocopy \"{0}\" \"{1}/{2}\" /E".format(self.md_path, NAS_BACKUP, camsn),prnt=False)

    def nir_tweaker_check(self):
        print "Did you run NIR tweaker? (y/n/s for skip)"
        while True:
            input = raw_input(">>> ")
            if input.lower() == "y" or input.lower() == "s":
                return True
            elif input.lower() == "n":
                return False
            else:
                print "Invalid input. Enter y/n/s only."

    def badpixels_check(self):
        print "Did you run badpixels? (y/n/s for skip)"
        while True:
            input = raw_input(">>> ")
            if input.lower() == "y" or input.lower() == "s":
                return True
            elif input.lower() == "n":
                while True:
                    print "Run baxpixels now? (y/n)\nYou will be given 10 seconds to cover camera shutter before badpixel begins."
                    input2 = raw_input(">>> ")
                    if input2.lower() == "y":
                        camSN = raw_input("Enter Camera Serial Number: ")
                        camSN = camSN.upper()

                        #run bad pixels
                        for i in range(10,0,-1):
                            print i,"..."
                            time.sleep(1)
                        self.run_badpixels(camSN)
                        return True
                    elif input2.lower() == "n":
                        return False
                    else:
                        print "Invalid input. Enter y/n only."
            else:
                print "Invalid input. Enter y/n/s only."

    def run_badpixels(self, camSN):
        #call to badpixels
        args = [camSN]
        badpixels.main(args)


    def main_menu(self):
        menu = '******************************************\n'
        menu += '* Choose command to run:                 *\n'
        menu += '* 1. Full Calibration                    *\n'
        menu += '* 2. Autocal                             *\n'
        menu += '* 3. Autogrid                            *\n'
        menu += '* 4. Cookgrid Gain                       *\n'
        menu += '* 5. Cookgrid Temp                       *\n'
        menu += '* 6. Make Metamap                        *\n'
        menu += '* 7. Checkspots                          *\n'
        menu += '* 8. Calibrate starting from...          *\n'
        menu += '* 9. Exit                                *\n'
        menu += '*                                        *\n'
        menu += '* 0. Custom Command                      *\n'
        menu += '******************************************'
        prompt = '*>>> '
        while True:
            try:
                print menu
                ok = raw_input(prompt)
                if ok == 'q' or ok == 'Q' or ok == '9':
                    self.log("Goodbye!")
                    print '\nGoodbye!'
                    return False
                ok = int(ok)
                if ok >= 0 and ok <= 9:
                    choice = self.get_choice_string(ok)
                    self.log("Main Menu. User chose: {0}".format(choice))

                    if ok == 0:
                        custom_command = raw_input("Enter custom command: ")
                        self.run_command(custom_command);
                    if ok == 1:
                        if not self.nir_tweaker_check():
                            raise SystemExit("Run NIR tweaker before full calibration. Returning to Main menu")
                        if not self.badpixels_check():
                            raise SystemExit("Run baxpixels before full calibration. Returning to Main menu")

                        self.log("Full calbration - pre calibration commands")
                        self.pre_calibration(ok)

                        self.log("Full calbration - Autocal")
                        #autocal -find -ctl ..\example.cal <CamSN>
                        autocal_info = {"cal":"../example.cal", "camSN": ""}
                        self.get_autocal_info(autocal_info)
                        if self.md_path != os.getcwd():
                            autocal_info["cal"] = os.path.join(self.cal_path, EXAMPLE_CAL)
                        #start to gather stats
                        pr_autocal = cProfile.Profile()
                        pr_autocal.enable()
                        autocal.autocal(autocal_info["cal"], autocal_info["camSN"], rect=None, resume=None, overwrite=None, cwd=self.md_path, full_cal=True)
                        self.stop_profile(pr_autocal, "Autocal_stats.log")

                        self.log("Full calbration - Autogrid gain")
                        #autogrid gain
                        autogrid_gain_info = {"resume":None, "overwrite":None, "key":"gain"}
                        # start to gather stats
                        pr_autogrid_gain = cProfile.Profile()
                        pr_autogrid_gain.enable()
                        autogrid.autogrid(autogrid_gain_info['resume'], autogrid_gain_info['overwrite'], autogrid_gain_info["key"], cwd=self.md_path, full_cal=True)
                        self.stop_profile(pr_autogrid_gain, "Autogrid_gain_stats.log")

                        #reload meta data
                        self.load_md(self.md_path)

                        self.log("Full calbration - Cookgrid gains")
                        #cookgrid -gain gains
                        cookgrid_info = {"key":"gains"}
                        gains_completed_keys = []
                        if hasattr(self.md, cookgrid_info["key"] + "_completed"):
                            gains_completed = getattr(self.md, "{0}_completed".format(cookgrid_info["key"]))
                            gains_completed_keys = list(gains_completed.keys())
                        # start to gather stats
                        pr_cookgrid_gain = cProfile.Profile()
                        pr_cookgrid_gain.enable()
                        cookgrid.cookgrid_gain(cookgrid_info['key'], cwd=self.md_path, keys=gains_completed_keys)
                        self.stop_profile(pr_cookgrid_gain, "Cookgrid_gain_stats.log")

                        self.log("Full calbration - Autogrid spot")
                        #autogrid spot
                        autogrid_spot_info = {"resume":None, "overwrite":None, "key":"spot"}
                        # start to gather stats
                        pr_autogrid_spot = cProfile.Profile()
                        pr_autogrid_spot.enable()
                        autogrid.autogrid(autogrid_spot_info['resume'], autogrid_spot_info['overwrite'], autogrid_spot_info["key"], cwd=self.md_path, full_cal=True)
                        self.stop_profile(pr_autogrid_spot, "Autogrid_spot_stats.log")

                        self.log("Full calbration - Metamap make")
                        #metamap make
                        # start to gather stats
                        pr_metamap = cProfile.Profile()
                        pr_metamap.enable()
                        metamap.makeMetaMap(cwd=self.md_path)
                        self.stop_profile(pr_metamap, "Metamap_stats.log")

                        self.log("Full calbration - Cookgrid spots")
                        #cookgrid -temp spots
                        cookgrid_info = {"key":"spots"}
                        # start to gather stats
                        pr_cookgrid_spots = cProfile.Profile()
                        pr_cookgrid_spots.enable()
                        cookgrid.cookgrid_temp(cookgrid_info['key'], cwd=self.md_path)
                        self.stop_profile(pr_cookgrid_spots, "Cookgrid_spots_stats.log")

                        #checkspots
                        dump123 = 111 #REPLACE THE COOKED SPOTS IMAGES
                        self.log("Full calibration - Checkspots")
                        pr_checkspots = cProfile.Profile()
                        pr_checkspots.enable()
                        cs_args = ['-p', '14', '-f', 'spots.*#1.tif', '-a', '#1', '-c']
                        checkspots.main(cs_args, cwd=self.md_path)
                        cs_args = ['-p', '14', '-f', 'spots.*#4.tif', '-a', '#4', '-c']
                        checkspots.main(cs_args, cwd=self.md_path)
                        cs_args = ['-p', '14', '-f', 'spots.*#12.tif', '-a', '#12', '-c']
                        checkspots.main(cs_args, cwd=self.md_path)
                        self.stop_profile(pr_checkspots, "Spotcheck_stats.log")

                        #backup to NAS drive
                        self.log("Full calibration - Backing up to NAS drive")
                        self.backup_to_NAS_drive()

                        return False
                    if ok == 2:
                        self.pre_calibration(ok)
                        autocal_info = {"cal": "", "camSN": "", "rect": None, "resume": None, "overwrite": None}
                        self.get_autocal_info_all(autocal_info)
                        pr_autocal = cProfile.Profile()
                        pr_autocal.enable()
                        autocal.autocal(autocal_info["cal"], autocal_info["camSN"], autocal_info["rect"], autocal_info["resume"], autocal_info["overwrite"], cwd=self.md_path)
                        self.stop_profile(pr_autocal, "Autocal_stats.log", append=True)

                        # reload meta data
                        self.load_md(self.md_path)
                    if ok == 3:
                        self.pre_calibration(ok)
                        autogrid_info = {"resume": None, "overwrite": None, "key": ""}
                        self.get_autogrid_info(autogrid_info)
                        if len(autogrid_info["key"]) > 0:
                            pr_autogrid = cProfile.Profile()
                            pr_autogrid.enable()
                            autogrid.autogrid(autogrid_info['resume'], autogrid_info['overwrite'], autogrid_info["key"], cwd=self.md_path)
                            self.stop_profile(pr_autogrid, "Autogrid_{0}_stats.log".format(autogrid_info["key"]), append=True)
                        else:
                            print "Error! key is blank."

                        # reload meta data
                        self.load_md(self.md_path)
                    if ok == 4:
                        cookgrid_info = {"key": ""}
                        os.chdir(self.md_path)
                        self.get_cookgrid_gain_info(cookgrid_info)
                        gains_completed_keys = []
                        if hasattr(self.md, cookgrid_info["key"]+"_completed"):
                            gains_completed = getattr(self.md, "{0}_completed".format(cookgrid_info["key"]))
                            gains_completed_keys = list(gains_completed.keys())
                        if len(cookgrid_info["key"]) > 0:
                            pr_cookgrid = cProfile.Profile()
                            pr_cookgrid.enable()
                            cookgrid.cookgrid_gain(cookgrid_info['key'], cwd=self.md_path, keys=gains_completed_keys)
                            self.stop_profile(pr_cookgrid, "Cookgrid_gain_{0}_stats.log".format(cookgrid_info["key"]), append=True)
                        else:
                            print "Error! key is blank."

                            # reload meta data
                            self.load_md(self.md_path)
                    if ok == 5:
                        os.chdir(self.md_path)
                        cookgrid_info = {"key": ""}
                        self.get_cookgrid_temp_info(cookgrid_info)
                        if len(cookgrid_info["key"]) > 0:
                            pr_cookgrid = cProfile.Profile()
                            pr_cookgrid.enable()
                            cookgrid.cookgrid_temp(cookgrid_info['key'], cwd=self.md_path)
                            self.stop_profile(pr_cookgrid, "Cookgrid_temp_{0}_stats.log".format(cookgrid_info["key"]),
                                              append=True)
                        else:
                            print "Error! key is blank."

                        # reload meta data
                        self.load_md(self.md_path)
                    if ok == 6:
                        pr_metamap = cProfile.Profile()
                        pr_metamap.enable()
                        metamap.makeMetaMap(cwd=self.md_path)
                        self.stop_profile(pr_metamap, "Metamap_stats.log", append=True)
                    if ok == 7:
                        pr_checkspots = cProfile.Profile()
                        pr_checkspots.enable()
                        # checkspots
                        cs_args = ['-p', '14', '-f', 'spots.*#1.tif', '-a', '#1', '-c']
                        #cs_args = ['-p', '45', '-f', 'spots.*#1.tif', '-a', '#1']
                        #cs_args = ['-p', '67_spots', '-f', 'spots.*#1.tif', '-a', '#1']
                        checkspots.main(cs_args, cwd=self.md_path)

                        cs_args = ['-p', '14', '-f', 'spots.*#4.tif', '-a', '#4', '-c']
                        #cs_args = ['-p', '45', '-f', 'spots.*#4.tif', '-a', '#4']
                        #cs_args = ['-p', '67_spots', '-f', 'spots.*#4.tif', '-a', '#4']
                        checkspots.main(cs_args, cwd=self.md_path)

                        cs_args = ['-p', '14', '-f', 'spots.*#12.tif', '-a', '#12', '-c']
                        #cs_args = ['-p', '45', '-f', 'spots.*#12.tif', '-a', '#12']
                        #cs_args = ['-p', '67_spots', '-f', 'spots.*#12.tif', '-a', '#12']
                        checkspots.main(cs_args, cwd=self.md_path)


                        self.stop_profile(pr_checkspots, "Checkspots_stats.log", append=True)
                    if ok == 8:
                        self.partial_calibration()
                else:
                    print "Error: Please pick 0-9 only"
            except RuntimeError as rte:
                msg = "Caught RuntimeError in ui_calibration_v2.py"
                err_msg = rte.message
                err_args = rte.args.__str__()
                print msg
                print rte.message
                self.log(msg)
                self.log(err_msg)
                self.log(err_args)
                #pass
            except ValueError as ve:
                msg = "Error: Enter numbers only or (q/Q) to quit"
                err_msg = ve.message
                err_args = ve.args.__str__()
                print ve.message
                self.log(msg)
                self.log(err_msg)
                self.log(err_args)
                pass
            except SystemExit as e:
                self.handle_error(e.code)
                #pass
            except Exception as ex:
                err_msg = ex.message
                err_args = ex.args.__str__()
                print ex.message
                if hasattr(ex, "strerror"):
                    print ex.strerror
                    self.log(ex.strerror)
                self.log(err_msg)
                self.log(err_args)
                #pass

    def close_log_file(self):
        self.log("closing log file")
        self.log_file.close()

def main(args):
    try:
        # bad pixels
        # Firmware updater
        # NIR parameter tweaker
        calui = CalUI()
        calui.run()

        # spackle & hotspot fix - used on gain map. but wont be needed on new 41 algorithm

        # checkspots

    finally:
        # check m390 temperature, if not at 581, set to 581 (hw_shutdown()?)
        # temp = autocalx.hw_gettemp()
        # if temp > 581:
        #     print "M390 current temperature is > 581. Starting shutdown procedure."
        #     autocalx.hw_shutdown()

        calui.close_log_file()

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

        file = open(os.path.join(calui.md_path,'Overall_statistics_info.log'), 'w')
        file.write(s.getvalue())
        file.write('\n\n\n')
        file.write(s2.getvalue())


if __name__ == '__main__':
    if main(sys.argv[1:]):
        print __doc__


