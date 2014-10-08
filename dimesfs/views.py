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
    if request.user.is_authenticated():
        fs_tags = tsc.query_tags(["tag", "like", "dimes_directory:%"])
    else:
        fs_tags = tsc.query_tags(['tag', 'like', 'dimes_directory:%'],
                  ['data', 'any', Query.tags_any('eq', 'privacy:public')])
    fs_taglist = [t for t in fs_tags]
    print fs_taglist
    fs_pathlist = [t.tag.split(":")[1][1:].split("/") for t in fs_taglist]
    def add(tree, path):
        for node in path:
            tree = tree[node]
    for path in fs_pathlist:
        add(fs_tree, path)
    if "" in fs_tree:
        del fs_tree[""]
    return HttpResponse(json.dumps(fs_tree), content_type="application/json")


def _download_id_to_ofs_url(did):
    uuid = decode(secret, str(did))
    return tsc._api_endpoint("ofs", uuid)


def _download_url_to_ofs_url(url):
    return _download_id_to_ofs_url(url.split('/')[-1])


# http://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html
HTTP_HOP_BY_HOP = set(['connection', 'keep-alive', 'proxy-authenticate',
                       'proxy-authorization', 'te', 'trailers',
                       'transfer-encoding', 'upgrade', ])


def download(request, uri_frag):
    url = _download_id_to_ofs_url(uri_frag)
    headers = {}
    as_attachment = False
    if as_attachment:
        headers['X-As-Attachment'] = 'yes'
    r = requests.get(url, headers=headers, stream=True)
    response = StreamingHttpResponse(r.iter_content())
    for header in r.headers:
        if header in HTTP_HOP_BY_HOP:
            continue
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
        if request.user.is_authenticated():
            files = [d for d in tsc.query_data(Query.tags_any("eq", tag))]
        else:
            tsq = tsc.query_data(Query.tags_any("eq", tag),
                                 Query.tags_any("eq", "privacy:public"))
            files = [d for d in tsq]
        fslist = [{"fname": f.fname, "url": ofs_to_dimes_uri(f.uri)} for f in files]
    return HttpResponse(json.dumps(fslist), content_type="application/json")


def rename(request):
    """POST rename

    Arguments: 
        path_from - path to rename from 
        path to - path to rename to

        data_id - data id to rename
        fname - new name

    """
    if request.method == "POST":
        if request.POST['type'] == 'file':
            uri = _download_url_to_ofs_url(request.POST['uri'])
            fname = request.POST['fname']
            data = tsc.query_data(['uri', 'eq', uri], limit=1, single=True)
            tsc.edit(data.id, data.uri, fname, data.tags)
            return HttpResponse(json.dumps(dict(status='ok')),
                                content_type="application/json")
        elif request.POST['type'] == 'dir':
            path_from = _path_from_json(request.POST['path_from'])
            path_to = _path_from_json(request.POST['path_to'])

            dir_from = "dimes_directory:{0}".format(path_from)
            dir_to = "dimes_directory:{0}".format(path_to)

            tags = tsc.query_tags(["tag", "eq", dir_from])
            for tag in tags:
                tsc.edit_tag(tag.id, dir_to)
            tags = tsc.query_tags(["tag", "like", dir_from + "/%"])
            for tag in tags:
                tsc.edit_tag(tag.id, tag.tag.replace(dir_from, dir_to, 1))
            return HttpResponse(json.dumps(dict(status='ok')),
                                content_type="application/json")


def delete(request):
    """POST delete

    body should be the uri of the file to delete.

    """
    if request.method == "POST":
        if request.POST['type'] == 'file':
            uri = _download_url_to_ofs_url(request.POST['uri'])
            data = tsc.query_data(["uri", "eq", uri], limit=1, single=True)
            if data:
                resp = tsc.delete(data.id)
                return HttpResponse(json.dumps(dict(status='ok')),
                            content_type="application/json")
        elif request.POST['type'] == 'dir':
            path = _path_from_json(request.POST['path'])
            ddir = 'dimes_directory:{0}'.format(path)
            ddir_recurse = '{0}/%'.format(ddir)
            data = tsc.query_data(Query.tags_any('eq', ddir))
            for datum in data:
                tsc.delete(datum.id)
            data = tsc.query_data(
                Query.tags_any('like', ddir_recurse))
            for datum in data:
                tsc.delete(datum.id)
            tags = tsc.query_tags(['tag', 'eq', ddir])
            for tag in tags:
                tsc.delete_tag(tag.id)
            tags = tsc.query_tags(['tag', 'like', ddir_recurse])
            for tag in tags:
                tsc.delete_tag(tag.id)
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
        uri = _download_url_to_ofs_url(request.POST['uri'])
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
