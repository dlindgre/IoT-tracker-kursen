import socket
import time
import pycom
import ujson
import ubinascii
import machine
import network
import utime
import uos
import math
import gc
from network import WLAN
from L76GNSV4 import L76GNSS
from pycoproc_2 import Pycoproc
from LIS2HH12 import LIS2HH12
from machine import SD
from machine import RTC

gc.enable()
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
#
# set initial values
#
okToStore=True
speedPrevious=0.0
accXPrevious=0.0
accXCalc=0.0
calcSpeed=0.0
#deltaTime=0 not needed
RTCtime=rtc.now()
print(RTCtime)
secondsTick=RTCtime[3]*3600+RTCtime[4]*60+RTCtime[6]

secondsPrevious=RTCtime[4]


#
# Main loop
#
while True:
    #break
    #
    # read data from sensord
    #
    coord = L76.coordinates(debug=False)
    ido = L76.getUTCDateTime(debug=False)
    accel = acc.acceleration()
    accX=accel[0]*9.81
    
    accY=accel[1]*9.81
    accZ=accel[2]*9.81
    print(accel, accX, accY,accZ)
    
    # Compare acceleration. Do we need to store or can we use previous datapoint?
    if abs(accX-accXPrevious)<0.05:
        okToStore=False
    else:
        okToStore=True
    if abs(accX)<0.2: # reduce noise (Experimental!)
        accX=0
    print(accX)
    accXPrevious=accX
    speedArr=L76.get_speed()
    battery_voltage = py.read_battery_voltage()
    lat=coord.get('latitude')
    long=coord.get('longitude') 
    speed=speedArr.get('speed')
    gpsspeed=float(speed)
    print("Gps speed" + str(gpsspeed))
    # Compare speed. Do we need to store or can we use previous datapoint?
    """ if abs(speed-speedPrevious)<3:
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

    deltaTime=RTCtime[4]-secondsPrevious
    print ("Delta time: "+str(deltaTime))
    secondsPrevious=RTCtime[4]
    calcSpeed=speedPrevious+accX*deltaTime
    print("Calculated speed: "+str(calcSpeed))


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
    # if connected, write to pybytes using http protocol. If not connected, write to SD card
    # 

    okToStore=True

    if okToStore:
        if not(wlan.isconnected()):
           # pybytes.send_signal(2,ujson.dumps(dict))
            print(ujson.dumps(dict))
            print("Write to cloud")
        else:
            print("Write to SD")
            with open ('/sd/Measure2.txt', 'w') as f:
                f.write(ujson.dumps(dict))
    else:
        print("No need to save data")


    #break
    print()
    print()
    print()
    print()
    #pybytes.send_signal(2,ujson.dumps(dict)) #om kontakt saknas, skriv till fil

    time.sleep(1) # No action for 1 second

    #
    # if no OK2Write for more than 600 iterations, go sleep
    #
