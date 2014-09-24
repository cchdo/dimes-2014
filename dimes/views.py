from django.shortcuts import render, render_to_response
from django.template import RequestContext

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
    return render_to_response('data.html', {},
        context_instance=RequestContext(request))

def fieldwork(request):
    return render_to_response('fieldwork.html', {},
        context_instance=RequestContext(request))

def cruise_page(request, page_for=""):
    #find all files tagged with cruise:page_for
    #do stuff with those data...
    files = []

    return render_to_response('cruise_page.html', {"files":files, "page_for":page_for},
        context_instance=RequestContext(request))

def cruise_reports(request):
    return render_to_response('cruise_reports.html', {},
        context_instance=RequestContext(request))

def media(request):
    return render_to_response('media.html', {},
        context_instance=RequestContext(request))

def index(request):
    return render_to_response('index.html', {},
        context_instance=RequestContext(request))

