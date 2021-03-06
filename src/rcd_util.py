###
### Copyright (C) 2002-2003 Ximian, Inc.
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License, version 2,
### as published by the Free Software Foundation.
###
### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.
###
### You should have received a copy of the GNU General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
###

import sys, os, errno, time, signal, string, types, md5, socket, gobject, gtk
import ximian_xmlrpclib
import red_pixbuf, red_serverproxy
import red_settings
import red_connection
from red_gettext import _

server = None
server_proxy = None
server_local = 0
server_permissions = {}
current_user = None
mirrors = None

def md5ify_password(pw):
    return md5.new(pw).hexdigest()

def register_server(srv, local):
    global server, server_proxy, server_local
    server = srv
    server_proxy = red_serverproxy.ServerProxy(server)
    server_local = local
    reset_server_permissions()
    reset_current_user()
    reset_mirrors()

def get_server():
    return server

def get_server_proxy():
    return server_proxy

def get_server_local():
    return server_local

def server_has_patch_support(server):
    return server.rcd.system.query_module("rcd.you", 1, 0)

def reset_server_permissions():
    global server_permissions
    server_permissions = {}

def check_server_permission(perm):
    if not perm:
        return 0
    perm = perm.lower()
    if not server_permissions.has_key(perm):
        server = get_server()
        try:
            server_permissions[perm] = server.rcd.users.has_privilege(perm)
        except:
            pass # FIXME: we can do better than this...

    return server_permissions.get(perm, 0)
    
def reset_current_user():
    global current_user
    current_user = None

def get_current_user():
    global current_user

    if current_user:
        return current_user

    server = get_server()
    current_user = server.rcd.users.get_current_user()
    return current_user

def get_mirrors():
    global mirrors

    def sort_cb(a, b):
        aname = string.lower(a["name"])
        bname = string.lower(b["name"])

        # "All Animals Are Equal / But Some Are More Equal Than Others."
        if aname[:6] == "ximian":
            aname = "a" * 10
        if bname[:6] == "ximian":
            bname = "a" * 10
                
        return cmp(aname, bname)

    if mirrors is None:
        server = get_server()
        mirrors = server.rcd.mirror.get_all()
        mirrors.sort(sort_cb)
    return mirrors

def reset_mirrors():
    global mirrors
    mirrors = None

###############################################################################

have_channels = 0
cached_channels = {}
cached_channel_icons = {}

def reset_channels():
    global have_channels, cached_channels, cached_channel_icons
    have_channels = 0
    cached_channels = {}
    cached_channel_icons = {}

def fetch_channels():
    global have_channels, cached_channels
    
    if have_channels:
        return

    channel_list = server.rcd.packsys.get_channels()
    for c in channel_list:
        if not c["hidden"]:
            cached_channels[c["id"]] = c

    have_channels = 1


def get_all_channels():
    fetch_channels()
    return cached_channels.values()


def get_channel(id):
    try:
        assert type(id) is types.StringType
    except AssertionError:
        print id
        raise

    fetch_channels()
    if cached_channels.has_key(id):
        return cached_channels[id]
    return None


def get_channel_name(id):
    c = get_channel(id)
    if c:
        return c["name"]
    else:
        return "????"

def get_channel_alias(id):
    c = get_channel(id)
    if c:
        return c["alias"]
    else:
        return "????"

def get_channel_icon(id, width=0, height=0):

    try:
        assert type(id) is types.StringType
    except AssertionError:
        print id
        raise

    if not id:
        return None

    if width > 0 and height > 0:
        key = "%s %d %d" % (id, width, height)
    else:
        key = id
    
    if cached_channel_icons.has_key(key):
        return cached_channel_icons[key]

    pixbuf = None
    
    if width > 0 and height > 0:
        
        original = get_channel_icon(id)

        if not original:
            return None
        
        pixbuf = original.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)

    else:

        #assert server
        try:
            icon_data = server.rcd.packsys.get_channel_icon(id)
        except ximian_xmlrpclib.Fault, f:
            if f.faultCode == fault.no_icon or f.faultCode == fault.invalid_channel:
                icon_data = None
            else:
                raise

        if icon_data:
            loader = gtk.gdk.gdk_pixbuf_loader_new()

            try:
                loader.write(icon_data.data, len(icon_data.data))
                loader.close()
            except gobject.GError, e:
                pass
            else:
                pixbuf = loader.get_pixbuf()

    if pixbuf is None:
        pixbuf = red_pixbuf.get_pixbuf("default-channel", width, height)

    cached_channel_icons[key] = pixbuf
    return pixbuf


