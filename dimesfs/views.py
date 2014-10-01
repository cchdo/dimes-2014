import json
import os.path
from collections import defaultdict
import os

from django.conf import settings
from django.shortcuts import render
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

@csrf_exempt
def dirflist(request):
    fslist=[]
    if request.method == "POST":
        #probably won't work on a non *nix OS
        tag = "dimes_directory:" + os.path.join("/", *json.loads(request.body))
        files = [d for d in tsc.query_data(Query.tags_any("eq", tag))]
        fslist = [f.fname for f in files]
    return HttpResponse(json.dumps(fslist), content_type="application/json")


def upload(request):
    path = request.POST['path']
    blob = request.FILES['file']
    path = os.path.normpath(path)
    if path == '.':
        path = ''
    tags = ['dimes_directory:/{0}'.format(path)]
    resp = tsc.create(blob, unicode(blob), tags)
    return HttpResponse(json.dumps(dict(uri=resp.uri)),
                        content_type="application/json")


def index(request):
    return render(request, "dimesfs/index.html")
