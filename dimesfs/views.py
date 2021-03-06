import json
import os
import base64
from collections import defaultdict
from zipfile import ZipFile
from tempfile import SpooledTemporaryFile

from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import (
    HttpResponse, StreamingHttpResponse, Http404, 
)
from django.views.decorators.csrf import csrf_exempt

import requests

from tagstore.client import TagStoreClient, Query


secret = "66969bfac21f5dba5e3d" # 10 bytes

tsc = TagStoreClient(settings.TS_API_ENDPOINT, results_per_page=50,
        preload_page_num_results=50,)

TAG_WEBSITE = "website:dimes"
TAG_PATH_PREFIX = 'path:dimes'

TAG_OTHER_DATA = "Other"

TAGS_CRUISE = (
        'US1', 'US2', 'US3', 'US4', 'US5', 'UK1', 'UK2', 'UK2.5', 'UK3', 'UK4',
        'UK5',
    )
TAGS_DATA_TYPE = ('CTD', 'ADCP', 'LADCP', 'SADCP', 'XBT', 'microstructure', 
        'XCTD', 'underway', 'thermosalinograph',
        'navigation', 'bathymetry', 'tracer',
        'floats', 'drifters', 'bottle',
        )


def _check_auth(func):
    def checker(request):
        if not request.user.is_authenticated():
            return redirect(reverse('login', kwargs=dict(next=request.path)))
        return func(request)
    return checker


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


def _path_dimes(path):
    return '{0}:{1}'.format(TAG_PATH_PREFIX, path)


def _path_from_json(string):
    return "/" + "/".join(json.loads(string))


def fslist(request):
    Tree = lambda: defaultdict(Tree) # did you mean recursion?
    fs_tree = Tree()
    def add(tree, path):
        for node in path:
            tree = tree[node]

    view = request.GET.get("view", None)

    if view:
        value = request.GET.get("value", None)
        primary_tag = view + ":" + value

        if view == "cruise" and value in TAGS_CRUISE:
            secondary_tag = "data_type:%"
        elif view == "data_type" and value in TAGS_DATA_TYPE:
            secondary_tag = "cruise:%"
        else:
            add(fs_tree, ["{0} is an unknown value for {1}".format(value, view)])
            return HttpResponse(json.dumps(fs_tree), content_type="application/json")

        filters = [
                ["tag", "like", secondary_tag],
                ["data", "any", Query.tags_any("eq", primary_tag)],
                ]
        if not request.user.is_authenticated():
            filters.append(["data", "any", Query.tags_any("eq", "privacy:public")])

        fs_tags = tsc.query_tags(*filters, preload=True)
        fs_pathlist = [[t.tag.split(":")[1]] for t in fs_tags]

        other_files = tsc.query_data(
                Query.tags_any('like', primary_tag),
                ['tags', 'not_any', ['tag', 'like', secondary_tag]],
                )

        if other_files:
            fs_pathlist.append([TAG_OTHER_DATA])

        if len(fs_pathlist) is 0:
            add(fs_tree, ["No data are available from this {0}".format(view)])
        for path in fs_pathlist:
            add(fs_tree, path)
    else:
        filters = [["tag", "like", _path_dimes("%")]]
        if not request.user.is_authenticated():
            filters.append(["data", "any", Query.tags_any("eq", "privacy:public")])
        fs_tags = tsc.query_tags(*filters, preload=True)
        fs_pathlist = [t.tag.split(":")[2][1:].split("/") for t in fs_tags]
        for path in fs_pathlist:
            add(fs_tree, path)

    try:
        del fs_tree[""]
    except KeyError:
        pass
    return HttpResponse(json.dumps(fs_tree), content_type="application/json")


def _download_id_to_ofs_url(did):
    uuid = decode(secret, str(did))
    return tsc._api_endpoint("ofs", uuid)


DOWNLOAD_URI_BASE = '/dimesfs/download/'


def _download_url_to_ofs_url(url):
    if url.startswith(DOWNLOAD_URI_BASE):
        return _download_id_to_ofs_url(url.split('/')[-1])
    return url


def ofs_to_dimes_uri(s):
    if tsc._is_local(s):
        uuid = s.split("/")[-1]
        uuid_hidden = encode(secret, uuid)
        return DOWNLOAD_URI_BASE + uuid_hidden
    return s


