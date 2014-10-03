import json
import os
import base64
from collections import defaultdict
from zipfile import ZipFile
from tempfile import SpooledTemporaryFile
from shutil import copyfileobj

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, StreamingHttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

import requests

from tagstore.client import TagStoreClient, Query

secret = "66969bfac21f5dba5e3d" # 10 bytes

tsc = TagStoreClient(settings.TS_API_ENDPOINT)

#http://stackoverflow.com/a/2490718
def encode(key, string):
    encoded_chars = []
    for i in xrange(len(string)):
        key_c = key[i % len(key)]
        encoded_c = chr(ord(string[i]) + ord(key_c) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = "".join(encoded_chars)
    return base64.urlsafe_b64encode(encoded_string)
 
 
def decode(key, string):
    decoded_chars = []
    string = base64.urlsafe_b64decode(string)
    for i in xrange(len(string)):
        key_c = key[i % len(key)]
        encoded_c = chr(abs(ord(string[i]) - ord(key_c) % 256))
        decoded_chars.append(encoded_c)
    decoded_string = "".join(decoded_chars)
    return decoded_string


def _path_from_json(string):
    return "/" + "/".join(json.loads(string))


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


def download(request, uri_frag):
    uuid = decode(secret, str(uri_frag))
    r = requests.get(settings.TS_API_ENDPOINT + "/ofs/" + uuid + "?as_attachment",
            stream=True)
    def get_ofs(r):
        for l in r.iter_lines():
            yield l
    response = StreamingHttpResponse(get_ofs(r))
    for header in r.headers:
        response[header] = r.headers[header]
    return response

def ofs_to_dimes_uri(s):
    base = "/dimesfs/download/" 
    uuid = s.split("/")[-1]
    uuid_hidden = encode(secret, uuid)
    return base + uuid_hidden


@csrf_exempt
def dirflist(request):
    fslist=[]
    if request.method == "POST":
        tag = "dimes_directory:" + _path_from_json(request.body)
        files = [d for d in tsc.query_data(Query.tags_any("eq", tag))]
        fslist = [{"fname": f.fname, "url": ofs_to_dimes_uri(f.uri)} for f in files]
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


def unzip(request):
    if request.method == "POST":
        uri = request.POST['uri']
        data = tsc.query_data(["uri", "eq", uri], limit=1, single=True)

        # make the new dimes directory, current dimes directory + zipname
        old_dir = [tag for tag in data.tags if
                   tag.startswith('dimes_directory:')]
        tags = [tag for tag in data.tags if not
                tag.startswith('dimes_directory:')]
        if not old_dir:
            raise Http404()
        old_dir = old_dir[0].split(':')[1]
        zipdirname = os.path.splitext(data.fname)[0].replace('/', '-')
        new_dir = os.path.join(old_dir, zipdirname)

        # put the new tag onto the old tags
        dir_tag = 'dimes_directory:{0}'.format(new_dir)
        tags.append(dir_tag)

        fobj = data.open()
        with SpooledTemporaryFile(max_size=2**26) as tfile:
            copyfileobj(fobj, tfile)
            tfile.seek(0)
            with ZipFile(tfile, 'r') as zfile:
                for info in zfile.infolist():
                    fname = info.filename
                    if fname.startswith('__MACOSX'):
                        continue
                    with zfile.open(info) as fobj:
                        tsc.create(fobj, fname, tags)
        return HttpResponse(json.dumps(dict(dirname=zipdirname)),
                            content_type="application/json")


def index(request):
    return render(request, "dimesfs/index.html")
