import socket
import os
import threading
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Database connection details
DB_PARAMS = {
    'database': os.getenv("DATABASE_NAME"),
    'user': os.getenv("DATABASE_USER"),
    'password': os.getenv("DATABASE_PASSWORD"),
    'host': os.getenv("DATABASE_HOST"),
    'port': os.getenv("DATABASE_PORT")
}

# Thread lock to ensure that actions are handled sequentially
lock = threading.Lock()

def get_db_connection():
    """Establish a new connection to the database."""
    return psycopg2.connect(**DB_PARAMS)

def client_thread(conn):
    """Handle each client connection in a separate thread."""
    try:
        # Receiving voter details and vote
        data = conn.recv(1024).decode()
        print(f"Data received: {data}")

        # Split the received data
        log = data.split(' ')
        voter_id = log[0]
        mobileno = log[1]
        vote = log[2]  # Assuming the vote is sent after voter details

        with lock:  # Ensure that this block runs one at a time
            connection = get_db_connection()
            cursor = connection.cursor()

            # Verify voter credentials
            cursor.execute('SELECT "IsVoted" FROM voter WHERE "Voterid" = %s AND "VoterNumber" = %s', [voter_id, mobileno])
            record = cursor.fetchone()

            if record:
                if record[0]:  # True means already voted
                    print(f'Vote Already Cast by ID: {voter_id}')
                    conn.send("Error: Already voted".encode())
                else:
                    print(f'Voter Logged in... ID: {voter_id}')
                    print(f"Vote Received: Voter ID = {voter_id}, Candidate = {vote}")
                    conn.send("Vote Received".encode())
            else:
                print('Invalid Voter')
                conn.send("Error: Invalid voter".encode())

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

    print("Waiting for connections...")
    serversocket.listen(10)
    print(f"Listening on {host}:{port}")

    while True:
        try:
            client, address = serversocket.accept()
            print('Connected to:', address)

            client.send("Connection Established".encode())

            # Start a new thread for each client
            t = threading.Thread(target=client_thread, args=(client,))
            t.start()

        except Exception as e:
            print(f"Error accepting connections: {e}")
            continue

    serversocket.close()

if __name__ == '__main__':
    voting_server()
