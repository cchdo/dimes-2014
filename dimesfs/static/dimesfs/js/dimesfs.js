Dropzone.autoDiscover = false;

var write_allowed = true;
var fs_struct;
var current_path = [];
var fs_list_pagenum = 0;
var dug_tree; // store a reference to the dug tree for mkdir
if (window.location.hash == ""){
  window.location.hash = encodeURIComponent(JSON.stringify([])); 
} else {
  parseHash();
}

if (window.location.search != ""){
  write_allowed = false;
}
var fslist_url = "/dimesfs/fslist" + window.location.search;
$.getJSON(fslist_url, function(data){
  fs_struct = data;
  set_table();
});
function parseHash(){
  try{
    current_path = JSON.parse(decodeURIComponent(window.location.hash.slice(1)));
  } catch (e) {
    window.location.hash = encodeURIComponent(JSON.stringify([])); 
  }
}
function localeCompare(a,b){return a.localeCompare(b)}
function createIcon(type) {
    return $('<span class="glyphicon glyphicon-' + type + '"></span>');
}
function createRow(icon, body, secondary, accessory) {
  var tr = $("<tr></tr>");
  tr.append($('<td class="icon"></td>').append(icon));
  var colspan = "";
  if (!secondary) {
    colspan = 'colspan="2"';
  }
  tr.append($('<td class="body"' + colspan + '></td>').append(body));
  if (secondary) {
    tr.append($('<td class="secondary"></td>').append(secondary));
  }
  tr.append($('<td class="accessories"></td>').append(accessory));
  return tr;
}

function goto_page(page_num){
  fs_list_pagenum = page_num;
  set_table();
}
function createPaginationButton(text, disabled, page_to){
  var disabled_text = '';
  if (disabled){
    disabled_text = 'disabled="disabled"';
  }
  var button = $('<button onclick="goto_page('+page_to+')" type="button" class="btn btn-md btn-default" '+ disabled_text +'>'+ text +'</button>');
  return button;
}

