# This Code id for Client 

import asyncio
import websockets
import sqlite3
import csv

# Path to the SQLite database and the CSV file

db_path = '/home/Nada/voltage_measurements.db'
csv_path = '/home/Nada/voltage_measurements.csv'

# Asynchronous function to send the CSV file over WebSocket
async def send_csv(websocket, file_path):
    with open(file_path, 'rb') as file:  
        while chunk := file.read(4096):
            await websocket.send(chunk)  
    await websocket.send("END_OF_FILE") 

# Function to create a CSV file from the database
def create_csv(file_path):
    """Create a CSV file with headers and data from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()  
  
    headers = ["id", "timestamp", "Voltage", "Current", "VoltageRC", "voltage_repos1", "voltage_repos2", "voltage_repos3", 
               "current1", "current2", "current3", "voltage_RC1", "voltage_RC2", "voltage_RC3", "state"]                    # Defines the CSV headers according to the structure of your database 
  
    cursor.execute('SELECT * FROM voltage_measurements')  # Executes a query to fetch all data from the table
    rows = cursor.fetchall()  # Fetches all rows of the query result
    with open(file_path, mode='w', newline='') as file:  # Opens the CSV file in write mode
        writer = csv.writer(file)  # Creates a CSV writer object
        writer.writerow(headers)  # Writes the header row
        writer.writerows(rows)  # Writes the data rows
    conn.close()  # Closes the database connection
    print(f"CSV file '{file_path}' created successfully.")  # Prints a confirmation message

async def main():
    uri = "ws://192.168.1.15:8765"  # Replace with the IP address of your WebSocket server
    create_csv(csv_path)  # Creates the CSV file from the database
    async with websockets.connect(uri) as websocket:
        message = await websocket.recv() 
        print(f"Received message: {message}")

        # Sends the CSV file to the server
        await websocket.send("SEND_CSV")
        await send_csv(websocket, csv_path)

        # Requests the last column from the server
        await websocket.send("GET_LAST_COLUMN")
        last_column_message = await websocket.recv() 
        print(f"Received last column:\n{last_column_message}")

# Runs the asynchronous main function
if __name__ == "__main__":
    asyncio.run(main())





