from django.shortcuts import render, render_to_response
from django.template import RequestContext

def about(request):
    return render_to_response('about.html', {},
        context_instance=RequestContext(request))

def components(request):
    return render_to_response('components.html', {},
        context_instance=RequestContext(request))

def contact(request):
    return render_to_response('contact.html', {},
        context_instance=RequestContext(request))

def index(request):
    return render_to_response('index.html', {},
        context_instance=RequestContext(request))
