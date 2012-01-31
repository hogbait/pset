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
from django import forms

#import models and forms here
from main.models import *
from main.forms import *
from main.views_common import *

import re

def front_page(request):
    rc={}
    user = request.user
    if user.is_authenticated():
        return home_page(request)
    rc['rform'] = EmailRegisterForm() 
    return render_to_response("main/home/front_page.html", rc, context_instance=RequestContext(request))

@login_required
def home_page(request):
    rc={}
    user = request.user
    now=timezone.now()
    personalized = personalized_party_query(request)
    rc['numparties'] = personalized.count()
    rc['newsfeed'] = get_newsfeed(request,'personalized')
    rc['myclasses'] = ({'ob':a, 'n':a.party_set.filter(endtime__gt=now, active=True).count()} for a in request.user.user_info.klasses.all())
    rc['calendar'] = get_history(request, 'person', request.user.pk, time="future")
    return render_to_response("main/home/home_page.html", rc, context_instance=RequestContext(request))

def about(request):
    rc={}
    return render_to_response("main/home/about.html", rc, context_instance=RequestContext(request))

