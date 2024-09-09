from django.shortcuts import render, redirect
import os
import psycopg2
from dotenv import load_dotenv
from django.http import HttpResponse

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
cursor.execute('SELECT "CandidateName" , "CandidatePosition", "VotingCount" FROM candidatedetails')
politicaldata = cursor.fetchall()

for i in politicaldata:
    political_leaders.append({
        'leader_name': i[0],
        'position': i[1],
        'Votingcount': i[2]
    })

print(political_leaders)

def home(request):
    return render(request, 'home.html')


# Logic for candidate login
# Logic for candidate login
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
            if record[2]:  # record[2] is "IsVoted" field (True/False)
                # Instead of rendering a template, use JavaScript to show alert and redirect
                return render(request, 'candidatelogin.html', {
                    'alert_message': 'You have already voted. '
                })
            else:
                request.session['voter_id'] = voter_id  # Save voter ID in session
                return redirect('candidatelist')  # Redirect to candidate list if not voted
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
                'Votingcount': 0  # Initialize vote count to 0 for new candidate
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

        # Redirect to the admin page to allow for new entries
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


# Logic to cast a vote for a candidate
def cast_vote(request):
    if request.method == 'POST':
        voter_id = request.session.get('voter_id')  # Get voter ID from session

        # Check if voter has already voted
        cursor.execute(
            'SELECT "IsVoted" FROM voter WHERE "Voterid" = %s', [voter_id]
        )
        is_voted = cursor.fetchone()[0]

        if not is_voted:
            leader_name = request.POST.get('vote')

            # Increment the vote count for the selected candidate
            cursor.execute(
                'UPDATE candidatedetails SET "VotingCount" = "VotingCount" + 1 WHERE "CandidateName" = %s', 
                [leader_name]
            )
            connection.commit()

            # Mark the voter as having voted
            cursor.execute(
                'UPDATE voter SET "IsVoted" = TRUE WHERE "Voterid" = %s',
                [voter_id]
            )
            connection.commit()

            # After successful vote, redirect to login
            return redirect('candidatelogin')
        else:
            return render(request, 'candidatelogin.html')

    return HttpResponse("Invalid request method", status=405)
    return HttpResponse("Invalid request method", status=405)


# Logic for logging out
def logout(request):
    if request.method == 'POST':
        if request.POST.get('logout'):
            return redirect('home')

    return render(request, 'logout.html')