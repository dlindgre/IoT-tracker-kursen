import socket
import time
import pycom
import ubinascii
import machine
import network
#from network import LoRa
from L76GNSV4 import L76GNSS
from pycoproc_2 import Pycoproc
from LIS2HH12 import LIS2HH12
from machine import ADC



print("Före")
py = Pycoproc()
print("Efter")
L76 = L76GNSS()
L76.setAlwaysOn()
acc = LIS2HH12(py)
# make the socket non-blocking
# (because if there's no data received it will block forever...)
##s.setblocking(False)
print("Pre fix")
L76.get_fix(debug=False)
print("post fix")
if L76.fixed():
    pycom.rgbled(0x000f00)
while True:
    coord = L76.coordinates(debug=False)
    ido = L76.getUTCDateTime(debug=False)
    accel = acc.acceleration()
    speed=L76.get_speed()
    battery = py.read_battery_voltage()

    print(coord)
    print(speed)

    dict = {}
    dict['deviceToken'] = "d4c203ae-0429-4647-b377-f7524aa0707b"
    dict['event'] = "Datacake"
    dict['signal'] = "2"
    dict['payload'] = {
        'voltage': battery,
        'speed': speed,
        "COG": 160.89,
        "ACC":(0.1253662, -0.07019043, 0.9925537),
        "Coord": coord,
        "latitude": 56.27001,
        "longitude": 12.97098,
        "ttf": 0,
        "TIME":0, 
    }
   
    print(str(dict))
    
    pybytes.send_signal(2,str(dict))

    time.sleep(10)
