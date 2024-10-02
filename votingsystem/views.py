from django.shortcuts import render, redirect
import os
import psycopg2
from dotenv import load_dotenv
import socket
from django.http import HttpResponse

# Load environment variables
load_dotenv()

# Establish database connection
connection = psycopg2.connect(
    database=os.getenv("DATABASE_NAME"), 
    user=os.getenv("DATABASE_USER"),
    password=os.getenv("DATABASE_PASSWORD"),
    host=os.getenv("DATABASE_HOST"),
    port=os.getenv("DATABASE_PORT")
)
cursor = connection.cursor()

# Dictionary to store socket connections
socket_connections = {}

# Fetch records for use in login functions
cursor.execute("SELECT * FROM voter")
voter_records = cursor.fetchall()

# List to store political leaders
political_leaders = []
cursor.execute('SELECT "CandidateName", "CandidatePosition", "VotingCount" FROM candidatedetails')
politicaldata = cursor.fetchall()

for i in politicaldata:
    political_leaders.append({
        'leader_name': i[0],
        'position': i[1],
        'Votingcount': i[2]
    })


def home(request):
    return render(request, 'home.html')


# Logic for candidate login with socket connection
def candidate_login(request):
    if request.method == 'POST':
        voter_id = request.POST['voter_id']
        mobileno = request.POST['mobileno']

        # Check if voter exists
        cursor.execute(
            'SELECT * FROM voter WHERE "Voterid" = %s AND "VoterNumber" = %s',
            [voter_id, mobileno]
        )
        record = cursor.fetchone()
        
        if record:
            # Check if voter has already voted
            if record[2]:  
                return render(request, 'candidatelogin.html', {
                    'alert_message': 'You have already voted.'
                })
            else:
                request.session['voter_id'] = voter_id 
                request.session['mobileno'] = mobileno  
                # Create socket connection if it doesn't exist for this session
                
                if voter_id not in socket_connections:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_address = ('127.0.0.1', 4001) 
                    sock.connect(server_address)
                    socket_connections[voter_id] = sock  

                return redirect('candidatelist')  
        else:
            return render(request, 'candidatelogin.html', {
                'alert_message': 'Invalid Voter ID or Mobile Number'
            })

    return render(request, 'candidatelogin.html')


# Logic for admin login
def admin_login(request):
    if request.method == 'POST':
        adminid = request.POST['admin_id']
        
        cursor.execute(
            'SELECT * FROM admin WHERE "Adminid" = %s',
            [adminid]
        )
        record = cursor.fetchone()

        if record:
            return redirect('adminpage')
        else:
            return render(request, 'adminlogin.html', {'alert_admin_message': 'Invalid Admin ID'})
    
    return render(request, 'adminlogin.html')


# Logic for about us page
def about_page(request):
    return render(request, 'aboutpage.html')


# Logic for admin page
def admin_page(request):
    global political_leaders

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            leader_name = request.POST['leader_name']
            position = request.POST['position']

            political_leaders.append({
                'leader_name': leader_name,
                'position': position,
                'Votingcount': 0  
            })

            cursor.execute(
                'INSERT INTO candidatedetails ("CandidateName", "CandidatePosition", "VotingCount") VALUES (%s, %s, 0)',
                [leader_name, position]
            )
            connection.commit()

        elif action == 'delete':
            leader_name = request.POST['leader_name']
            delete_leader(leader_name)

            political_leaders = [leader for leader in political_leaders if leader['leader_name'] != leader_name]
         
        elif action == 'refresh':
            return redirect('adminpage')
    
        return redirect('adminpage')
    
      

    return render(request, 'adminpage.html', {'political_leaders': political_leaders})


# Function to delete leader from the database
def delete_leader(leader_name):
    cursor.execute(
        'DELETE FROM candidatedetails WHERE "CandidateName" = %s',
        [leader_name]
    )
    connection.commit()


# Logic for candidate list
def candidate_list(request):
    global political_leaders
    return render(request, 'candidatelist.html', {'political_leaders': political_leaders})


# Logic to cast a vote using the socket connection
def cast_vote(request):
    if request.method == 'POST':
        voter_id  = request.session.get('voter_id') 
        mobilenumber = request.session.get('mobileno')  
       
        cursor.execute(
            'SELECT "IsVoted" FROM voter WHERE "Voterid" = %s', [voter_id]
        )
        is_voted = cursor.fetchone()[0]

        if not is_voted:
            leader_name = request.POST.get('vote')

            if voter_id in socket_connections:
                sock = socket_connections[voter_id]  

                try:
                    
                    sock.sendall(f"{voter_id} {mobilenumber}".encode())  
                    sock.sendall(leader_name.encode())  

                    # Wait for the server's response
                    response = sock.recv(1024).decode()  # Receive the response from the server
                    print(f" Server response: {response}")

                    response = sock.recv(1024).decode()
                    print(f"Voting  response: {response}")

                    

                    if response == "Successful":
                        # Voting successful, show success message
                        cursor.execute(
                            'UPDATE candidatedetails SET "VotingCount" = "VotingCount" + 1 WHERE "CandidateName" = %s', [leader_name]
                        )
                        connection.commit()
                        for leader in political_leaders:
                          if leader['leader_name'] == leader_name:
                             leader['Votingcount'] += 1 
                        
                        cursor.execute(
                            'UPDATE voter SET "IsVoted" = TRUE WHERE "Voterid" = %s', [voter_id]
                        )
                        connection.commit()
                        

                        return redirect('home')
                    else:
                        # Voting failed, show error message
                        return render(request, 'candidatelogin.html', {
                            'alert_message': 'Voting failed. Please try again later.'
                        })
                except Exception as e:
                    # Handle socket communication errors
                    return render(request, 'candidatelogin.html', {
                        'alert_message': f'Server error: {str(e)}. Please try again later.'
                    })

                finally:
                    # Close socket and clean up after vote is cast
                    sock.close()
                    del socket_connections[voter_id] 

        else:
            return render(request, 'candidatelogin.html', {
                'alert_message': 'You have already voted.'
            })

    return HttpResponse("Invalid request method", status=405)


# Logic for logging out
def logout(request):
    if request.method == 'POST':
        if request.POST.get('logout'):
            if 'sock' in request.session:
                request.session['sock'].close()  # Close the socket on logout
                del request.session['sock']  # Clear session
            return redirect('home')

    return render(request, 'logout.html')
