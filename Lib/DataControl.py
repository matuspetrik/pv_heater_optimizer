# Data processing functions
# from Lib import VictronApi
import Lib.Logger as logger
import argparse
import os
import yaml
from munch import Munch
from pprint import pprint

class Battery:

    def __init__(self, data):
        self.data = data

    def state(self, codes):
        # codes:
        #   bst - battery state
        # Returns:
        #   - idle
        #   - charging
        #   - discharging
        codes = [codes] if isinstance(codes, str) else codes
        assert isinstance(codes, list)
        for code in codes:
            ret = [element["formattedValue"]\
                for element in self.data if element["code"]==code][0].split()[0]
        return ret

    def power(self, codes):
        # codes:
        #   bp - battery power, positive or negative integer
        codes = [codes] if isinstance(codes, str) else codes
        assert isinstance(codes, list)
        for code in codes:
            power = int(float([element["formattedValue"]\
                for element in self.data if element["code"]==code][0].split()[0]))
        return power

    def soc(self, codes, minBattery):
        # codes:
        #   SOC - state of charge
        codes = [codes] if isinstance(codes, str) else codes
        assert isinstance(codes, list)
        for code in codes:
            batterySoC = int(float([element["formattedValue"]\
                for element in self.data if element["code"]==code][0].split()[0]))

        if batterySoC > minBattery:
            logger.file(f"\tBattery SoC is { batterySoC }%: OK.")
            return batterySoC
        else:
            logger.file(f"\tToo low: { batterySoC }%."+
                        f"We need at least { minBattery }%."+
                        "Waiting to be charged..")
        return False

class Grid:

    def __init__(self, data):
        self.data = data

    def power(self, codes, maxDraw):
        codes = [codes] if isinstance(codes, str) else codes
        assert isinstance(codes, list)
        # https://vrm.victronenergy.com/installation/<installation_id>/dashboard
        #   - Grid
        # return power drawn from grid, L1+L2+L3
        # codes = ["g1p", "g2p", "g3p"]
        power = 0
        for code in codes:
            partPower = int(float([element['formattedValue']\
                for element in self.data if element['code']==code][0].split()[0]))
            power += partPower

        if power <= maxDraw:
            logger.file(f"\tDrawing { power } Watts from grid: OK.")
            power = "ZERO"
            return power
        else:
            logger.file(f"\tDrawing { power } Watts which is more than { maxDraw }. "+
                        "Waiting for grid to be less utilized...")
        return False

    def consumPower(self, codes):
        codes = [codes] if isinstance(codes, str) else codes
        assert isinstance(codes, list)
        # https://vrm.victronenergy.com/installation/<installation_id>/dashboard
        #   - AC loads: i1 + i2 + i3
        #   - Critical loads: o1
        # codes = ["i1", "i2", "i3", "o1"]
        power = 0
        for code in codes:
            tmpPower = int(float([element["formattedValue"]\
                for element in self.data if element["code"]==code][0].split()[0]))
            power += tmpPower
        return power

class PV:

    def __init__(self, data):
        self.data = data

    def power(self, codes):
        # codes = ["ScW"]     # or PVP
        codes = [codes] if isinstance(codes, str) else codes
        assert isinstance(codes, list)
        power = 0
        for code in codes:
            tmpPower = int(float([element["formattedValue"]\
                for element in self.data if element["code"]==code][0].split()[0]))
            power += tmpPower
        return power


class Variables:

    def __init__(self, cfgFile):
        self.cfgFile = cfgFile

        try:
            with FileHandler(self.cfgFile, "r") as cf:
                cfg = Munch(yaml.safe_load(cf))
        except Exception as e:
            logger.file(f"-- Config file problem: { e }")

        self.username = cfg.api_username
        self.password = cfg.api_password
        self.logInUrl = cfg.login_url
        self.logOutUrl = cfg.logout_url
        self.diagsUrl = cfg.diags_url
        self.minBattery = cfg.min_battery
        self.minDayTime = cfg.min_day_time
        self.maxDayTime = cfg.max_day_time
        self.sleepTimer = cfg.sleep_timer
        self.maxGridDraw = cfg.max_grid_draw
        self.maxBatteryDraw = cfg.max_battery_discharge
        self.tolerateRange = cfg.tolerance
        self.pwrPcnt = cfg.power_percent
        self.fcastUrl = cfg.fcast_url
        self.fcastHeaders = cfg.fcast_headers
        self.fcastDiff = cfg.fcast_diff
        self.fcastTimePull = cfg.fcast_time_pull
        self.adjust = cfg.adjust_value
        self.logfile = cfg.log_file
        self.fcastHourlyFile = cfg.day_hourly_fcast


class FileHandler:

    def __init__(self, fileName, action):
        self.name = fileName
        self.action = action

    def __enter__(self):
        self.file = open(self.name, self.action)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()

def parseConfig(fileOnly=False):
    parser = argparse.ArgumentParser()
    parser.add_argument(\
                        "-c",\
                        "--config",\
                        type=str,\
                        help = "Define own configuration file. "+
                        "If not defined, default will be used: Files/config.yaml",\
                        default=os.environ['CONFIG_FILE']
                        )
    args = parser.parse_args()
    # print(f"args: { args.config }")
    cfgFile = args.config
    # print(cfgFile)
    if fileOnly:
        return cfgFile
    vars = Variables(cfgFile)
    return vars
