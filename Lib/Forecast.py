from datetime import datetime, date, timedelta
import sys
import time
import re
from threading import Thread
import Lib.Logger as logger
import requests
import schedule
import json


class Daylight:

    def __init__(self, *args):
        self.currTime = datetime.now()
        self.minTime = self.currTime.replace(
            hour=int(args[0].split(":")[0]),
            minute=int(args[0].split(":")[1]),
            second=int(args[0].split(":")[2])
            )
        self.maxTime = self.currTime.replace(
            hour=int(args[1].split(":")[0]),
            minute=int(args[1].split(":")[1]),
            second=int(args[1].split(":")[2])
            )
        # print(self.minTime)
        # print(self.maxTime)
        # print(self.currTime)

    def daylightHour(self):
        if self.currTime < self.minTime:
            logger.file(f"\tToo early morning: { self.currTime } o'clock. We're starting at "+
                        f"{ self.minTime } o'clock.")
            return False
        if self.currTime > self.maxTime:
            logger.file(f"\tToo late for sunshine: { self.currTime } o'clock. Let's wait till "+
                        f"tomorrow { self.minTime } o'clock.")
            return False
        logger.file("\tWe are at correct phase of the day: OK.")
        return True


class HourlyFileHandle:

    def __init__(self, vars):
        self.vars = vars
        self.url = self.vars.fcastUrl
        self.headers = self.vars.fcastHeaders

    def writeToFile(self, data):
        self.nowDateTime = date.today()
        responseJson = json.loads(f"{ data }".replace("'", '"'))
        thisDayDict = {}
        thisDayDict["today"] = f"{ self.nowDateTime }"
        thisDayDict["data"] = None
        counter = 0         # skip very first occurence for the day
        prevHour = None
        prevValue = 0
        tmpDict = {}
        for dayTime, value in responseJson["result"].items():
            if f"{ date.today() }" in dayTime and counter > 0:
                hour = dayTime.split()[-1].split(":")[0]
                if prevHour == hour:    # skip very last occurence for the day
                    continue
                value = value - prevValue
                tmpDict[hour] = value
                prevHour = hour
                prevValue = responseJson["result"][dayTime]
            counter += 1
        thisDayDict["data"] = tmpDict
        fileName = self.vars.fcastHourlyFile
        with open(fileName, "w") as f:
            json.dump(thisDayDict, f)

    def readFile(self, file):
        _res = None
        while _res is None:
            _res = True
            try:
                with open(file, "r") as f:
                    return json.load(f)
            except Exception as inst:
                _res = None
                logger.file(f"{ type(inst).__name__ }: { inst }")
                time.sleep(self.vars.sleepTimer)

    def getRawFcastData(self):
        currentMethodName = sys._getframe(  ).f_code.co_name
        curFn = f"{ __name__ }.{ currentMethodName }: "
        try:
            msg = curFn+"Other error."
            response = requests.get(self.url, headers=self.headers, timeout=10)
            if response.status_code == 429:
                msg = f"{ curFn }{ response.status_code }: Too many requests."
                raise ValueError(f"\tForecast connection status is { response.status_code }.")
            if response.status_code == 422:
                msg = f"{ curFn }{ response.status_code }: Invalid/unknown location."
                raise ConnectionError(f"\tForecast connection status is { response.status_code }.")
            if response.status_code != 200:
                msg = f"{ curFn }{ response.status_code }: Other error."
                raise ConnectionError(f"\tForecast connection status is { response.status_code }.")
        except ValueError as inst:
            try:
                retryAt = response.json()["message"]["ratelimit"]["retry-at"]
            except:
                newTime = datetime.now() + timedelta(seconds=60)
                retryAt = newTime.strftime("%H:%M:%S")
            hour = retryAt.split("T")[-1].split(":")[0]
            minute = retryAt.split("T")[-1].split(":")[1]
            second = re.split('\+|\-', retryAt.split("T")[-1].split(":")[2])[0]
            schedule.clear()    # restart scheduler
            thrd = FcastThreading(self.vars)
            thrd.timeToRun = f"{ hour }:{ minute }:{ second }"
            logger.file(f"\t{ msg }")
            thrd.run()
        except Exception as inst:
            schedule.clear()
            thrd = FcastThreading(self.vars)
            newTime = datetime.now() + timedelta(seconds=10)
            thrd.timeToRun = newTime.strftime("%H:%M:%S")
            logger.file(f"\t{ msg }")
            thrd.run()
        else:
            msg = curFn+"OK"
            try:
                self.writeToFile(response.json())
            except:
                self.writeToFile({"no_json_data":"True"})
            thrd = FcastThreading(self.vars)
            schedule.clear()
            thrd.timeToRun = self.vars.fcastTimePull
            thrd.run()


class FcastThreading(Thread):

    def __init__(self, vars, initRun=False):
        super().__init__()
        self.vars = vars
        self.initRun = initRun
        self.timeToRun = self.vars.fcastTimePull
        self.url = self.vars.fcastUrl
        self.headers = self.vars.fcastHeaders

    def run(self):
        if self.initRun:
            newTime = datetime.now() + timedelta(seconds=2)         # only for testing
            self.timeToRun = newTime.strftime("%H:%M:%S")                         # only for testing
        self.initRun = False
        f = HourlyFileHandle(self.vars)
        logger.file(f"THREADING: Next run at: { self.timeToRun }")
        schedule.every().day.at(f"{ self.timeToRun }").do(f.getRawFcastData)

        while True:
            schedule.run_pending()
            time.sleep(1)
