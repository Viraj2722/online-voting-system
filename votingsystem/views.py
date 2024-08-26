from django.shortcuts import render, redirect
import os ,psycopg2
import easygui as e
from django.http import HttpResponse
from dotenv import load_dotenv
load_dotenv()
import supabase 




connection = psycopg2.connect(database=os.getenv("DATABASE_NAME"), 
                              user=os.getenv("DATABASE_USER"),
                                password=os.getenv("DATABASE_PASSWORD"),
                                  host=os.getenv("DATABASE_HOST"),
                                    port=os.getenv("DATABASE_PORT"))
cursor = connection.cursor()
cursor.execute("SELECT * FROM voter") # Missing closing quotation mark
record = cursor.fetchall()
# print(record)

def home(request):
    return render(request, 'home.html')

def candidate_login(request):
    if request.method == 'POST':
        voter_id = request.POST['voter_id']
        mobileno = request.POST['mobileno']

        cursor.execute('SELECT * FROM voter WHERE "Voterid" = {voter_id}  AND "VoterNumber" ={mobileno}'.format(voter_id=voter_id, mobileno=mobileno))
        record = cursor.fetchone()
        
        # Check if the voter exists
        if record:
            return redirect('candidatelist')
        else:
            return render(request, 'candidatelogin.html', {'alert_message': 'Invalid Voter ID or Mobile Number'})

           
            
            # JavaScript code with a simulated alert function
            # return render(request, 'candidatelogin.html')
            

    return render(request, 'candidatelogin.html')

    
    
def admin_login(request):
    if request.method == 'POST':
        adminid =  request.POST['admin_id']
        
        cursor.execute('SELECT * FROM admin WHERE "Adminid" = \'{adminid}\' ' .format(adminid=adminid))
        record = cursor.fetchone()

        
        # Check if the admin exists
        if record:
            return redirect('adminpage')
        else:
            e.msgbox('Invalid Admin ID ', 'Error')
            return render(request, 'adminlogin.html')
    
    return render(request, 'adminlogin.html')

def admin_page(request):
    if request.method == 'POST':
        leader_name = request.POST['leader_name']
        symbol = request.FILES['symbol']
        # Add logic to save political leader and symbol
        return redirect('home')

    return render(request, 'adminpage.html')

def candidate_list(request):
    return render(request, 'candidatelist.html')


