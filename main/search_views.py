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
from haystack.query import SearchQuerySet
import logging, simplejson, string, re
from django.core import serializers

#import models and forms here
from main.models import *
from main.forms import *
from main.views_common import *

RESULTS_PER_PAGE = getattr(settings,'RESULTS_PER_PAGE',10)
logger = logging.getLogger(__name__)

def parties_by_class(request, pk):
    rc={}
    return render_to_response("main/search/parties_by_class.html", rc, context_instance=RequestContext(request))

def parties_by_date(request):
    rc={}
    return render_to_response("main/search/parties_by_date.html", rc, context_instance=RequestContext(request))

trunc = lambda s,n: s if len(s)<n-3 else s[:n-3]+"..."

#takes a search query and an optional category. If no category, it tries to intelligently guess the
#cagetory. If the search query contains a class number, the search will try to make that result first
#it returns a dict with name, description, (picture), and related classes if a class. If a person,
#returns dict with name, class, department, (picture)
#format: {'page':int, 'numpages':int, 'results':[{'title':string,'description':string,'metadata':string}]}
def exec_search(query, category=None, page=1):
    numpages=0
    result_items=[]
    pageresults=0
    totalresults=0
    sqs=None
    if query:
        wildcard_tokens = string.join([a+'* ' for a in query.split()])
        if not category:#do multiple searches and decide what the user is looking for
            if re.match(".*\d+.*", query):
                category="Classes"
            else:
                q1 = wildcard_tokens + ' django_ct:(main.class)'
                q2 = wildcard_tokens + ' django_ct:(main.userinfo)'
                sqs1 = SearchQuerySet().raw_search(q1)
                sqs2 = SearchQuerySet().raw_search(q2)
                l1 = len(sqs1)
                l2 = len(sqs2)
                if l1>l2:
                    category="Classes"
                    sqs = sqs1
                else:
                    category="People"
                    sqs=sqs2
        if category=="Classes":
            if not sqs:
                if re.match(".*\d+.*", query):
                    q = '"' + query+ '"' + ' django_ct:(main.classnumber)'
                else:
                    q = wildcard_tokens + ' django_ct:(main.class)'
                sqs = SearchQuerySet().raw_search(q)
            totalresults = len(sqs)
            numpages = totalresults/RESULTS_PER_PAGE+1
            pageresults = totalresults if totalresults < RESULTS_PER_PAGE else RESULTS_PER_PAGE
            tmp = [a.object for a in sqs[page*RESULTS_PER_PAGE:(page+1)*RESULTS_PER_PAGE]]
            for a in tmp:
                item={}
                item['title'] = trunc(a.get_title(),45)
                item['description'] = trunc(a.get_description(),250)
                item['metadata'] = 'Class Numbers: '+string.join([x.number for x in a.get_meta()],', ')
                item['link']=reverse("main.search_views.parties_by_class", kwargs={'pk':a.pk})
                result_items.append(item)
    prwidth = 4
    pagerange = range(1,numpages+1)[max(page-prwidth-1,0):][:prwidth*2+1]
    return {'page':page,'numpages':numpages, 'result_items':result_items, 'category':category, 'pageresults':pageresults, 'totalresults':totalresults, 'pagerange':pagerange}

def search_page(request):
    rc={}
    query = request.GET.get('q','')
    category = request.GET.get('c',None)
    page = request.GET.get('page',0)
    rc['query']=query
    rc['category']=category
    rc['results'] = exec_search(query=query, category=category, page=page)
    return render_to_response("main/search/search_page.html", rc, context_instance=RequestContext(request))

def ajax_s(request):
    result={'status':"none"}
    try:
        if request.method=="GET":
            verb = request.GET.get('verb',None)
            query = request.GET.get('q',None)
            category = request.GET.get('c',None)
            page = int(request.GET.get('page',"0"))
            if verb=='search_page':
                result['results'] = exec_search(query=query, category=category, page=page)
                result['status'] = "success"
            else:
                result['status']="verb didn't match"
    except Exception as e:
        result['status']="error: "+ str(e)
    json=simplejson.dumps(result)
    return HttpResponse(json, mimetype="application/json")
