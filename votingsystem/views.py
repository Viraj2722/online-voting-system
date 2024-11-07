import os
import random
from django.shortcuts import render, redirect
from dotenv import load_dotenv
from twilio.rest import Client
import psycopg2
import socket

load_dotenv()

# Twilio and database setup
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

connection = psycopg2.connect(
    database=os.getenv("DATABASE_NAME"),
    user=os.getenv("DATABASE_USER"),
    password=os.getenv("DATABASE_PASSWORD"),
    host=os.getenv("DATABASE_HOST"),
    port=os.getenv("DATABASE_PORT")
)
cursor = connection.cursor()

def send_otp(mobile_number, otp):
    try:
        message = twilio_client.messages.create(
            from_="+19293252516",
            body=f"OTP for the voting is: {otp}",
            to=f'+91{mobile_number}'
        )
        print(f"OTP sent to {mobile_number}: {message.sid}")
    except Exception as e:
        print(f"Error sending OTP: {e}")
        raise

def candidate_login(request):
    if request.method == 'POST':
        voter_id = request.POST.get('voter_id')
        mobileno = request.POST.get('mobileno')
        send_otp_button = request.POST.get('send_otp')
        otp_entered = request.POST.get('otp')

        # Check if the voter exists
        cursor.execute(
            'SELECT "IsVoted", "otp" FROM voter WHERE "Voterid" = %s AND "VoterNumber" = %s',
            [voter_id, mobileno]
        )
        record = cursor.fetchone()

        if record is None:
            return render(request, 'candidatelogin.html', {
                'alert_message': 'Invalid Voter ID or Mobile Number.',
                'show_otp': False,
                'voter_id': voter_id,
                'mobileno': mobileno
            })

        is_voted = record[0]
        stored_otp = record[1]

        if is_voted:
            return render(request, 'candidatelogin.html', {
                'alert_message': 'You have already voted.',
                'show_otp': False,
                'voter_id': voter_id,
                'mobileno': mobileno
            })

        request.session['voter_id'] = voter_id
        request.session['mobileno'] = mobileno

        if otp_entered:
            if stored_otp and str(stored_otp) == otp_entered:
                return redirect('candidatelist')
            else:
                return render(request, 'candidatelogin.html', {
                    'alert_message': 'Invalid OTP, please try again.',
                    'show_otp': True,
                    'voter_id': voter_id,
                    'mobileno': mobileno
                })

        if send_otp_button == 'send_otp':
            if not is_voted: 
                otp = random.randint(10000, 99999)
                cursor.execute(
                    'UPDATE voter SET "otp" = %s WHERE "Voterid" = %s',
                    [otp, voter_id]
                )
                connection.commit()
                print(f"OTP sent for voter_id: {voter_id} to mobile: {mobileno} with OTP: {otp}")
                #send_otp(mobileno, otp)  # Send OTP via Twilio
                print("otp send", otp)
                return render(request, 'candidatelogin.html', {
                    'show_otp': True,
                    'voter_id': voter_id,
                    'mobileno': mobileno
                })

    return render(request, 'candidatelogin.html')

def candidate_list(request):
    if not request.session.get('live_voting_enabled', False):
        return render(request, 'voting_disabled.html', {
            'alert_message': 'Live voting is currently disabled.'
        })

    # Fetch and display candidate list
    political_leaders = []
    cursor.execute('SELECT "CandidateName", "CandidatePosition", "VotingCount" FROM candidatedetails')
    politicaldata = cursor.fetchall()

    for i in politicaldata:
        political_leaders.append({
            'leader_name': i[0],
            'position': i[1],
            'Votingcount': i[2]
        })

    return render(request, 'candidatelist.html', {'political_leaders': political_leaders})