function createPaginationRow(current_page, total_pages) {
  current_page -= 1
  var first_page = false;
  if (current_page == 0){
    first_page = true;
  }
  var last_page = false;
  if (current_page == (total_pages - 1)){
    last_page = true;
  }
  var tr = $("<tr></tr>");
  var td = $('<td style="text-align:center;" colspan="4"></td>');
  tr.append(td);
  var form = $('<form class="form-inline" role="form"></form>');
  var back_group = $('<div class="btn-group"></div>');
  var for_group = $('<div class="btn-group"></div>');
  back_group.append(createPaginationButton("First", first_page, 0));
  back_group.append(createPaginationButton("Previous", first_page, current_page -1));
  for_group.append(createPaginationButton("Next", last_page, current_page + 1));
  for_group.append(createPaginationButton("Last", last_page, total_pages -1));

  var page_select = $('<select onchange="goto_page(this.value)" class="form-control"></select>');
  for (var i=0; i<total_pages; i++){
    var selected = "";
    if (i == current_page){
      selected = "selected";
    }
    page_select.append($('<option '+selected+' value="'+i+'">Page '+ (i +1) +'</option>'));
  }
  form.append(back_group);
  form.append(page_select);
  form.append(for_group);
  td.append(form);
  return tr;
}
function input_hidden(name, value) {
  return '<input type="hidden" name="' + name + "\" value='" + value + "'>";
}
function createAccessoryButton(title, glyph) {
  var button = $('<button type="button" class="btn btn-default btn-xs" title="' + title + '"></button>');
  button.append(createIcon(glyph));
  return button;
}
function edit_tag(type, tag, oid, action) {
  var data = {
    tag: tag,
    type: type,
    action: action,
    csrfmiddlewaretoken: $.cookie("csrftoken")
  };
  if (type == "file") {
    data.uri = oid;
  } else if (type == "dir") {
    data.path = oid;
  }
  $.ajax({
    type: "POST",
    url: "/dimesfs/edit_tag",
    data: data,
    success: function(data){},
    dataType: 'json'
  });
}
function addTagdrop(ul, type, oid) {
  ul.sortable({
    connectWith: ".tagdrop",
    placeholder: "ui-state-highlight",
    receive: function (event, ui) {
      var contains = ":contains('" + $(ui.item).html() + "')";
      var contained = $(contains, event.target);
      if (contained.length > 1) {
        contained.get(0).remove();
        return;
      }
      var tag = $(ui.item).html();
      edit_tag(type, tag, oid, 'add');
    },
    remove: function (event, ui) {
      var tag = $(ui.item).html();
      edit_tag(type, tag, oid, 'delete');
    }
  });
}
function createRowFile(file) {
  var accessories = $('<span class="pull-right"></span>');
  var secondary = $('<ul class="tagdrop">');
  if (dimesfs.is_authenticated && write_allowed) {
    if (file.fname.slice(-4) == ".zip") {
      var unzip_button = createAccessoryButton('Unzip', 'gift');
      unzip_button.click(function() { dimesfs_unzip(this, file); });
      accessories.append(unzip_button);
    }
    var privacy_button = createAccessoryButton("", "");
    privacy_button.click(function () {dimesfs_toggle_privacy(this, file);});
    accessories.append(privacy_button);

    var rename_button = createAccessoryButton('Rename', 'pencil');
    rename_button.click(function(event) { dimesfs_rename_file(this, file); return false;});
    accessories.append(rename_button);

    var delete_button = createAccessoryButton('Delete', 'remove');
    delete_button.click(function() { dimesfs_del_file(this, file); });
    accessories.append(delete_button);

    addTagdrop(secondary, "file", file.url);
    var disallowed = ['path', 'website', 'privacy'];
    for (var i = 0; i < file.tags.length; i++) {
      var tag = file.tags[i];
      if (tag.indexOf(':') && disallowed.indexOf(tag.split(':')[0]) >= 0) {
        continue;
      }
      secondary.append($('<li class="ui-state-default">' + tag + '</li>'));
    }
  } else {
    secondary = '';
  }
  var body = $('<a href="' + file.url + '">' + file.fname + '</a>');
  var tr = createRow(createIcon('file'), body, secondary, accessories);
  if (dimesfs.is_authenticated && write_allowed) {
    dimesfs_set_privacy_button(privacy_button, file.privacy == 'public')
  }
  return tr;
}
function getRowBodyItem(row) {
  var body = row.find('.body');
  var item = body;
  if (item.find('a').length) {
    item = item.find('a');
  }
  return item;
}
function getRowBodyItemForButton(button) {
  return getRowBodyItem($(button).parents('tr'));
}
function setRowBodyFromButton(button, html) {
  getRowBodyItemForButton(button).html(html);
}
function createRowDir(key) {
  var accessories = $('<span class="pull-right"></span>');
  var secondary = $('<ul class="tagdrop">');

  if (dimesfs.is_authenticated && write_allowed) {
    var rename_button = createAccessoryButton('Rename', 'pencil');
    rename_button.click(function(event) { dimesfs_rename(this, key); return false;});
    accessories.append(rename_button);

    var delete_button = createAccessoryButton('Delete', 'remove');
    delete_button.click(function() { dimesfs_del(this, key); return false; });
    accessories.append(delete_button);

    var path = current_path.slice(0);
    path.push(key);
    addTagdrop(secondary, "dir", JSON.stringify(path));
  } else {
    secondary = '';
  }

  var tr = createRow(createIcon('folder-close'), key, secondary, accessories)
    .click(function () { dimesfs_cd(getRowBodyItem($(this)).html());});
  return tr;
}
function createRowTagBank() {
  var tag_bank = $('<div class="tag-bank"></div>');
  var tag_bank_list = $('<ul class="tagdrop">').appendTo(tag_bank);
  $.get('/dimesfs/allowed_tags', function (data) {
    var tag_bank_tags = data.tags;
    $.each(tag_bank_tags, function (i, x) {
      tag_bank_list.append($('<li class="ui-state-default">' + x + '</li>'));
    })
  }, 'json');
  tag_bank_list.disableSelection().sortable({
    connectWith: ".tagdrop",
    placeholder: "ui-state-highlight",
    receive: function (event, ui) {
      var contains = ":contains('" + $(ui.item).html() + "')";
      var contained = $(contains, event.target);
      if (contained.length > 1) {
        contained.get(0).remove();
        return;
      }
    },
    remove: function (event, ui) {
      ui.item.clone().prependTo(tag_bank_list);
    }
  });
  var tr = createRow(createIcon('tags'), tag_bank);
  return tr;
}
function set_table(){
  var new_tbody = $('<tbody id="fs_table"></tbody>');

  if (!dimesfs.is_authenticated) {
    // Login list item
    var login = $('<div><a href="/login?next=' + window.location.href + '">Login</a> to see non-public data.</div>');
    var tr = createRow(createIcon('lock'), login);
    new_tbody.append(tr);
  }
  if (dimesfs.is_authenticated && write_allowed) {

    // Change path list item
    var new_dir_group = $('<div class="input-group"></div>');
    var newdir_input = $('<input type="text" class="form-control input-sm" placeholder="new path">');
    var input_button_span = $('<span class="input-group-btn"></span>');
    var create_button = $('<button class="btn btn-default btn-sm" type="button">Create Path</button>');
    create_button.click(function() {dimesfs_mkdir(newdir_input.val());});
    // "submit" on 'enter' keyup
    newdir_input.keyup(function(e) {if (e.keyCode == 13) {create_button.click()}});
    input_button_span.append(create_button);
    new_dir_group.append(newdir_input);
    new_dir_group.append(input_button_span);
    var tr = createRow(createIcon('plus'), new_dir_group);
    new_tbody.append(tr);

    // Upload files list item
    var new_upload_form = $(
        '<form class="dropzone" action="/dimesfs/upload" method="POST" enctype="multipart/form-data">'+
        input_hidden("csrfmiddlewaretoken", $.cookie("csrftoken")) + 
        input_hidden("path", JSON.stringify(current_path)) + 
        '<div class="fallback input-group">' +
        '<input type="file" name="file" class="form-control input-sm" multiple>' +
        '<span class="input-group-btn">' +
        '<input class="btn btn-default btn-sm" type="submit" value="Upload">' +
        '</span>' +
        '</div>' +
      '</form>');
    new_upload_form.dropzone({
      //forceFallback: true
      init: function(){
        this.on("success", function(_, resp) {
          files.push(resp);
          var tr = createRowFile(resp);
          new_tbody.append(tr);
        });
      }
    });
    var tr = createRow(createIcon('upload'), new_upload_form);
    new_tbody.append(tr);
  }

  // Download path list item
  if (window.location.search != ""){
    var download_zip_url = "/dimesfs/download_zip" + window.location.search;
    var download_button_text = "Download all files as zip"
  } else {
    var download_zip_url = "/dimesfs/download_zip?path=" + JSON.stringify(current_path);
    var download_button_text = "Download all path files as zip"
  }
  var download_form = $(
      "<a href='" + download_zip_url + "' class=\"btn btn-default input-sm\">" +
      download_button_text +'</a>');
  var tr = createRow(createIcon('download'), download_form);
  new_tbody.append(tr);
  if (current_path.length > 0){
    var tr = createRow(createIcon('folder-open'), '..')
      .click(function () {dimesfs_cd("..");});
    new_tbody.append(tr);
  }

  $("#fs_table").replaceWith(new_tbody);

  // Add list items for files and directories
  var loader = $('<tr><td></td><td>Loading...</td></tr>')
    .hide().appendTo(new_tbody).fadeIn();
  var files = [];
  parseHash();
  var query_params = window.location.search;
  if (query_params.length){
    query_params += "&page=" + fs_list_pagenum;
  } else{
    query_params += "?page=" + fs_list_pagenum;
  }
  $.ajax({
    type: "POST",
    url: "/dimesfs/dirflist" + query_params,
    data: JSON.stringify(current_path),
    success: function(data){
      files = data.files;

      loader.fadeOut().remove();

      dug_tree = fs_struct;
      for (var i=0; i< current_path.length; i++){
        var cd = current_path[i];
        if (dug_tree.hasOwnProperty(cd)){
          dug_tree = dug_tree[cd];
        } else {
          window.location.hash = encodeURIComponent(JSON.stringify([])); 
        }
      }
      
      var docfrag = $(document.createDocumentFragment());

      var pager = createPaginationRow(data.page, data.pages);
      docfrag.append(pager.clone());

      var keys = Object.keys(dug_tree);
      keys = keys.sort(localeCompare);
      for (var i=0; i < keys.length; i++){
        var key = keys[i];
        var tr = createRowDir(key);
        docfrag.append(tr);
      }

      files = files.sort(function(a,b){return localeCompare(a.fname, b.fname)});
      for (var i=0; i < files.length; i++){
        var file = files[i];
        var tr = createRowFile(files[i]);
        docfrag.append(tr);
      }

      docfrag.append(pager);

      if (dimesfs.is_authenticated && write_allowed) {
        docfrag.append(createRowTagBank());
      }
      new_tbody.append(docfrag)
    },
    dataType: 'json',
  });
}
function dimesfs_add_dir(tbody, dname) {
  if ($(tbody.children('tr:contains("' + dname + '")'))) {
    return;
  }
  var tr = createRowDir(dname);
  tbody.append(tr);
}
function dimesfs_rename(target, dname) {
  var path_from = current_path.slice(0);
  path_from.push(dname);
  var path_to = current_path.slice(0);
  var new_name = prompt('New path name', dname);
  path_to.push(new_name);
  $.ajax({
    type: "POST",
    url: "/dimesfs/rename",
    data: {
      type: 'dir',
      path_from: JSON.stringify(path_from),
      path_to: JSON.stringify(path_to),
      csrfmiddlewaretoken: $.cookie('csrftoken')
    },
    success: function(data) {
      setRowBodyFromButton(target, new_name);
      var fs = fs_struct;
      for (var i = 0; i < current_path.length; i++) {
        fs = fs[current_path[i]];
      }
      fs[new_name] = fs[dname];
      delete fs[dname];
    },
    dataType: 'json'
  });
}
function dimesfs_rename_file(target, file) {
  var fname = prompt('New file name', file.fname);
  $.ajax({
    type: "POST",
    url: "/dimesfs/rename",
    data: {
      type: 'file',
      uri: file.url,
      fname: fname,
      csrfmiddlewaretoken: $.cookie('csrftoken')
    },
    success: function(data) {
      setRowBodyFromButton(target, fname);
    },
    dataType: 'json'
  });
}
function dimesfs_unzip(target, file) {
  $.ajax({
    type: "POST",
    url: "/dimesfs/unzip",
    data: {
      uri: file.url,
      csrfmiddlewaretoken: $.cookie('csrftoken')
    },
    success: function(data) {
      var dname = data['dirname'];
      dimesfs_add_dir($(target).parents('tbody'), dname);
    },
    dataType: 'json'
  });
}
function dimesfs_del(target, dirname) {
  var answer = confirm("Delete " + dirname + "?");
  var path = current_path.slice(0);
  path.push(dirname);
  if (answer) {
    $.ajax({
      type: "POST",
      url: "/dimesfs/delete",
      data: {
        type: 'dir',
        path: JSON.stringify(path),
        csrfmiddlewaretoken: $.cookie('csrftoken')
      },
      success: function(data){
        if (data.status == "ok") {
          $(target).parents('tr').hide('fast').remove();
        }
      },
      dataType: 'json'
    });
  }
}
function dimesfs_del_file(target, file) {
  var answer = confirm("Delete " + file.fname + "?");
  if (answer) {
    $.ajax({
      type: "POST",
      url: "/dimesfs/delete",
      data: {
        type: 'file',
        uri: file.url,
        csrfmiddlewaretoken: $.cookie('csrftoken')
      },
      success: function(data){
        if (data.status == "ok") {
          $(target).parents('tr').hide('fast').remove();
        }
      },
      dataType: 'json'
    });
  }
}
function dimesfs_set_privacy_button(btn, public) {
  var title = "Make public";
  var remove_class = "eye-close";
  var add_class = "eye-open";
  if (public) {
    title = "Make private";
    remove_class = "eye-open";
    add_class = "eye-close";
  }
  btn.attr('title', title);
  var row = btn.parents('tr');
  if (public) {
    row.removeClass('private');
  } else {
    row.addClass('private');
  }
  $('span', btn)
    .removeClass('glyphicon-' + remove_class)
    .addClass('glyphicon-' + add_class);
}
function dimesfs_toggle_privacy(target, file) {
  var btn = $(target);
  btn.prop('disabled', true);

  $.ajax({
    type: "POST",
    url: "/dimesfs/toggle_privacy",
    data: {
      type: 'file',
      uri: file.url,
      csrfmiddlewaretoken: $.cookie('csrftoken')
    },
    success: function(data) {
      dimesfs_set_privacy_button(btn, data.privacy == 'public');
      btn.prop('disabled', false);
    },
    dataType: 'json'
  });

}
function dimesfs_mkdir(dir_name){
  if (dir_name.indexOf("..") == 0) { // don't start with ".."
    return;
  }
  if (dir_name.indexOf("/") > -1){ // no "/" in the name
    return;
  }
  dug_tree[dir_name] = {}; //yeah, it's that simple
  set_table();
}
function dimesfs_cd(path){
  fs_list_pagenum = 0;
  if (path == ".."){
    current_path.pop()
  } else {
    current_path.push(path)
  }
  window.location.hash = encodeURIComponent(JSON.stringify(current_path));
}
window.onhashchange = set_table;
