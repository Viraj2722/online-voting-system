
from django.shortcuts import render, redirect
import os ,psycopg2
import easygui as e
from dotenv import load_dotenv
load_dotenv()


connection = psycopg2.connect(database=os.getenv("DATABASE_NAME"), 
                              user=os.getenv("DATABASE_USER"),
                                password=os.getenv("DATABASE_PASSWORD"),
                                  host=os.getenv("DATABASE_HOST"),
                                    port=os.getenv("DATABASE_PORT"))
cursor = connection.cursor()
cursor.execute("SELECT * FROM voter")
record = cursor.fetchall()
# print(record)

def home(request):
    return render(request, 'home.html')

def candidate_login(request):
    if request.method == 'POST':
        voter_id = request.POST['voter_id']
        mobileno = request.POST['mobileno']

        cursor.execute("SELECT * FROM voter WHERE voterid=%s AND voter_number=%s", (voter_id, mobileno))
        record = cursor.fetchone()
        
        # Check if the voter exists
        if record:
            return redirect('candidatelist')
        else:
            e.msgbox('Invalid Voter ID or Mobile Number', 'Error')
            return render(request, 'candidatelogin.html')
            

    return render(request, 'candidatelogin.html')

    
    
def admin_login(request):
    if request.method == 'POST':
        adminid =  request.POST['admin_id']
        
        cursor.execute("SELECT * FROM voteradmin WHERE adminid = '{adminid}' ".format(adminid=adminid))
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


