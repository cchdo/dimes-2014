from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import logout as auth_logout
from django.conf import settings

def components(request):
    return render_to_response('components.html', {},
        context_instance=RequestContext(request))

def people(request):
    return render_to_response('people.html', {},
        context_instance=RequestContext(request))

def publications(request):
    return render_to_response('publications.html', {},
        context_instance=RequestContext(request))

def data(request):
    cruises0 = [
        dict(id='US1', ship='R/V Revelle', dates='2009'),
        dict(id='UK1', ship='James Cook', dates='2009',
             link='http://www.bodc.ac.uk/projects/international/dimes/data_inventories/cruise/jc041/'),
        dict(id='US2', ship='R/V Thompson', dates='2010'),
        dict(id='UK2', ship='RRS James Clark Ross', dates='2010-2011',
             link='http://www.bodc.ac.uk/projects/international/dimes/data_inventories/cruise/jc054/'),
        dict(id='US3'),
        dict(id='UK2.5', ship='RRS James Clark Ross',
             link='http://www.bodc.ac.uk/projects/international/dimes/data_inventories/cruise/jr20110409/'),
    ]

    cruises1 = [
        dict(id='UK3', ship='RRS James Cook', dates='2011-2012',
             link='http://www.bodc.ac.uk/projects/international/dimes/data_inventories/cruise/jc069/'),
        dict(id='UK4', ship='RRS James Clark Ross', dates='2013'),
        dict(id='US5'),
        dict(id='UK5'),
        dict(id='UK2014', ship='RRS James Cook'),
    ]
    return render_to_response('data.html', {"cruises0": cruises0, "cruises1":
                                            cruises1},
        context_instance=RequestContext(request))

def fieldwork(request):
    return render_to_response('fieldwork.html', {},
        context_instance=RequestContext(request))

def cruise_page(request, page_for=""):
    #find all files tagged with cruise:page_for
    #do stuff with those data...
    files = []

    return render_to_response('cruise_page.html',
                              {"files": files, "page_for": page_for},
                              context_instance=RequestContext(request))

def cruise_reports(request):
    return render_to_response('cruise_reports.html', {},
        context_instance=RequestContext(request))

def data_policy(request):
    return render_to_response('data_policy.html', {},
        context_instance=RequestContext(request))

def outreach(request):
    return render_to_response('outreach.html', {},
        context_instance=RequestContext(request))

def index(request):
    return render_to_response('index.html', {},
        context_instance=RequestContext(request))

def logout(request):
    auth_logout(request)
    return redirect(settings.LOGIN_REDIRECT_URL)
