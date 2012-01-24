from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse, reverse_lazy
from django.core import serializers
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.conf import settings
from datetime import datetime, date
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template import loader, Context
from django import forms
import random
import urllib
import re

#import models and forms here
from main.models import *
from main.forms import *
from main.views_common import *
from BeautifulSoup import BeautifulSoup

def fetch_fullname(username):
    # Returns tuple: [firstName, lastName]
    params = urllib.urlencode({'query':username})
    htmldoc = urllib.urlopen("http://web.mit.edu/bin/cgicso?options=general&" + params)
    soup = BeautifulSoup(htmldoc.read())
    data = soup.find('pre') or [1] # put in array with one element in case connection failed
    #data='   name: Drach, Zachary email: <a href="mailto:zdrach@MIT.EDU">zdrach@MIT.EDU</a> address: MacGregor House # F413 year: 1 '
    if len(data) <= 1:
        return ("","")
    else:
        m = re.search("(?<=name: )(\w+), (\w+)", data.contents[0])
        if m == None:
            return ("","") 
        name = (str(m.group(2)), str(m.group(1)))  # [firstName, lastName]
        return name

#Helper functions
#function for creating and saving account
def createAccount(email="", username="", first_name="", last_name="", 
                  password="", is_active=True):
    user = User.objects.create_user(username, email=email, password=password)
    user.is_active = is_active
    if not first_name and not last_name:
        (first_name, last_name) = fetch_fullname(username)
    user.first_name = first_name
    user.last_name = last_name
    user.save()
    userdata = UserInfo()
    userdata.user = user
    userdata.save()
    
    return user

#views start here
def profile_page(request, pk):
    rc={}
    return render_to_response("main/account/profile_page.html", rc, 
                              context_instance=RequestContext(request))

@login_required
def my_profile_page(request):
    return profile_page(request, request.user.pk)

@login_required
def profile_edit(request):
    rc={}
    return render_to_response("main/account/profile_edit.html", rc, 
                              context_instance=RequestContext(request))

@login_required
def profile_new_user_info(request):
    rc={}
    return render_to_response("main/account/profile_new_user_info.html", rc, 
                              context_instance=RequestContext(request))

def create_account_page(request):
    rc={}
    form = EmailRegisterForm()
    if request.method=="POST":
        form = EmailRegisterForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['pw1']==form.cleaned_data['pw2']:
                email=form.cleaned_data['email']
                uname=email.split("@")[0]
                account=createAccount(email=email, 
                                      username=uname, 
                                      password=form.cleaned_data['pw1'], 
                                      is_active=False)
                h = "%032x" % random.getrandbits(128)
                ph = PendingHash(user=account, hashcode=h)
                ph.save()
                t = loader.get_template('emails/verify.txt')
                html = loader.get_template('emails/verify.html')
                root_email = request.get_host()
                c = RequestContext(request, {
                    'username':uname,
                    'web_root': root_email,
                    'h':h,
                })
                subject = 'Email Verification'
                from_email, to = 'no-reply@babymastodon.com', email
                msg = EmailMultiAlternatives(subject, t.render(c), 
                                             from_email, [to])
                msg.attach_alternative(html.render(c), "text/html")
                msg.send()
                rc['email'] = form.cleaned_data['email']
                return render_to_response(
                  "main/account/create_from_email_sent.html", 
                  rc, context_instance=RequestContext(request)
                )
            rc['error']="Passwords don't match"
    rc['form'] = form
    return render_to_response("main/account/create_account_page.html", 
                              rc, context_instance=RequestContext(request))

def verify(request, hashcode):
    rc={}
    user = authenticate(hashcode=hashcode)
    if not user:
        render_to_response("main/account/verify_expired.html", 
                                  rc, context_instance=RequestContext(request))
    rc['next']=reverse('main.home_views.home_page')#redirect to home after login
    login(request,user)
    return render_to_response("main/account/verify.html", rc, 
                              context_instance=RequestContext(request))

def link_to_facebook(request):
    rc={}
    return render_to_response("main/account/link_to_facebook.html", rc, 
                              context_instance=RequestContext(request))

def login_page(request):
    rc={}
    n = request.GET.get('next',"/")
    if request.user.is_authenticated():
        return HttpResponseRedirect(n)
    form = LoginForm()
    if request.method=="POST":
        form = LoginForm(request.POST)
        n = request.POST['next']
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], 
                                password=form.cleaned_data['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect(n)
        rc['error']=True
    if n:
        rc['next']=n
    rc['form']=form
    return render_to_response("main/account/login_page.html", rc, 
                              context_instance=RequestContext(request))

def login_facebook(request):
    rc={}
    return render_to_response("main/account/login_facebook.html", rc, 
                              context_instance=RequestContext(request))

def logout_view(request):
    if request.user.is_authenticated():
        logout(request)
    return redirect("main.home_views.front_page")

