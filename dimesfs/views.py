import json
import os
from collections import defaultdict

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from tagstore.client import TagStoreClient, Query


tsc = TagStoreClient(settings.TS_API_ENDPOINT)


def fslist(request):
    Tree = lambda: defaultdict(Tree) # did you mean recursion?
    fs_tree = Tree()
    fs_tags = tsc.query_tags(["tag", "like", "dimes_directory:%"])
    fs_taglist = [t for t in fs_tags]
    fs_pathlist = [t.tag.split(":")[1][1:].split("/") for t in fs_taglist]
    def add(tree, path):
        for node in path:
            tree = tree[node]
    for path in fs_pathlist:
        add(fs_tree, path)
    del fs_tree[""]
    return HttpResponse(json.dumps(fs_tree), content_type="application/json")

def _path_from_json(string):
    return "/" + "/".join(json.loads(string))

@csrf_exempt
def dirflist(request):
    fslist=[]
    if request.method == "POST":
        tag = "dimes_directory:" + _path_from_json(request.body)
        files = [d for d in tsc.query_data(Query.tags_any("eq", tag))]
        fslist = [{"fname": f.fname, "url": f.uri} for f in files]
    return HttpResponse(json.dumps(fslist), content_type="application/json")


def delete(request):
    """POST delete

    body should be the uri of the file to delete.

    """
    if request.method == "POST":
        uri = request.POST['uri']
        data = tsc.query_data(["uri", "eq", uri], limit=1, single=True)
        if data:
            resp = tsc.delete(data.id)
            return HttpResponse(json.dumps(dict(status='ok')),
                        content_type="application/json")
    return HttpResponse(json.dumps(dict(status='failed')),
                        content_type="application/json")


def upload(request):
    path = _path_from_json(request.POST['path'])
    blob = request.FILES['file']
    path = os.path.normpath(path)
    if path == '.':
        path = ''
    tags = ['dimes_directory:{0}'.format(path)]
    resp = tsc.create(blob, unicode(blob), tags)
    if request.is_ajax():
        return HttpResponse(json.dumps(dict(fname=resp.fname, url=resp.uri)),
                            content_type="application/json")
    else:
        return redirect(request.META['HTTP_REFERER'])


def index(request):
    return render(request, "dimesfs/index.html")
