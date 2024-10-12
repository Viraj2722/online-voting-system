import os
import random
import json
from django.shortcuts import render, redirect
from dotenv import load_dotenv
from twilio.rest import Client
import psycopg2
import socket


load_dotenv()


TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# Path to store OTPs
OTP_STORAGE_FILE = 'otp_storage.json'


connection = psycopg2.connect(
    database=os.getenv("DATABASE_NAME"),
    user=os.getenv("DATABASE_USER"),
    password=os.getenv("DATABASE_PASSWORD"),
    host=os.getenv("DATABASE_HOST"),
    port=os.getenv("DATABASE_PORT")
)
cursor = connection.cursor()

# Function to load OTPs from file
def load_otps():
    try:
        with open(OTP_STORAGE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}





# Function to save OTPs to file
def save_otps(otps):
    with open(OTP_STORAGE_FILE, 'w') as f:
        json.dump(otps, f)





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




# Candidate Login Logic
def candidate_login(request):
    if request.method == 'POST':
        voter_id = request.POST.get('voter_id')
        mobileno = request.POST.get('mobileno')
        send_otp_button = request.POST.get('send_otp') 
        otp_entered = request.POST.get('otp') 


        otps = load_otps()

       
        cursor.execute(
            'SELECT "IsVoted" FROM voter WHERE "Voterid" = %s AND "VoterNumber" = %s',
            [voter_id, mobileno]
        )
        record = cursor.fetchone()

        if record:
            is_voted = record[0]
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
            stored_otp_data = otps.get(voter_id)
            if stored_otp_data and str(stored_otp_data['otp']) == otp_entered:
                return redirect('candidatelist')
            else:
                return render(request, 'candidatelogin.html', {
                    'alert_message': 'Invalid OTP, please try again.',
                    'show_otp': True,
                    'voter_id': voter_id,
                    'mobileno': mobileno
                })

       
        if send_otp_button == 'send_otp':
            if record and not is_voted: 
                print(f"Send OTP clicked for voter_id: {voter_id}, mobileno: {mobileno}") 
                otp = random.randint(10000, 99999)
                otps[voter_id] = {'otp': otp, 'mobileno': mobileno}
                save_otps(otps)

                print("OTP generated: ", otp)
                
                #send_otp(mobileno, otp)

                return render(request, 'candidatelogin.html', {
                    'show_otp': True,
                    'voter_id': voter_id,
                    'mobileno': mobileno
                })
            else:
                return render(request, 'candidatelogin.html', {
                    'alert_message': 'Invalid Voter ID or Mobile Number.',
                    'show_otp': False,
                    'voter_id': voter_id,
                    'mobileno': mobileno
                })

    return render(request, 'candidatelogin.html')








# Candidate List Logic
def candidate_list(request):
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






# Logic to cast a vote
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
        if record and record[0]: 
            return render(request, 'candidatelogin.html', {
                'alert_message': 'You have already voted.'
            })

      
        message = f"{voter_id} {mobilenumber} {leader_name}"

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.connect(('127.0.0.1', 4001))
                client_socket.send(message.encode())

                
                response = client_socket.recv(1024).decode()
                print(f"Server response: {response}")

                if response.startswith("Error"):
                    return render(request, 'candidatelogin.html', {
                        'alert_message': response,
                    })
                else:
                    
                    cursor.execute(
                        'UPDATE candidatedetails SET "VotingCount" = "VotingCount" + 1 WHERE "CandidateName" = %s',
                        [leader_name]
                    )
                    connection.commit()

                    
                    cursor.execute(
                        'UPDATE voter SET "IsVoted" = TRUE WHERE "Voterid" = %s',
                        [voter_id]
                    )
                    connection.commit()

                    return redirect('home')

            except Exception as e:
                print(f"Error connecting to the server: {e}")
                return render(request, 'home.html', {
                    'alert_message': 'Could not connect to the voting server.'
                })

    return render(request, 'home.html')









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





# Logic for admin page (add, delete candidates, refresh)
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





# Logic for logging out
def logout(request):
    if request.method == 'POST':
        if request.POST.get('logout'):
            if 'voter_id' in request.session:
                del request.session['voter_id']
                del request.session['mobileno']  # Clear session
            return redirect('home')

    return render(request, 'logout.html')




# About page logic
def about_page(request):
    return render(request, 'aboutpage.html')




# Home page logic
def home(request):
    return render(request, 'home.html')
