import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import os
import sys
import logging
import spidev as SPI
from bluepy import btle

from Code.temperatureMOC import Measure, mac

sys.path.append("..")
from lib import LCD_2inch
from PIL import Image,ImageDraw,ImageFont

# Raspberry Pi pin configuration:
RST = 27
DC = 25
BL = 18
bus = 0
device = 0
logging.basicConfig(level=logging.DEBUG)
directory = os.getcwd()


doInterrupt = 0
showOn = 0

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
Moisture_channel = AnalogIn(ads, ADS.P2)
LDR_channel = AnalogIn(ads, ADS.P3)
LM35_channel = AnalogIn(ads, ADS.P1)

ADC_16BIT_MAX = 65536
lm35_constant = 10.0/1000
ads_InputRange = 4.096 #For Gain = 1; Otherwise change accordingly
ads_bit_Voltage = (ads_InputRange * 2) / (ADC_16BIT_MAX - 1)

#Initialising Variables
Moisture_Recent = 100
HighIn_DataSent = 0
LowIn_DataSent = 0
Thirsty_DataSent = 0
Savory_DataSent = 0
Happy_DataSent = 0
TemperatureDataSent = 0

previousData = ''


# Map function
def _map(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)



def show(emotion):
    global doInterrupt, showOn, disp
    try:
        disp = LCD_2inch.LCD_2inch(spi=SPI.SpiDev(bus, device),spi_freq=90000000,rst=RST,dc=DC,bl=BL)
        disp.Init() # Initialize library.
        #disp.clear() # Clear display.
        bg = Image.new("RGB", (disp.width, disp.height), "BLACK")
        draw = ImageDraw.Draw(bg)
        # display with hardware SPI:
        for i in range(180):
            if (doInterrupt==1):
                doInterrupt = 0
                break
            else:
                image = Image.open(directory+'/emotion/'+emotion+'/frame'+str(i)+'.png')
                image = image.rotate(180)
                disp.ShowImage(image)
        showOn = 0
        disp.module_exit()
        logging.info("quit:")
    except IOError as e:
        logging.info(e)
    except KeyboardInterrupt:
        disp.module_exit()
        logging.info("quit:")
        exit()


def display(data):
    global doInterrupt, showOn, previousData
    if previousData != data:
        print(data)
        doInterrupt = 1
        previousData = data
        show(data)

def connect():
    p = btle.Peripheral(mac)
    p.writeCharacteristic(0x0038, b'\x01\x00', True)
    p.writeCharacteristic(0x0046, b'\xf4\x01\x00', True)
    measure = Measure("mijia")
    p.withDelegate(measure)
    return p




if __name__ == '__main__':
    show('thirsty')
    while True:
        # Read the specified ADC channels using the previously set gain value.
        LDR_Value = LDR_channel.value
        LDR_Percent = _map(LDR_Value, 22500, 50, 0, 100)
        Moisture_Value = Moisture_channel.value
        Moisture_Percent = _map(Moisture_Value, 17539, 7148, 0, 100)
        ads_ch0 = LM35_channel.value
        ads_Voltage_ch0 = ads_ch0 * ads_bit_Voltage
        Temperature = int(ads_Voltage_ch0 / lm35_constant)
        print("Temperature = ", Temperature)
        print("Light Intensity = ", LDR_Percent)
        print("Moisture % = ", Moisture_Percent)
        if (LDR_Percent < 20):
            if(LowIn_DataSent == 0):
                #client.connect(('0.0.0.0', 8080))
                # client.send(bytes('sleep','utf-8'))
                #client.close()
                display('sleep')
                HighIn_DataSent = 0
                LowIn_DataSent = 1
        elif (LDR_Percent > 20):
            if(HighIn_DataSent == 0):
                #client.connect(('0.0.0.0', 8080))
                # client.send(bytes('happy','utf-8'))
                #client.close()
                display('happy')
                HighIn_DataSent = 1
                LowIn_DataSent = 0

        if (Moisture_Percent < 10):
            Moisture_Recent = Moisture_Percent
            if(Thirsty_DataSent == 0):
                #client.connect(('0.0.0.0', 8080))
                # client.send(bytes('thirs','utf-8'))
                #client.close()
                display('thirsty')
                Thirsty_DataSent = 1
                Savory_DataSent = 0
                Happy_DataSent = 0
        elif (Moisture_Percent>10 and Moisture_Recent < Moisture_Percent and Moisture_Percent < 90):
            Moisture_Recent = Moisture_Percent
            if(Savory_DataSent == 0):
                display('savor')
                Savory_DataSent = 1
                Thirsty_DataSent = 0
                Happy_DataSent = 0
        elif (Moisture_Percent > 90):
            Moisture_Recent = Moisture_Percent
            if(Happy_DataSent == 0):
                display('savor')
                Happy_DataSent = 1
                Savory_DataSent = 0
                Thirsty_DataSent = 0

        if(Temperature>30):
            if(TemperatureDataSent == 0):
                display('hot')
                TemperatureDataSent = 1
        elif(Temperature<22):
            if(TemperatureDataSent == 0):
                display('freeze')
                TemperatureDataSent = 1
        else:
                TemperatureDataSent = 0
