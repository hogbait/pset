from django.shortcuts import get_object_or_404, render_to_response, redirect, render
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse, reverse_lazy
from django.core import serializers
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib.auth.models import User
from django.conf import settings
from datetime import datetime, date
from django.template import loader, Context
import urllib
from django import forms
from itertools import chain

#import models and forms here
from main.models import *
from main.forms import *

def string_or_blank(s):
    if s:
        return str(s)
    return ""

#replacing the default login_required with our own
def login_required(f):
    def login_required_func(*args, **kwargs):
        if args[0].user.is_authenticated():
            #for debugging purposes only: automatically generate userinfos so no error
            if not UserInfo.objects.filter(user=args[0].user).exists():
                UserInfo(user=args[0].user).save()
            else:
                args[0].user.user_info.save()
            return f(*args,**kwargs)
        return HttpResponseRedirect(reverse('main.account_views.login_page')+"?next="+urllib.quote(args[0].get_full_path()))
    return login_required_func
   
def all_newsfeed(request, feedtype, pk, page=1):
    rc={}
    page = int(page)
    rc['feed'] = get_newsfeed(feedtype, pk, page)
    rc['next'] = reverse('main.views_common.all_newsfeed', kwargs={'feedtype':feedtype, 'pk':pk, 'page':page+1})
    if page>1:
        rc['prev'] = reverse('main.views_common.all_newsfeed', kwargs={'feedtype':feedtype, 'pk':pk, 'page':page-1})
    rc['page'] = page
    rc['feed']['link'] = None
    return render(request, 'main/modules/all_newsfeed.html', rc)

def get_newsfeed(feedtype, pk, page=1):
    r={}
    r['link'] = reverse("main.views_common.all_newsfeed", kwargs={'feedtype':feedtype, 'page':1, 'pk':pk})
    r['header']="Recent Activity"
    NUM_PER_PAGE=6
    if feedtype=="profile":
        newsfeed1 = Activity.objects.filter(target__target_type='User', target__target_id=pk).exclude(activity_type='comment').order_by('-time_created')[:page*NUM_PER_PAGE]

        newsfeed2 = Activity.objects.filter(actor__pk=pk).order_by('-time_created')[:page*NUM_PER_PAGE]
        r['feed'] = sorted(chain(newsfeed1,newsfeed2),key=lambda x: x.time_created)[page*NUM_PER_PAGE-1:(page-1)*NUM_PER_PAGE-1:-1]
        n = User
    if feedtype=='class':
        r['feed'] = Activity.objects.filter(target__target_type='Class', target__target_id=pk).exclude(activity_type='comment').order_by('-time_created')[(page-1)*NUM_PER_PAGE:page*NUM_PER_PAGE]
        n=Class
    if feedtype=='party':
        r['feed'] = Activity.objects.filter(target__target_type='Party', target__target_id=pk).exclude(activity_type='comment').order_by('-time_created')[(page-1)*NUM_PER_PAGE:page*NUM_PER_PAGE]
        n=Party
    #get the name of the thingy
    try:
        r['name'] = n.objects.get(pk=pk).get_name()
    except Exception as e:
        pass
    return r


def send_email(request, to, subject, template, rc):
    html = loader.get_template('emails/'+template)
    c = RequestContext(request, rc)
    from_email = 'InTheLoop@babymastodon.com'
    msg = EmailMultiAlternatives(subject, html.render(c), from_email, [to])
    msg.content_subtype = "html"
    msg.send()
