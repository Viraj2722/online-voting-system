from django.shortcuts import render, redirect
import os
import psycopg2
from dotenv import load_dotenv

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

# Fetch records for use in login functions
cursor.execute("SELECT * FROM voter")
voter_records = cursor.fetchall()

# List to store political leaders
political_leaders = []

def home(request):
    return render(request, 'home.html')


#Logic for candidate login
def candidate_login(request):
    if request.method == 'POST':
        voter_id = request.POST['voter_id']
        mobileno = request.POST['mobileno']

        cursor.execute(
            'SELECT * FROM voter WHERE "Voterid" = %s AND "VoterNumber" = %s',
            [voter_id, mobileno]
        )
        record = cursor.fetchone()
        
        if record:
            return redirect('candidatelist')
        else:
            return render(request, 'candidatelogin.html', {'alert_message': 'Invalid Voter ID or Mobile Number'})

    return render(request, 'candidatelogin.html')



#Logic for admin login
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



#Logic for admin page
def admin_page(request):
    global political_leaders

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            leader_name = request.POST['leader_name']
            position = request.POST['position']

            political_leaders.append({
                'leader_name': leader_name,
                'position': position
            })

            cursor.execute(
                'INSERT INTO candidatedetails ("CandidateName", "CandidatePosition") VALUES (%s, %s)',
                [leader_name, position]
            )
            connection.commit()

        elif action == 'delete':
            leader_name = request.POST['leader_name']
            delete_leader(leader_name)

            political_leaders = [leader for leader in political_leaders if leader['leader_name'] != leader_name]

        # Redirect to the admin page to allow for new entries
        return redirect('adminpage')

    return render(request, 'adminpage.html', {'political_leaders': political_leaders})





#function to delete leader from database
def delete_leader(leader_name):
    cursor.execute(
        'DELETE FROM candidatedetails WHERE "CandidateName" = %s',
        [leader_name]
    )
    connection.commit()





#Logic for candidate list
def candidate_list(request):
    return render(request, 'candidatelist.html')
