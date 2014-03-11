from django.contrib.auth.views import login as django_login
from django.shortcuts import render, redirect
from authentication.forms import RegistrationForm

def login(request, *args, **kwargs):
    return django_login(request, template_name='authentication/login.html')

def register(request, *args, **kwargs):
    if request.method == 'POST':
        registration_form = RegistrationForm(request.POST)
        if registration_form.is_valid():
            registration_form.save()
            return redirect('/login/')
    else:
        registration_form = RegistrationForm()
    return render(request, 'authentication/registration.html', {'registration_form': registration_form})