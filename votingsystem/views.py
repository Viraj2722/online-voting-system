from django.shortcuts import render, redirect

def home(request):
    return render(request, 'home.html')

def candidate_login(request):
    if request.method == 'POST':
        voter_id = request.POST['voter_id']
        dob = request.POST['dob']
        # Add logic to authenticate voter
        return redirect('home')
    return render(request, 'candidatelogin.html')

def admin_login(request):
    if request.method == 'POST':
        leader_name = request.POST['leader_name']
        symbol = request.FILES['symbol']
        # Add logic to save political leader and symbol
        return redirect('home')
    return render(request, 'adminlogin.html')
