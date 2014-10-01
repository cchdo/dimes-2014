import json
from collections import defaultdict

from django.shortcuts import render
from django.http import HttpResponse

from tagstore.client import TagStoreClient, Query


def fslist(request):
    Tree = lambda: defaultdict(Tree) # did you mean recursion?
    fs_tree = Tree()
    tsc = TagStoreClient("http://umi.local:5000/api/v1")
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

def dirflist(request):
    fslist=[]
    return HttpResponse(json.dumps(flist), content_type="application/json")

def index(request):
    return render(request, "dimesfs/index.html")
