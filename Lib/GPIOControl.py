# Servo motor functions
import RPi.GPIO as gpio
import time

class RelayControl:

    # def __init__(self, pin, flag=False, relayOn=False):
    def __init__(self, **kwargs):
        self.pin = kwargs.get("pin", 11)
        # self.heatingFlag = kwargs.get("flag", False)

    def __enter__(self):
        # gpio.setmode(gpio.BOARD)
        # gpio.setup(self.pin, gpio.OUT)
        # time.sleep(0.1)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass
        # time.sleep(2)
        # gpio.cleanup(self.pin)

    def triggerWorkaround(self, heatingFlag=False):
        # This is a workaround since relay is 5V for arduino.
        # RPi provides only 3V3 on GPIO, thus need to replace with 3V3 relay.
        # https://forums.raspberrypi.com//viewtopic.php?f=91&t=83372&p=1225448#p1225448
        gpio.setwarnings(False)
        gpio.setmode(gpio.BOARD)
        if heatingFlag:
            print("TURN ON")
            # gpio.setmode(gpio.BOARD)
            gpio.setup(self.pin, gpio.OUT)
            gpio.output(self.pin, gpio.HIGH)
            # time.sleep(10)
        else:
            print("TURN OFF")
            gpio.setup(self.pin, gpio.OUT)
            gpio.cleanup(self.pin)
            # time.sleep(1)
            gpio.setmode(gpio.BOARD)

    def trigger(self, heatingFlag=False):
        # Normal operation:
        # print(f"Heating Flag: { heatingFlag }")
        # Called:
        # with RelayControl(pin=11, flag=False) as relayCtl:
        #     relayCtl.trigger(False)
        if heatingFlag:
            print("TURN ON")
            action = gpio.HIGH
        else:
            print("TURN OFF")
            action = gpio.LOW
        gpio.output(self.pin, action)

    def __del__(self):
        print("DEL TURN OFF")
        gpio.setup(self.pin, gpio.OUT)
        gpio.cleanup(self.pin)
        # time.sleep(1)
        gpio.setmode(gpio.BOARD)



class ServoControl:

    def __init__(self, pin):
        self.pin = pin
        self.time_sleep = 0.2
        self.steps = 10
        self.freqc = 50

    def __enter__(self):
        gpio.setmode(gpio.BOARD)
        gpio.setup(self.pin, gpio.OUT)
        self.servo = gpio.PWM(self.pin, self.freqc)
        self.servo.start(0)
        time.sleep(self.time_sleep)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.servo.stop(self.pin)
        gpio.cleanup(self.pin)

    def rotateServo(self, powerPercent):
        # powerPercent: 0-100 %:
        #   0 => 0, 100 => 180 degrees
        #   0 => 2, 100 => 12 steps
        if powerPercent > 100: powerPercent = 100
        if powerPercent < 0: powerPercent = 0
        duty = (powerPercent * self.steps)/100 + 2
        assert duty <= self.steps + 2
        self.servo.ChangeDutyCycle(duty)
        time.sleep(self.time_sleep)


# # just for testing
# # RELAY:
# with RelayControl(pin=11) as relayCtl:
#     relayCtl.triggerWorkaround(True)
#     # relayCtl.trigger(False)
# # SERVO:
# val = 60
# with ServoControl(pin=40) as sc:
#     sc.rotateServo(val)
# while True:
#     if val < 0: val = 0
#     with ServoControl(pin=40) as sc:
#         print(val)
#         sc.rotateServo(val)
#     val = val - 10
#     time.sleep(2)
#     del sc