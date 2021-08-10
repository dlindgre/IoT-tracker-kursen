#
# This SW captures:
# acceleration from accelerometer L2HH12
# speed and GPS position from L76GNSS
# battery voltage from PyTrack 2.0x 
# 
# Data is pre processed in order to look for gradients and behaviour of acceleration and speed
#
# Finally data is transferred to the cloud and saved to an SD card available on pyTrack2
#
# For now a Lopy4 is used. This will be changed to FiPy as suggested by F. Ahlgren to reduce the latency issues noted.
# As such some of teh code will be updated in the frame of this R&D activity.
#
# David Lindgren 2021
# 
# 

import time
import pycom
import ujson
import ubinascii
import machine
import network
import utime
import uos

from network import WLAN
from L76GNSV4 import L76GNSS
from pycoproc_2 import Pycoproc
from LIS2HH12 import LIS2HH12
from machine import SD
from machine import RTC

def runningAvg(MyShfiftRegIn):
    sumV=0.0
    countV=0
    for x in MyShiftRegIn:
        sunV=sumV+x
        countV=countV+1
    myRunAvg=sumV/countV
    return myRunAvg

def shiftRegAdd(MyShiftReg,ValueIn):
    MyShiftReg[0]=MyShiftReg[1]
    MyShiftReg[1]=MyShiftReg[2]
    MyShiftReg[2]=ValueIn
    return MyShiftReg



#
# Initiate sensors and SD card
#
print("Initiate sensor and GPS")
py = Pycoproc()
L76 = L76GNSS()
L76.setAlwaysOn()
acc = LIS2HH12(py)
rtc=RTC()
print("Sensors and GPS initiated")
print("Get GPS connected")
L76.get_fix(debug=False)
print("GPS connected")
if L76.fixed():
    pycom.rgbled(0x000f00)
print("Init SD card")
try:
    sd=SD()
    print("mounting SD card")
    uos.mount(sd, '/sd')
    uos.listdir('/sd')
    print("Testing SD card")
    with open ('/sd/fileWSD.txt', 'w') as f:
        f.write("Hello!")
    with open ('/sd/fileWSD.txt') as f:
        print(f.read())
    print("SDcard tested")
except:
    print("SD card missing or other SD card error")
    write2SD=False
#
# set initial values
#
okToStore=True
speedPrevious=0.0
accXPrevious=0.0
accXCalc=0.0
calcSpeed=0.0
speedReg=[0,0,0]
accZReg=[0,0,0]
RTCtime=rtc.now()
print(RTCtime[6])

secondsPrevious=utime.time()
runID=str(RTCtime[6])

# Validation of shift register and runing average
speedArr=L76.get_speed()
print(speedArr)
speed=speedArr.get('speed')
print(speedReg)
speedReg=shiftRegAdd(speedReg,float(speed))
print(speedReg)
speedAvg=runningAvg(speedReg)
print("Average speed:"+str(speedAvg))
#
# Main loop
#
while True:
    #
    # read data from sensors
    #
    coord = L76.coordinates(debug=False)
    print(coord)
    ido = L76.getUTCDateTime(debug=False)
    accel = acc.acceleration()
    accX=accel[0]*9.81
    
    accY=accel[1]*9.81
    accZ=accel[2]*9.81
    print(accel, accX, accY,accZ)
    accZReg=shiftRegAdd(accZReg,float(accZ))
    speedReg=shiftRegAdd(speedReg,float(speed))
    # Compare acceleration. Do we need to store or can we use previous datapoint?
    if abs(accX-accXPrevious)<0.005:
        okToStore=False
    else:
        okToStore=True
    accXPrevious=accX
    speedArr=L76.get_speed()
    print(speedArr) # R&D info
    battery_voltage = py.read_battery_voltage()
    lat=coord.get('latitude')
    long=coord.get('longitude') 
    speed=speedArr.get('speed')
    gpsspeed=float(speed)
    print("Gps speed" + str(gpsspeed))
    # Compare speed. Do we need to store or can we use previous datapoint?
    # Only as comment since these tests will be is a nested structure in the final solution.
    """ if abs(speed-speedPrevious)<1:
        okToStore=False
    else:
        okToStore=True
    speedPrevious=speed """

    myDate=ido.split("T")[0]
    myTime=ido.split("T")[1]

    #function time to seconds
    hour=myTime.split

    RTCtime=rtc.now()
    print(RTCtime)

    #
    # Prepare dataset for upload
    #
    dict = {}  
    dict = {"myTime":myTime,
         "myDate":myDate,
         "Voltage_battery": str(battery_voltage),
         "latitude":str(lat),
         "longitude":str(long),
         "speed": str(speed),
         "accX":str(accel[0]),
         "accY":str(accel[1]),
         "accZ":str(accel[2]),
    }
    
    
    #
    # if connected, write to pybytes and SD card (as backup). 
    # 

    okToStore=True # Later on this flag will depend on difference between the result and the previous result.

    if okToStore:
      #  if not(wlan.isconnected()):
        pybytes.send_signal(2,ujson.dumps(dict))
        print(ujson.dumps(dict))
        print("Write to cloud")
        print("Write to SD")
        with open ('/sd/Measure2'+runID+'.txt', 'a') as f:
            f.write(ujson.dumps(dict))
            f.write('\n')
    else:
        print("No need to save data")


    time.sleep(1) # No action for 1 second

    #
    # if no OK2Write for more than 600 iterations, go sleep. Latre on development.
    #
