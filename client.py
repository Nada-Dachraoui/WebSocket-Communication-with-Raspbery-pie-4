import asyncio
import websockets
import sqlite3
import csv
import os
import subprocess
# Chemins des fichiers
db_path = '/home/Nada/voltage_measurements.db'
csv_path = '/home/Nada/voltage_measurements.csv'
ID_path = '/home/Nada/report.txt'

def get_serial():
    """Get the serial number of the Raspberry Pi."""
    try:
        result = subprocess.run(["cat", "/proc/cpuinfo"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if line.startswith("Serial"):
                return line.split(": ")[1]
        return "Unknown"
    except Exception as e:
        print(f"Error getting serial number: {e}")
        return "Unknown"
    
def create_info_file(filename):
    """Create a text file with the Raspberry Pi's serial number."""
    try:
        serial = get_serial()
        with open(filename, 'w') as f:
            f.write(f"Serial Number: {serial}\n")
        print(f"File '{filename}' created successfully with serial number.")
    except Exception as e:
        print(f"Error creating info file: {e}")
async def send_csv(websocket, file_path):
    """Send a CSV file over the WebSocket."""
    try:
        with open(file_path, 'rb') as file:
            while (chunk := file.read(4096)):
                await websocket.send(chunk)
        await websocket.send("END_OF_FILE")
    except Exception as e:
        print(f"Error sending CSV file: {e}")
async def send_txt(websocket, file_path):
    """Send a text file over the WebSocket."""
    try:
        with open(file_path, 'rb') as file:
            while (chunk := file.read(4096)):
                await websocket.send(chunk)
        await websocket.send("END_OF_FILE_TXT")
    except Exception as e:
        print(f"Error sending text file: {e}")
        
def create_csv(file_path):
    """Create a CSV file from the database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        headers = ["id", "timestamp", "Voltage_FXS", "Current_FXS", "RingVoltage", "Power", 
                   "voltage_FXS1", "voltage_FXS2", "current_FXS1", "current_FXS2", 
                   "RingVoltage1", "RingVoltage2", "Power1", "Power2", "state"]
        cursor.execute('SELECT * FROM voltage_measurements')
        rows = cursor.fetchall()

        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows)
        conn.close()
        print(f"CSV file '{file_path}' created successfully.")
    except Exception as e:
        print(f"Error creating CSV file: {e}")


async def main():
    """Main function to connect to the WebSocket server and perform file operations."""
    uri = "ws://192.168.1.13:8765"  # Assurez-vous que cela correspond à l'IP et au port du serveur
    try:
        create_csv(csv_path)
        create_info_file(ID_path)
        async with websockets.connect(uri) as websocket:
            # Recevoir le message de bienvenue avec l'adresse IP
            message = await websocket.recv()
            print(f"Received message: {message}")
            # Envoyer le fichier CSV
            await websocket.send("SEND_CSV")
            await send_csv(websocket, csv_path)
            # Envoyer le fichier texte avec le numéro de série
            await websocket.send("SEND_TXT")
            await send_txt(websocket, ID_path)
            # Tester l'état dans le CSV reçu
            await websocket.send("TEST_STATE")
            state_test_results = await websocket.recv()
            print(f"Received state test results:\n{state_test_results}")
    except Exception as e:
        print(f"Error in WebSocket communication: {e}")
if __name__ == "__main__":
    asyncio.run(main())