def get_channel_image(id, width=0, height=0):
    pixbuf = get_channel_icon(id, width, height)
    if not pixbuf:
        return None
    img = gtk.Image()
    img.set_from_pixbuf(pixbuf)
    return img

def get_package_channel_name(pkg):
    if pkg.has_key("channel") and pkg["channel"]:
        return get_channel_name(pkg["channel"])
    elif pkg.has_key("channel_guess"):
        return get_channel_name(pkg["channel_guess"])
    else:
        return "None"

def get_package_channel_icon(pkg, width=0, height=0):
    if pkg.has_key("channel") and pkg["channel"]:
        return get_channel_icon(pkg["channel"], width, height)
    elif pkg.has_key("channel_guess"):
        return get_channel_icon(pkg["channel_guess"], width, height)
    else:
        # Don't return None here, because we want an empty image to be
        # scaled to the correct height.
        return red_pixbuf.get_pixbuf("empty", width=width, height=height)

def get_package_EVR(pkg):
    epoch_str = ""
    rel_str = ""
    if pkg["has_epoch"]:
        epoch_str = "%d:" % pkg["epoch"]
    if pkg["release"]:
        rel_str = "-%s" % pkg["release"]
    return "%s%s%s" % (epoch_str, pkg["version"], rel_str)

PACKAGE_TYPE_PACKAGE = 1
PACKAGE_TYPE_PATCH   = 2
PACKAGE_TYPE_BUNDLE  = 3

def get_package_type(pkg):
    if pkg.has_key("is_patch") and pkg["is_patch"]:
        return PACKAGE_TYPE_PATCH
    if pkg.has_key("is_bundle") and pkg["is_bundle"]:
        return PACKAGE_TYPE_BUNDLE

    return PACKAGE_TYPE_PACKAGE

def get_package_info(pkg):
    if not pkg.has_key("__info"):
        pkg_type = get_package_type(pkg)
        if pkg_type == PACKAGE_TYPE_PACKAGE:
            pkg["__info"] = server.rcd.packsys.package_info(pkg)
        elif pkg_type == PACKAGE_TYPE_PATCH:
            pkg["__info"] = server.rcd.you.patch_info(pkg)
##      elif pkg_type == PACKAGE_TYPE_BUNDLE:
            
        else:
            pkg["__info"] = {}

    return pkg["__info"]

def get_package_history(pkg):
    return server.rcd.log.query_log([["name", "=", pkg["name"]]])

def is_system_package(pkg):
    if not pkg.get("channel", "") or pkg.has_key("channel_guess"):
        return 1
    return 0

def get_package_key(pkg):
    key = pkg.get("__key")
    if not key:
        if is_system_package(pkg):
            channel = pkg.get("channel_guess", "")
        else:
            channel = pkg.get("channel")

        key = pkg["__key"] = "%s/%s/%s" % (pkg["name"],
                                           get_package_EVR(pkg),
                                           channel)
    return key

def get_dep_EVR(dep):
    evr = get_package_EVR(dep)
    return dep["relation"] + " " + evr

###############################################################################
have_services = 0
cached_services = {}

def reset_services():
    global have_services, cached_services
    have_services = 0
    cached_services = {}

def fetch_services():
    global have_services, cached_services

    if have_services:
        return

    service_list = server.rcd.service.list()
    for s in service_list:
        if not s["is_invisible"]:
            cached_services[s["id"]] = s

    have_services = 1

def get_all_services():
    fetch_services()
    return cached_services.values()

def get_service_by_id(id):
    for s in get_all_services():
        if s["id"] == id:
            return s
    return None

###############################################################################

def byte_size_to_string(sz):
    if sz <= 0:
        return ""
    elif sz < 1024:
        return "%d bytes" % sz
    elif sz < 1048576:
        return "%d kB" % (sz/1024)
    else:
        return "%.1f MB" % (sz/(1048576.0))

###############################################################################

def linebreak(in_str, width):

    str = string.strip(in_str)

    if not str:
        return []

    if len(str) <= width:
        return [str]

    if width < len(str) and str[width] == " ":
        n = width
    else:
        n = string.rfind(str[0:width], " ")
        if n  == -1:
            n = string.find(str, " ")

    lines = []

    if n == -1:
        lines.append(str)
    else:
        lines.append(str[0:n])
        lines = lines + linebreak(str[n+1:], width)

    return lines

###############################################################################

