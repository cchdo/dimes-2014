import json
from collections import defaultdict
import os

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from tagstore.client import TagStoreClient, Query

ts_api_endpoint = "http://umi.local:5000/api/v1"

def fslist(request):
    Tree = lambda: defaultdict(Tree) # did you mean recursion?
    fs_tree = Tree()
    tsc = TagStoreClient(ts_api_endpoint)
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
    tsc = TagStoreClient(ts_api_endpoint)
    if request.method == "POST":
        #probably won't work on a non *nix OS
        tag = "dimes_directory:" + os.path.join("/", *json.loads(request.body))
        files = [d for d in tsc.query_data(Query.tags_any("eq", tag))]
        fslist = [f.fname for f in files]
    return HttpResponse(json.dumps(fslist), content_type="application/json")

def index(request):
    return render(request, "dimesfs/index.html")