def cast_vote(request):
    if request.method == 'POST':
        voter_id = request.session.get('voter_id')
        mobilenumber = request.session.get('mobileno')
        leader_name = request.POST.get('vote')

        if not voter_id or not mobilenumber:
            return render(request, 'home.html', {
                'alert_message': 'Please log in to vote.'
            })

        cursor.execute(
            'SELECT "IsVoted" FROM voter WHERE "Voterid" = %s',
            [voter_id]
        )
        record = cursor.fetchone()
        if record and record[0]:  # Voter has already voted
            return render(request, 'candidatelogin.html', {
                'alert_message': 'You have already voted.'
            })

        # Handle voting via socket
        message = f"{voter_id} {mobilenumber} {leader_name}"

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect(('127.0.0.1', 4001))
                client_socket.send(message.encode())

                response = client_socket.recv(1024).decode()
                print(f"Server response: {response}")

                if response.startswith("Error"):  # Error response from the server
                    return render(request, 'candidatelogin.html', {
                        'alert_message': response,
                    })
                else:
                    cursor.execute(
                        'UPDATE candidatedetails SET "VotingCount" = "VotingCount" + 1 WHERE "CandidateName" = %s',
                        [leader_name]
                    )
                    connection.commit()  # Commit the changes

                    cursor.execute(
                        'UPDATE voter SET "IsVoted" = TRUE WHERE "Voterid" = %s',
                        [voter_id]
                    )
                    connection.commit()  # Commit the changes

                    return redirect('home')

        except socket.error as e:
            print(f"Error connecting to the server: {e}")
            return render(request, 'home.html', {
                'alert_message': 'Could not connect to the voting server.'
            })

        except Exception as e:
            print(f"Error occurred: {e}")
            return render(request, 'home.html', {
                'alert_message': 'An unexpected error occurred, please try again.'
            })

    return render(request, 'home.html')

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

def admin_page(request):
    political_leaders = []
    cursor.execute('SELECT "CandidateName", "CandidatePosition", "VotingCount" FROM candidatedetails')
    politicaldata = cursor.fetchall()

    for i in politicaldata:
        political_leaders.append({
            'leader_name': i[0],
            'position': i[1],
            'Votingcount': i[2]
        })

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'start_live_voting':
            request.session['live_voting_enabled'] = True
            return redirect('adminpage')

        elif action == 'stop_live_voting':
            request.session['live_voting_enabled'] = False
            return redirect('adminpage')

        elif action == 'add':
            leader_name = request.POST['leader_name']
            position = request.POST['position']

            cursor.execute(
                'INSERT INTO candidatedetails ("CandidateName", "CandidatePosition", "VotingCount") VALUES (%s, %s, 0)',
                [leader_name, position]
            )
            connection.commit()
            return redirect('adminpage')

        elif action == 'delete':
            leader_name


def admin_page(request): 
    # Fetch the list of candidates from the database
    political_leaders = []
    cursor = connection.cursor()
    cursor.execute('SELECT "CandidateName", "CandidatePosition", "VotingCount" FROM candidatedetails')
    politicaldata = cursor.fetchall()

    for i in politicaldata:
        political_leaders.append({
            'leader_name': i[0],
            'position': i[1],
            'Votingcount': i[2]
        })

    if request.method == 'POST':
        action = request.POST.get('action')

        # Handle live voting toggle (start/stop)
        if action == 'start_live_voting':
            request.session['live_voting_enabled'] = True
            return redirect('adminpage')

        elif action == 'stop_live_voting':
            request.session['live_voting_enabled'] = False
            return redirect('adminpage')

        elif action == 'add':
            leader_name = request.POST['leader_name']
            position = request.POST['position']

            cursor.execute(
                'INSERT INTO candidatedetails ("CandidateName", "CandidatePosition", "VotingCount") VALUES (%s, %s, 0)',
                [leader_name, position]
            )
            connection.commit()
            return redirect('adminpage')

        elif action == 'delete':
            leader_name = request.POST['leader_name']
            delete_leader(leader_name)
            return redirect('adminpage')

        elif action == 'refresh':
            return redirect('adminpage')

    # Pass the live voting status to the template
    return render(request, 'adminpage.html', {
        'political_leaders': political_leaders,
    })


def delete_leader(leader_name):
    cursor.execute(
        'DELETE FROM candidatedetails WHERE "CandidateName" = %s',
        [leader_name]
    )
    connection.commit()

def logout(request):
    if request.method == 'POST':
        if request.POST.get('logout'):
            if 'voter_id' in request.session:
                del request.session['voter_id']
                del request.session['mobileno']  
            return redirect('home')

    return render(request, 'logout.html')

def about_page(request):
    return render(request, 'aboutpage.html')

def home(request):
    return render(request, 'home.html')