def dialog_from_fault(f, error_text=None, additional_text=None,
                      parent=None, post_dialog_thunk=None):
    if not f:
        return

    if error_text:
        text = error_text + ": " + f.faultString
    else:
        text = f.faultString

    if additional_text:
        text = text + "\n\n" + additional_text
    
    text = text + "\n\n" + "(fault %d)" % f.faultCode

    dialog = gtk.MessageDialog(parent, 0, gtk.MESSAGE_WARNING,
                               gtk.BUTTONS_OK,
                               text)
    dialog.set_title("") # Gnome HIG says no titles on these sorts of dialogs

    def idle_cb(d, thunk):
        gtk.threads_enter()
        d.show()
        d.run()
        d.destroy()
        if thunk:
            thunk()
        gtk.threads_leave()

    # Always run the dialog in the main thread.
    gtk.idle_add(idle_cb, dialog, post_dialog_thunk)

###############################################################################

def server_proxy_dialog(worker,
                        callback=None,
                        message=None,
                        user_data=None,
                        parent=None,
                        can_cancel=1):

    if not message:
        message = _("Please wait while getting data.")

    if can_cancel:
        buttons = gtk.BUTTONS_CANCEL
    else:
        buttons = gtk.BUTTONS_NONE

    dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO,
                               buttons, message)

    if parent:
        dialog.set_transient_for(parent)

    def update_progressbar_cb(p):
        p.pulse()
        return 1

    progressbar = gtk.ProgressBar()
    tid = gtk.timeout_add(100, update_progressbar_cb, progressbar)
    progressbar.show()
    dialog.vbox.add(progressbar)

    def destroy_cb(x, y):
        gtk.timeout_remove(y)
        return 1

    dialog.connect("destroy", destroy_cb, tid)

    def cancel_cb(dialog, response, worker):
        worker.cancel()
        dialog.destroy()

    dialog.connect("response", cancel_cb, worker)
    dialog.show()

    worker.connect("ready", lambda x,y:y.destroy(), dialog)
    if callback:
        if user_data:
            worker.connect("ready", callback, user_data)
        else:
            worker.connect("ready", callback)

###############################################################################

def refresh(parent):
    server = get_server_proxy()

    def got_channels_cb(worker, parent):
        if worker.is_cancelled():
            return
        try:
            stuff_to_poll = worker.get_result()
        except ximian_xmlrpclib.Fault, f:
            dialog_from_fault(f,
                              additional_text=_("Please ensure that your "
                              "network settings are correct."),
                              parent=parent)
            return
        
        import red_pendingview

        pend = red_pendingview.PendingView_Simple(title=_("Refreshing catalog data"),
                                                  parent=parent)
        pend.set_label(_("Downloading catalog information"))
        pend.set_icon("dialog-refreshing")
        pend.show_all()
        pend.set_pending_list(stuff_to_poll)

    try:
        worker = server.rcd.service.refresh()
    except ximian_xmlrpclib.Fault, f:
        dialog_from_fault(f,
                          additional_text=_("Please ensure that your "
                          "network settings are correct."),
                          parent=parent)
        return

    server_proxy_dialog(worker,
                        callback=got_channels_cb,
                        user_data=parent,
                        parent=parent)
    
###############################################################################

###
### Format transaction status messages into readable text
###

def transaction_status(message):
    messages = {"verify"       : _("Verifying"),
                "verify-undef" : _("Unable to verify package signature for"),
                "verify-nosig" : _("There is no package signature for"),
                "prepare"      : _("Preparing Transaction"),
                "install"      : _("Installing"),
                "remove"       : _("Removing"),
                "configure"    : _("Configuring")}
    
    status = string.split(message, ":", 1)

    m = messages[status[0]]
    if len(status) > 1:
        return m + " " + status[1]
    else:
        return m

###############################################################################

### XML-RPC faults that we care about back from the daemon.
###
### KEEP THIS IN SYNC WITH RCD!

class fault:
    type_mismatch          = -501 # matches xmlrpc-c
    invalid_stream_type    = -503 # matches xmlrpc-c
    undefined_method       = -506 # matches xmlrpc-c
    permission_denied      = -600
    package_not_found      = -601
    package_is_newest      = -602
    failed_dependencies    = -603
    invalid_search_type    = -604
    invalid_package_file   = -605
    invalid_channel        = -606
    invalid_transaction_id = -607
    invalid_preference     = -608
    locked                 = -609
    cant_authenticate      = -610
    cant_refresh           = -611
    no_icon                = -612
    cant_activate          = -613
    not_supported          = -614
    license_not_found      = -615
    cant_set_preference    = -616
    invalid_service        = -617
    transaction_failed     = -618

