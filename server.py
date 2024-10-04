import asyncio
import websockets
import os
import pandas as pd

db_path = 'received_data.csv'
txt_path = 'received_report.txt'


async def receive_csv(websocket):
    with open(db_path, 'wb') as file:
        while True:
            message = await websocket.recv()
            if message == "END_OF_FILE":
                break
            file.write(message)
    print("CSV file received and saved as 'received_data.csv'.")


async def receive_txt(websocket):
    with open(txt_path, 'wb') as file:
        while True:
            message = await websocket.recv()
            if message == "END_OF_FILE_TXT":
                break
            file.write(message)
    print("Text file received and saved as 'received_report.txt'.")



async def fetch_last_column(csv_file_path):
    """Fetch the last column from a CSV file."""
    try:
        df = pd.read_csv(csv_file_path)
        if df.empty:
            print(f"No data found in the CSV file '{csv_file_path}'.")
            return pd.Series()  # Return an empty Series on error or if the file is empty
        last_column = df.iloc[:, -1]
        return last_column
    except Exception as e:
        print(f"Error reading CSV file '{csv_file_path}': {e}")
        return pd.Series()  # Return an empty Series on error
    
async def test_state(websocket):
    """Test states from the last column of the CSV file and send results back."""
    column = await fetch_last_column(db_path)
    states_to_test = [
        "Invalid 47V",
        "FXS Current Invalid",
        "Ring voltage invalid",
        "Power invalid"
    ]
    results = {state: (state in column.values) for state in states_to_test}
    found_any = any(results.values())
    print("State test results:")
    for state, exists in results.items():
        print(f"{state}: {'Found' if exists else 'Not Found'}")
    try:
        await websocket.send(f"State test results:\n{results}")
    except Exception as e:
        print(f"Error sending state test results: {e}")
    return 1 if found_any else 0

async def handler(websocket, path):
    """Handle WebSocket connections and messages."""
    client_ip = websocket.remote_address[0]
    print(f"Client connected with IP: {client_ip}")
    try:
        await websocket.send(f"Your IP address is {client_ip}")
        async for message in websocket:
            if message == "SEND_CSV":
                await receive_csv(websocket)
            elif message == "SEND_TXT":
                await receive_txt(websocket)
            elif message == "TEST_STATE":
                state_found = await test_state(websocket)
                print(f"State found: {state_found}")

    except websockets.ConnectionClosed as e:
        print(f"WebSocket connection closed: {e}")

    except Exception as e:
        print(f"Error handling WebSocket message: {e}")

async def main():
    """Start the WebSocket server."""
    try:
        server = await websockets.serve(handler, '0.0.0.0', 8765)
        print("WebSocket server running on ws://0.0.0.0:8765")
        await server.wait_closed()
    except Exception as e:
        print(f"Error starting WebSocket server: {e}")
if __name__ == "__main__":
    asyncio.run(main())
