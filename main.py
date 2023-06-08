import os
from time import sleep
from datetime import datetime
import Lib.Logger as logger
import Lib.GPIOControl as rpigpio
import Lib.DataControl as dtctl
from Lib import Forecast as forecast
import Lib.VictronApi as vcapi


def main():

    logger.file('\n\n')
    servoPin = 40
    relayPin = 11
    heatingFlag = False
    initRun = True
    vars = dtctl.parseConfig()

    # init relay to off
    with rpigpio.RelayControl(pin=relayPin) as relayCtl:
        relayCtl.triggerWorkaround(heatingFlag)

    # Get forecast data for the day by starting
    # a new thread and getting forecast file written
    fcastThread = forecast.FcastThreading(vars, initRun)
    fcastThread.start()

    d = vcapi.getPortalData(vars)
    f = forecast.HourlyFileHandle(vars)

    while True:
        if not initRun:
            logger.file(f"==== FULL LOOP END:: {datetime.now()} ====")
            sleep(vars.sleepTimer)
            if not heatingFlag:
                vars.pwrPcnt = 50
                with rpigpio.RelayControl(pin=relayPin) as relayCtl:
                    relayCtl.triggerWorkaround(heatingFlag)
        initRun = False
        logger.file(f"==== FULL LOOP START:: {datetime.now()} ====")


        # Daylight hours verification
        logger.file("Daylight hours verification:")
        daytime = forecast.Daylight(vars.minDayHour, vars.maxDayHour)
        if not daytime.daylightHour():
            heatingFlag = False
            continue

        # Net/portal connectivity verification
        logger.file("Portal connectivity and getting data:")
        data = d.getData()
        if not data:
            heatingFlag = False
            continue

        # Battery state verification
        logger.file("Battery verification:")
        battery = dtctl.Battery(data)
        # if not dtctl.getBatterySoC(data, varsDict):
        # if not battery.soc(["SOC"], varsDict["minBattery"]):
        if not battery.soc(["SOC"], vars.minBattery):
            heatingFlag = False
            continue

        grid = dtctl.Grid(data)
        # Grid power verification
        # if not dtctl.getGridPower(data, varsDict):
        # if not grid.power(["g1p", "g2p", "g3p"], varsDict["maxGridDraw"]):
        logger.file("Grid verification:")
        if not grid.power(["g1p", "g2p", "g3p"], vars.maxGridDraw):
            heatingFlag = False
            continue

        # Get PV power
        pv = dtctl.PV(data)
        pvPower = pv.power("ScW")

        # Get system's total power draw
        # totalPower = dtctl.getTotalPower(data)
        totalPower = grid.consumPower(["i1", "i2", "i3", "o1"])

        # Weather forecast verification
        dayForecastDict = f.readFile(vars.fcastHourlyFile)
        hour = f"{ datetime.now().strftime('%H') }"

        logger.file(f"Heating flag is set to: { heatingFlag }")
        if heatingFlag:   # when boiler is turned on and drawing power
            if \
            abs(battery.power("bp")) > vars.maxBatteryDraw or \
            battery.state("bst") == "discharging":
                # drawing more than limit from battery
                logger.file(f"\servo decrease")
                vars.pwrPcnt = vars.pwrPcnt - vars.adjust
                if vars.pwrPcnt < 0: vars.pwrPcnt = 0
                print(vars.pwrPcnt)
                with rpigpio.ServoControl(pin=servoPin) as sc:
                    sc.rotateServo(vars.pwrPcnt)
                del sc
            elif dayForecastDict["data"][hour] - pvPower > vars.tolerateRange:
                    # can draw more power from PV
                    logger.file(f"\servo increase")
                    vars.pwrPcnt = vars.pwrPcnt + vars.adjust
                    if vars.pwrPcnt > 100: vars.pwrPcnt = 100
                    print(vars.pwrPcnt)
                    with rpigpio.ServoControl(pin=servoPin) as sc:
                        sc.rotateServo(vars.pwrPcnt)
                    del sc
            else:
                print("All settled. Doing nothing.")
        else:
            # enough spare PV power and heater is off
            print(f"Forecast for { hour } o'clock: { dayForecastDict['data'][hour] }")
            print(f"PV Power: { pvPower }")
            if dayForecastDict["data"][hour] - pvPower > vars.fcastDiff:
                print(vars.pwrPcnt)
                logger.file(\
                    f"\tForecast for { hour } o'clock: { dayForecastDict['data'][hour] }, "
                    f"and drawing only { pvPower }. Turning heater on.")
                heatingFlag = True
                with rpigpio.RelayControl(pin=relayPin, flag=True) as rc:
                    rc.triggerWorkaround(heatingFlag)
                with rpigpio.ServoControl(pin=servoPin) as sc:
                    sc.rotateServo(vars.pwrPcnt)
                del sc
            else:
                print("Conditions not met, doing nothing!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped by CTRL+C")