# http://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html
HTTP_HOP_BY_HOP = set(['connection', 'keep-alive', 'proxy-authenticate',
                       'proxy-authorization', 'te', 'trailers',
                       'transfer-encoding', 'upgrade', ])


def _proxy(response):
    """Convert a requests response to a StreamingHttpResponse."""
    # chunk_size defaults to 1 byte if not set here, small values of chunk_size
    # will cause data transfer slowness, and TCP request overhead to make up
    # abotu 95% of the data transfer
    resp = StreamingHttpResponse(response.iter_content(chunk_size=2**20))
    for header in response.headers:
        if header in HTTP_HOP_BY_HOP:
            continue
        resp[header] = response.headers[header]
    return resp


def download(request, uri_frag):
    url = _download_id_to_ofs_url(uri_frag)
    headers = {}
    as_attachment = False
    if as_attachment:
        headers['X-As-Attachment'] = 'yes'
    r = requests.get(url, headers=headers, stream=True)
    return _proxy(r)


def tag_value(data, key):
    """Return the value for a tag key on a given data.

    This gives no consideration for more than one tag having the same tag key.
    It merely returns the first encountered.

    Raises:
        KeyError - if the tag key does not exist

    """
    prefix = '{0}:'.format(key)
    for tag in data.tags:
        if tag.startswith(prefix):
            return tag[len(prefix):]
    raise KeyError()

def _add_dirs_arclist(name_list, datum, *dirs):
    path = os.path.join("/", *dirs)
    arcname = os.path.join(path, datum.fname)
    name_list.append((datum.id, arcname))

def download_zip(request):
    view = request.GET.get('view')
    value = request.GET.get('value')
    data_arcnames = []
    if view:
        primary_tag = view + ":" + value
        if view == 'cruise':
            secondary_tag = u"data_type:"
            allowed_secondary_values = TAGS_DATA_TYPE
        if view == 'data_type':
            secondary_tag = u"cruise:"
            allowed_secondary_values = TAGS_CRUISE

        primary_path = "/dimes_data_{0}".format(value)
        sane_name = primary_path[1:] + ".zip"

        filters = [
                Query.tags_any('eq', primary_tag)
                ]
        if not request.user.is_authenticated():
            filters.append(Query.tags_any("eq", "privacy:public"))

        data = [t for t in tsc.query_data(*filters, preload=True)]
        data_tags = {secondary_tag + dt for dt in allowed_secondary_values}
        for datum in data:
            datum_types = data_tags.intersection(datum.tags)
            if datum_types:
                for datum_dt in datum_types:
                    dt = datum_dt.split(secondary_tag)[1]
                    _add_dirs_arclist(data_arcnames, datum, value, dt)
            else:
                _add_dirs_arclist(data_arcnames, datum, value, TAG_OTHER_DATA)
    else:
        zdir = _path_from_json(request.GET.get('path'))
        basedir = _path_dimes(zdir)
        sane_name = 'dimes{0}.zip'.format(
            zdir.replace('/', '-').replace(' ', '_'))

        filters = []
        if not request.user.is_authenticated():
            filters.append(Query.tags_any("eq", "privacy:public"))

        data = list(tsc.query_data(Query.tags_any('eq', basedir), *filters))
        if zdir == '/':
            subdirs = basedir + '%'
        else:
            subdirs = basedir + '/%'
        data.extend(list(tsc.query_data(Query.tags_any('like', subdirs), *filters)))

        for datum in data:
            fname = datum.fname
            try:
                arcname = os.path.join(tag_value(datum, TAG_PATH_PREFIX), fname)
            except KeyError:
                continue
            data_arcnames.append((datum.id, arcname))

    data = dict(data_arcnames=data_arcnames, fname=sane_name,
                ofs_endpoint=tsc._api_endpoint('ofs'))
    return _proxy(requests.post(tsc._api_endpoint('zip'),
                                data=json.dumps(data), headers=tsc.headers_json))


