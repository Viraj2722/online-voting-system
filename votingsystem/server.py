import socket
import os
import threading
import psycopg2
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

# Database connection details
DB_PARAMS = {
    'database': os.getenv("DATABASE_NAME"),
    'user': os.getenv("DATABASE_USER"),
    'password': os.getenv("DATABASE_PASSWORD"),
    'host': os.getenv("DATABASE_HOST"),
    'port':  os.getenv("DATABASE_PORT")
}

# Thread lock to ensure that vote casting is handled sequentially
lock = threading.Lock()

def get_db_connection():
    """Establish a new connection to the database."""
    return psycopg2.connect(**DB_PARAMS)

def client_thread(conn):
    """Handle each client connection in a separate thread."""
    try:
        data = conn.recv(1024).decode()  # Receiving voter details
        vote = conn.recv(1024).decode()
        print(f"Data received: {data}")
       

        log = data.split(' ')
        voter_id = int(log[0])
        mobileno = log[1]

        # Get the connection and cursor for the current client
        connection = get_db_connection()
        cursor = connection.cursor()

        # Verify voter credentials
        cursor.execute('SELECT "IsVoted" FROM voter WHERE "Voterid" = %s AND "VoterNumber" = %s', [voter_id, mobileno])
        record = cursor.fetchone()

        if record:
            if record[0]:  # True means already voted
                print(f'Vote Already Cast by ID: {voter_id}')
            else:
                print(f'Voter Logged in... ID: {voter_id}')
        else:
            print('Invalid Voter')
            
            return
        
        # Receive vote from the client
        
        
        print(f"Vote Received from ID: {voter_id}. Processing...")

        print(f"Vote Casted Successfully by voter ID = {voter_id} to Candidate = {vote}")
        conn.send("Successful".encode())

    except Exception as e:
        print(f'Error: {e}')
        conn.send("Error".encode())

    finally:
        # Always close the connection and database resources
        cursor.close()
        connection.close()
        conn.close()

def voting_server():
    """Main server function to handle incoming connections."""
    serversocket = socket.socket()
    host = '127.0.0.1'
    port = 4001

    try:
        serversocket.bind((host, port))
    except socket.error as e:
        print(f"Socket binding error: {e}")
        return

    print("Waiting for the connection")
    serversocket.listen(10)
    print(f"Listening on {host}:{port}")

    while True:
        try:
            client, address = serversocket.accept()
            print('Connected to:', address)

            client.send("Connection Established".encode())

            # Start a new thread for each client
            t = Thread(target=client_thread, args=(client,))
            t.start()

        except Exception as e:
            print(f"Error accepting connections: {e}")
            continue

    serversocket.close()

if __name__ == '__main__':
    voting_server()
