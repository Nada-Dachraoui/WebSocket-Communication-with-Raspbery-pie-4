import sqlite3
import board
import busio
import RPi.GPIO as GPIO
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ina219 import INA219
from adafruit_ads1x15.analog_in import AnalogIn
import threading
from datetime import datetime
import time

# Initialize the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize the INA219 at address 0x45
ina219 = INA219(i2c, addr=0x45)

# Initialize the ADS1115 at address 0x49
ads = ADS.ADS1115(i2c, address=0x49)

# Define ADC channels
channel_0 = AnalogIn(ads, ADS.P0)
channel_1 = AnalogIn(ads, ADS.P1)
channel_2 = AnalogIn(ads, ADS.P2)
channel_3 = AnalogIn(ads, ADS.P3)

# Define shunt resistance in ohms
SHUNT_OHMS = 470

# Set up GPIO pins as output
pins = [9, 10, 11, 12]
GPIO.setmode(GPIO.BCM)
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# Initialize counters
iv = ov = ic = oc = ivRC = ovRC = p1 = p2 = 0
def create_database():
    """Create the database table if it does not exist."""
    conn = sqlite3.connect('voltage_measurements.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voltage_measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            Voltage_FXS REAL NOT NULL,
            Current_FXS REAL NOT NULL,
            RingVoltage REAL NOT NULL,
            Power REAL NOT NULL,
            voltage_FXS1 REAL NOT NULL,
            voltage_FXS2 REAL NOT NULL,
            current_FXS1 REAL NOT NULL,
            current_FXS2 REAL NOT NULL,
            RingVoltage1 REAL NOT NULL,
            RingVoltage2 REAL NOT NULL,
            Power1 REAL NOT NULL,
            Power2 REAL NOT NULL,
            state TEXT NOT NULL
            
        )
    ''')
    conn.commit()
    conn.close()

def read_voltage(stop_event):
    """Read voltage and save to the database."""
    global iv, ov
    conn = sqlite3.connect('voltage_measurements.db')
    cursor = conn.cursor()
    GPIO.output(9, GPIO.HIGH)   
    try:
        while not stop_event.is_set():
            voltage = (channel_1.voltage + 0.7)* 10
            current = current = (channel_1.voltage * 1000 / SHUNT_OHMS)+15
            power = (ina219.power * 1000)+2
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Check if the voltage is within the range of 44 to 50
            if 44 <= voltage <= 50:
                state = "FXS voltage in average 47V rms"
                iv += 1
                cursor.execute('''
                INSERT INTO voltage_measurements (timestamp, Voltage_FXS, Current_FXS, RingVoltage, Power, voltage_FXS1, 
                                                  voltage_FXS2, current_FXS1, current_FXS2, RingVoltage1, RingVoltage2, 
                                                  Power1, Power2, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, voltage, current, voltage, power, iv, ov, ic, oc, ivRC, ovRC, 0, 0, state))
            else:
                state ="Invalid 47V"
                ov += 1
            cursor.execute('''
                INSERT INTO voltage_measurements (timestamp, Voltage_FXS, Current_FXS, RingVoltage, Power, voltage_FXS1, 
                                                  voltage_FXS2, current_FXS1, current_FXS2, RingVoltage1, RingVoltage2, 
                                                  Power1, Power2, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, voltage, current, voltage, power, iv, ov, ic, oc, ivRC, ovRC, 0, 0, state))
            conn.commit()
            time.sleep(2)
    finally:
        GPIO.output(9, GPIO.LOW)
        conn.close()


def read_current(stop_event):
    """Read current and save to the database."""
    global ic, oc
    conn = sqlite3.connect('voltage_measurements.db')
    cursor = conn.cursor()
    GPIO.output(10, GPIO.HIGH)
    try:
        while not stop_event.is_set():
            voltage = (channel_1.voltage + 0.7)* 10
            current = current = (channel_1.voltage * 1000 / SHUNT_OHMS)+15
            power = (ina219.power * 1000)+2
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if 20 <= current <= 60:
                state = "FXS Current Valid"
                ic += 1
                cursor.execute('''
                INSERT INTO voltage_measurements (timestamp, Voltage_FXS, Current_FXS, RingVoltage, Power, voltage_FXS1, 
                                                  voltage_FXS2, current_FXS1, current_FXS2, RingVoltage1, RingVoltage2, 
                                                  Power1, Power2, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, voltage, current,  voltage, power, iv, ov, ic, oc,ivRC, ovRC, 0, 0, state))
            else:
                state = "FXS Current Invalid"
                oc += 1
            cursor.execute('''
                INSERT INTO voltage_measurements (timestamp, Voltage_FXS, Current_FXS, RingVoltage, Power, voltage_FXS1, 
                                                  voltage_FXS2, current_FXS1, current_FXS2, RingVoltage1, RingVoltage2, 
                                                  Power1, Power2, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, voltage, current,  voltage, power, iv, ov, ic, oc,ivRC, ovRC, 0, 0, state))
            conn.commit()
            time.sleep(2)
    finally:
        GPIO.output(10, GPIO.LOW)
        conn.close()

        
def read_voltage_RC(stop_event):
    """Read ring voltage and save to the database."""
    global ivRC, ovRC
    conn = sqlite3.connect('voltage_measurements.db')
    cursor = conn.cursor()
    GPIO.output(11, GPIO.HIGH)
    try:
        while not stop_event.is_set():
            voltage = (channel_1.voltage-0.2)* 10
            current = (channel_1.voltage * 1000 / SHUNT_OHMS)+15
            power = (ina219.power * 1000)+2
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Check if the voltage is within the range of 35 to 39
            if 35 <= voltage <= 39:
                state = "Ring voltage valid 35V"
                ivRC += 1
                # Insert the values into the database
                cursor.execute('''
                    INSERT INTO voltage_measurements (timestamp, Voltage_FXS, Current_FXS, RingVoltage, Power, voltage_FXS1, 
                                                      voltage_FXS2, current_FXS1, current_FXS2, RingVoltage1, RingVoltage2, 
                                                      Power1, Power2, state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (timestamp, voltage+7, current, voltage, power , iv, ov, ic, oc, ivRC, ovRC, p1, p2, state))
                conn.commit()
                break  # Exit the loop once the voltage is valid
            else:
                state =  "Ring voltage invalid"
                ovRC += 1
                cursor.execute('''
                    INSERT INTO voltage_measurements (timestamp, Voltage_FXS, Current_FXS, RingVoltage, Power, voltage_FXS1, 
                                                      voltage_FXS2, current_FXS1, current_FXS2, RingVoltage1, RingVoltage2, 
                                                      Power1, Power2, state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (timestamp, voltage+10, current, voltage, power , iv, ov, 0, 0, ivRC, ovRC,p1, p2, state))
                conn.commit()
            time.sleep(2)
    finally:
        GPIO.output(11, GPIO.LOW)
        conn.close()


def read_consumption(stop_event):
    """Read power consumption and save to the database."""
    global p1, p2
    conn = sqlite3.connect('voltage_measurements.db')
    cursor = conn.cursor()
    GPIO.output(12, GPIO.HIGH)
    
    try:
        while not stop_event.is_set():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            voltage = (channel_1.voltage + 0.7)* 10
            current = (channel_1.voltage * 1000 / SHUNT_OHMS)+15
            power = (ina219.power * 1000)+2
            
            if 8 < power < 13:
                state ="Power valid"
                p1 += 1
                cursor.execute('''
                    INSERT INTO voltage_measurements (timestamp, Voltage_FXS, Current_FXS, RingVoltage, Power, voltage_FXS1, 
                                                      voltage_FXS2, current_FXS1, current_FXS2, RingVoltage1, RingVoltage2, 
                                                      Power1, Power2, state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (timestamp, voltage, current, voltage, power , iv, ov, ic, oc, ivRC, ovRC, p1, p2, state))
                conn.commit()
                break  
            else:
                state = "Power invalid"
                p2 += 1
                cursor.execute('''
                    INSERT INTO voltage_measurements (timestamp, Voltage_FXS, Current_FXS, RingVoltage, Power, voltage_FXS1, 
                                                      voltage_FXS2, current_FXS1, current_FXS2, RingVoltage1, RingVoltage2, 
                                                      Power1, Power2, state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (timestamp, voltage, current, voltage, power , iv, ov, ic, oc, ivRC, ovRC, p1, p2, state))
                conn.commit()
            
            time.sleep(2)
    finally:
        GPIO.output(12, GPIO.LOW)
        conn.close()


# Main function to run the measurement loop
def main():
    create_database()
    try:
        stop_event = threading.Event()
        # Start voltage reading thread
        voltage_thread = threading.Thread(target=read_voltage, args=(stop_event,))
        voltage_thread.start()
        time.sleep(0.01)
        stop_event.set()
        voltage_thread.join()

        # Start current reading thread
        stop_event.clear()
        current_thread = threading.Thread(target=read_current, args=(stop_event,))
        current_thread.start()
        time.sleep(0.01)
        stop_event.set()
        current_thread.join()

        # Start voltage_RC reading thread
        stop_event.clear()
        voltageRC_thread = threading.Thread(target=read_voltage_RC, args=(stop_event,))
        voltageRC_thread.start()
        time.sleep(0.009)
        stop_event.set()
        voltageRC_thread.join()

        # Start power consumption reading thread
        stop_event.clear()
        consumption_thread = threading.Thread(target=read_consumption, args=(stop_event,))
        consumption_thread.start()
        time.sleep(0.008)
        stop_event.set()
        consumption_thread.join()

    except KeyboardInterrupt:
        stop_event.set()
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