@csrf_exempt
def dirflist(request):
    fslist=[]
    view = request.GET.get("view", None)
    value = request.GET.get("value", None)
    page = request.GET.get("page", None)
    tsq = None
    pages = 0
    if request.method == "POST":
        if view:
            primary_tag = view + ":" + value
            path = json.loads(request.body)
            if view == "cruise" and value in TAGS_CRUISE:
                secondary_tag = "data_type:%"
            elif view == "data_type" and value in TAGS_DATA_TYPE:
                secondary_tag = "cruise:%"
            try:
                path_tag = path[0]
            except IndexError:
                files = []
            else:
                filters = [
                        Query.tags_any('eq', primary_tag),
                        ]
                if path_tag == TAG_OTHER_DATA:
                    filters.append(
                        ['tags', 'not_any', ['tag', 'like', secondary_tag]]
                    )
                else:
                    data_type_tag = secondary_tag[:-1] + path_tag
                    filters.append(
                        Query.tags_any('eq', data_type_tag),
                    )
                tsq = tsc.query_data(*filters, preload=True)

        else:
            tag = _path_dimes(_path_from_json(request.body))
            if request.user.is_authenticated():
                tsq = tsc.query_data(Query.tags_any("eq", tag))
            else:
                tsq = tsc.query_data(Query.tags_any("eq", tag),
                                     Query.tags_any("eq", "privacy:public"))
        if tsq is not None:
            start = len(tsq.objects)
            if start > 0:
                page = int(page) + 1
                tsq.get_page(page=page)
            stop = len(tsq.objects)
            files = tsq[start:stop]
            pages = tsq.num_pages

        fslist = []
        for fff in files:
            try:
                privacy = tag_value(fff, 'privacy')
            except KeyError:
                privacy = 'dimes'
            fslist.append({
                "fname": fff.fname,
                "url": ofs_to_dimes_uri(fff.uri),
                "tags": fff.tags,
                "privacy": privacy,
            })
        #cannot rely on the tsq.page value
        response_dict = {'page':page, 'pages':pages, 'files':fslist}
    return HttpResponse(json.dumps(response_dict), content_type="application/json")


@_check_auth
def rename(request):
    """POST rename

    Arguments: 
        type - the type of filesystem object to modify, either file or dir

        If the type is file:
            fname - specifies the new file name

        If the type is dir:
            path_from - path to rename from 
            path to - path to rename to

    """
    if request.method == "POST":
        if request.POST['type'] == 'file':
            uri = _download_url_to_ofs_url(request.POST['uri'])
            fname = request.POST['fname']
            data = tsc.query_data(['uri', 'eq', uri], limit=1, single=True)
            tsc.edit(data.id, fname=fname)
            return HttpResponse(json.dumps(dict(status='ok')),
                                content_type="application/json")
        elif request.POST['type'] == 'dir':
            path_from = _path_from_json(request.POST['path_from'])
            path_to = _path_from_json(request.POST['path_to'])

            dir_from = _path_dimes(path_from)
            dir_to = _path_dimes(path_to)

            tags = tsc.query_tags(["tag", "eq", dir_from])
            for tag in tags:
                tsc.edit_tag(tag.id, dir_to)
            tags = tsc.query_tags(["tag", "like", dir_from + "/%"])
            for tag in tags:
                tsc.edit_tag(tag.id, tag.tag.replace(dir_from, dir_to, 1))
            return HttpResponse(json.dumps(dict(status='ok')),
                                content_type="application/json")
    return HttpResponse(json.dumps(dict(status='invalid')),
                        status_code=400, content_type="application/json")


def allowed_tags(request):
    tags = []

    for cruise in TAGS_CRUISE:
        tags.append('cruise:{0}'.format(cruise))
    for dtype in TAGS_DATA_TYPE:
        tags.append('data_type:{0}'.format(dtype))
    return HttpResponse(json.dumps(dict(tags=tags)),
                        content_type="application/json")


def _edit_tags(data, tag, action):
    tags = data.tags
    if action == 'delete':
        if tag in tags:
            tags.remove(tag)
    elif action == 'add':
        if tag not in tags:
            tags.append(tag)
    tsc.edit(data.id, tags=tags)
    

