from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse, reverse_lazy
from django.core import serializers
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.conf import settings
from datetime import datetime, date, timedelta
from django import forms
import simplejson, string, re

#import models and forms here
from main.models import *
from main.forms import *
from main.views_common import *

def party_details(request, pk):
    rc={}
    return render_to_response("main/party/party_details.html", rc, context_instance=RequestContext(request))

@login_required
def party_create(request):
    rc={'error':None}
    now = datetime.datetime.now()
    defaults = {}
    defaults['day'] = now.strftime("%m/%d/%y")
    def clean_time(s):
        return s.lower().lstrip('0')
    defaults['start_time'] = clean_time(now.strftime("%I:%M%p"))
    defaults['end_time'] = clean_time((now+timedelta(hours=1)).strftime("%I:%M%p"))
    defaults['location'] = "W20: Stratton Student Center"
    defaults['lng'] = "-71.094774920000006"
    defaults['lat'] = "42.359042619999997"
    defaults['building_img'] = "http://web.mit.edu/campus-map/objimgs/object-W20.jpg"
    defaults['title']=defaults['agenda']=defaults['klass']=defaults['room']=""
    form = PartyCreateForm(defaults)
    if request.method=="POST":
        form = PartyCreateForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            party = Party()
            party.starttime = d['start_time']
            party.endtime = d['end_time']
            party.day = d['day']
            party.title = d['title']
            party.agenda = d['agenda']
            party.location = d['location']
            party.room = d['room']
            party.lat = d['lat']
            party.lng = d['lng']
            party.building_img = d['building_img']
            try:
                klass = re.search("\w+\.\w+", d['klass'])
                if klass:
                    party.class_obj = ClassNumber.objects.get(number=klass.group()).class_obj
                    party.save()
                    party.attendees.add(request.user)
                    party.admins.add(request.user)
                    return redirect(reverse('main.party_views.party_details', kwargs={'pk':party.pk}))
            except Exception as e:
                rc['errors'] = "Class Number is invalid"
                raise e
        else:
            rc['errors'] = "There were errors in the form. Please make sure that all the fields are filled out."
    rc['form'] = form
    return render_to_response("main/party/party_create.html", rc, context_instance=RequestContext(request))

def party_registered(request, pk):
    rc={}
    rc['event_name']='MOOMOMOO'
    rc['event_location']="Building 35"
    rc['event_time']="Monday, December 25 at 11:30pm"
    rc['title']="Let the games begin!"
    rc['pk']=pk
    return render_to_response("main/party/party_registered.html", rc, context_instance=RequestContext(request))

def party_unregistered(request, pk):
    rc={}
    rc['event_name']='MOOMOMOO'
    rc['event_location']="Building 35"
    rc['event_time']="Monday, December 25 at 11:30pm"
    rc['title']="Party Pooper :("
    rc['pk']=pk
    return render_to_response("main/party/party_unregistered.html", rc, context_instance=RequestContext(request))

def party_must_login(request, pk):
    rc={}
    rc['pk']=pk
    return render_to_response("main/party/party_login.html", rc, context_instance=RequestContext(request))

def party_register_ajax(request, party_pk):
    r = {}
    r["status"]="success"
    r['registered']=True
    r['link'] = reverse('main.party_views.party_registered',kwargs={'pk':party_pk})
    return r

def party_unregister_ajax(request, party_pk):
    r = {}
    r["status"]="success"
    r['registered']=True
    r['link'] = reverse('main.party_views.party_unregistered',kwargs={'pk':party_pk})
    return r

#ajax handler for handling party update information and party delete
def ajax(request):
    result={'status':"none"}
    try:
        verb = request.REQUEST.get('verb',None)
        party_pk = request.REQUEST.get('pk',None)
        if verb=='isregistered':
            result = {"status": "success", "attending":False}
        elif verb=='get_attend_button':
            return render_to_response('main/party/attend_button.html',{'pk':party_pk})
        elif verb=='register':
            result=party_register_ajax(request, party_pk)
        elif verb=='unregister':
            result=party_unregister_ajax(request, party_pk)
        else:
            result['status']="verb didn't match"
    except Exception as e:
        result['status']="error: "+ str(e)
    json=simplejson.dumps(result)
    return HttpResponse(json, mimetype="application/json")