@_check_auth
def edit_tag(request):
    """POST edit_tag

    Arguments:
        action - add or delete
        tag - the tag

        type - the type of filesystem object to edit, either file or dir

        If type is file:
            uri - the URI of the data to modify

        If type is dir:
            path - the path to apply the action to


    """
    action = request.POST['action']
    tag = request.POST['tag']
    if request.POST['type'] == 'file':
        uri = _download_url_to_ofs_url(request.POST['uri'])
        data = tsc.query_data(["uri", "eq", uri], limit=1, single=True)
        _edit_tags(data, tag, action)
        return HttpResponse(json.dumps(dict(status='ok')),
                    content_type="application/json")
    elif request.POST['type'] == 'dir':
        path = _path_dimes(_path_from_json(request.POST['path']))

        data = tsc.query_data(Query.tags_any("eq", path))
        for datum in data:
            _edit_tags(datum, tag, action)
        data = tsc.query_data(Query.tags_any("like", path + "/%"))
        for datum in data:
            _edit_tags(datum, tag, action)

        return HttpResponse(json.dumps(dict(status='ok')),
                    content_type="application/json")
    return HttpResponse(json.dumps(dict(status='invalid')),
                        status_code=400, content_type="application/json")


def _delete_dir(ddir):
    ddir_recurse = '{0}/%'.format(ddir)
    data = tsc.query_data(Query.tags_any('eq', ddir), preload=True)
    for datum in data:
        tsc.delete(datum.id)
    data = tsc.query_data(Query.tags_any('like', ddir_recurse), preload=True)
    for datum in data:
        tsc.delete(datum.id)
    tags = tsc.query_tags(['tag', 'eq', ddir], preload=True)
    for tag in tags:
        tsc.delete_tag(tag.id)
    tags = tsc.query_tags(['tag', 'like', ddir_recurse], preload=True)
    for tag in tags:
        tsc.delete_tag(tag.id)


@_check_auth
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
            ddir = _path_dimes(path)
            _delete_dir(ddir)
            return HttpResponse(json.dumps(dict(status='ok')),
                        content_type="application/json")
    return HttpResponse(json.dumps(dict(status='failed')),
                        content_type="application/json")


@_check_auth
def upload(request):
    path = _path_from_json(request.POST['path'])
    blob = request.FILES['file']
    path = os.path.normpath(path)
    if path == '.':
        path = ''
    tags = [TAG_WEBSITE, 'privacy:dimes', _path_dimes(path)]
    resp = tsc.create(blob, unicode(blob), tags)
    if request.is_ajax():
        return HttpResponse(json.dumps(dict(fname=resp.fname, url=resp.uri,
            tags=tags)),
                            content_type="application/json")
    else:
        return redirect(request.META['HTTP_REFERER'])


@_check_auth
def unzip(request):
    if request.method == "POST":
        uri = _download_url_to_ofs_url(request.POST['uri'])
        data = tsc.query_data(["uri", "eq", uri], limit=1, single=True)

        # make the new path tag, current path + zipname
        old_dir = [tag for tag in data.tags if
                   tag.startswith(TAG_PATH_PREFIX + ':')]
        # Copy the old tags minus the path tag
        tags = [tag for tag in data.tags if not
                tag.startswith(TAG_PATH_PREFIX + ':')]
        if not old_dir:
            raise Http404()
        old_dir = old_dir[0].split(':')[1]
        zipdirname = os.path.splitext(data.fname)[0].replace('/', '-')
        new_dir = os.path.join(old_dir, zipdirname)

        # put the new tag onto the old tags
        dir_tag = _path_dimes(new_dir)
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


@_check_auth
def toggle_privacy(request):
    if request.method == "POST":
        uri = _download_url_to_ofs_url(request.POST['uri'])
        data = tsc.query_data(['uri', 'eq', uri], limit=1, single=True)
        try:
            privacy = tag_value(data, 'privacy')
        except KeyError:
            tsc.edit(data.id, tags=data.tags + ['privacy:public'])
            state = 'public'
        else:
            if privacy == 'public':
                oldtag = 'privacy:public'
                newtag = 'privacy:dimes'
                state = 'dimes'
            else:
                oldtag = 'privacy:dimes'
                newtag = 'privacy:public'
                state = 'public'
            tsc.swap_tags(oldtag, newtag, ['id', 'eq', data.id])
        return HttpResponse(json.dumps(dict(privacy=state)),
                            content_type="application/json")


def index(request):
    return render(request, "dimesfs/index.html")
