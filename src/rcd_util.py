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

import sys, os, errno, time, signal, string, md5, socket, gtk
import ximian_xmlrpclib
import red_pixbuf, red_serverproxy
import red_settings
from red_gettext import _

server = None
server_proxy = None
server_permissions = {}
current_user = None

def md5ify_password(pw):
    return md5.new(pw).hexdigest()


def check_rcd_version(major, minor, micro):
    req_major = 1
    req_minor = 2
    req_micro = 0

    # Guard for NoneType
    major = major or 0
    minor = minor or 0
    micro = micro or 0

    req_version = (req_major * 100) + (req_minor * 10) + req_micro
    version = (major * 100) + (minor * 10) + micro

    if version < req_version:
        return _("Detected Red Carpet Daemon version %d.%d.%d.n"
                 "Version %d.%d.%d (or newer) is required.") % \
                 (major, minor, micro, req_major, req_minor, req_micro)

    return None

# Tries to connect to server and get a result
# to ping command.
# Returns (server, None) on success or
#         (None, error_msg) on failure.
def connect_real(url, username=None, password=None):
    transport_debug = os.environ.has_key("RC_TRANSPORT_DEBUG")

    err_msg = None
    server = None
    try:
        server = ximian_xmlrpclib.Server(url,
                                         auth_username=username,
                                         auth_password=password,
                                         verbose=transport_debug)
    except:
        err_msg = _("Unable to connect to the daemon")

    if not err_msg:
        try:
            ping = server.rcd.system.ping()
        except socket.error, f:
            err_msg = f[1]
        except ximian_xmlrpclib.ProtocolError, f:
            err_msg = f
        except ximian_xmlrpclib.Fault, f:
            err_msg = f.faultString
        else:
            err_msg = check_rcd_version(ping.get("major_version"),
                                        ping.get("minor_version"),
                                        ping.get("micro_version"))

    if err_msg:
        return (None, err_msg)

    return (server, None)

def connect_to_server(force_dialog=0):
    if not force_dialog:
        # Get stuff from config and try to connect.
        data = red_settings.DaemonData()
        url, username, password, local = data.data_get()
        server, err_msg = connect_real(url, username, password)

        if not err_msg:
            register_server(server)
            return server

    # Ask for information.
    while 1:
        d = red_settings.ConnectionWindow()
        d.run()
        url, username, password, local = d.get_server_info()
        d.destroy()
        # FIXME: This shouldn't be here, it should be fixed in pygtk.
        gtk.threads_leave()

        if not url:
            return None

        server, err_msg = connect_real(url, username, password)
        if not err_msg:
            register_server(server)
            return server

        # Try to start an rcd.
        # FIXME: This will probably require some distribution-specific love
        if local and os.geteuid() == 0 and os.path.exists("/sbin/service"):
            dialog = gtk.MessageDialog(None,
                                       gtk.DIALOG_MODAL,
                                       gtk.MESSAGE_WARNING,
                                       gtk.BUTTONS_YES_NO,
                                       _("Red Carpet requires a Red Carpet "
                                         "Daemon to be running.\n"
                                         "Would you like to start one now?"))
            dialog.set_title("") # Conform to GNOME HIG
            gtk.threads_enter()
            response = dialog.run()
            gtk.threads_leave()
            dialog.destroy()

            if response == gtk.RESPONSE_YES:
                sd = StartDaemon()
                # This will block with a dialog.
                server = sd.run()

                if server is not None:
                    register_server(server)
                    return server
        else:
            dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                       gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                       _("Unable to connect to the "
                                       "daemon:\n '%s'.") % err_msg)
            dialog.set_title("") # Gnome HIG says no titles on these sorts of dialogs
            gtk.threads_enter()
            dialog.run()
            gtk.threads_leave()
            dialog.destroy()

def register_server(srv):
    global server, server_proxy
    server = srv
    server_proxy = red_serverproxy.ServerProxy(server)
    reset_server_permissions()
    reset_current_user()

def get_server():
    global server
    if not isinstance(server, ximian_xmlrpclib.Server):
        server = connect_to_server()

    if not isinstance(server, ximian_xmlrpclib.Server):
        sys.exit(1)

    return server

def get_server_proxy():
    return server_proxy

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

class StartDaemon:
    def __init__(self):
        self.start_time = 0
        self.service_pid = -1;
        self.rcd_pid = -1;
        self.server = None

        # FIXME: Distro-specific love?
        self.cmd = "/sbin/service"
        self.args = (self.cmd, "rcd", "start")

    def run(self):
        self.dialog = gtk.MessageDialog(None, 0,
                                        gtk.MESSAGE_INFO,
                                        gtk.BUTTONS_CANCEL,
                                        _("Starting daemon..."))

        child_pid = os.fork()
        if child_pid == 0: # child
            os.execv(self.cmd, self.args)
            # If we get here, the exec failed.
            return None

        # parent
        self.service_pid = child_pid
        print "service pid is %d" % self.service_pid

        gtk.timeout_add(500, self.wait_for_daemon_cb)

        gtk.threads_enter()
        response = self.dialog.run()
        print "run exited, so a mainloop died somewhere"
        gtk.threads_leave()
        self.dialog.destroy()

        if response == gtk.RESPONSE_CANCEL or \
           response == gtk.RESPONSE_DELETE_EVENT:
            if self.service_pid != -1:
                os.kill(self.service_pid, signal.SIGKILL)
            if self.rcd_pid != -1:
                os.kill(self.rcd_pid, signal.SIGKILL)

        return self.server

    def wait_for_daemon_cb(self):
        if self.service_pid != -1:
            pid, status = os.waitpid(self.service_pid, os.WNOHANG)
            if pid == self.service_pid:
                self.service_pid = -1

                pidfile = open("/var/run/rcd.pid")
                pidstr = pidfile.read()
                print "pidstr: %s" % pidstr
                self.rcd_pid = int(pidstr)
                print "rcd pid: %d" % self.rcd_pid

        if self.rcd_pid != -1:
            # FIXME: allow other paths?
            s = ximian_xmlrpclib.Server("/var/run/rcd/rcd")
            try:
                s.rcd.system.ping()
            except:
                if not self.start_time:
                    self.start_time = time.time()
                else:
                    # Give the rcd 20 seconds to start before we give up.
                    if time.time() - self.start_time >= 20:
                        self.dialog.response(gtk.RESPONSE_CANCEL)
                        return 0
            else:
                print "Contacted daemon"
                self.dialog.response(gtk.RESPONSE_OK)
                self.server = s
                return 0

        return 1

###############################################################################

have_channels = 0
cached_channels = {}
cached_channel_icons = {}

def reset_channels():
    global have_channels, cached_channels, cached_channel_icons
    have_channels = 0
    cached_channels = {}
    cached_channel_icons = {}

def fetch_all_channels():
    global have_channels, cached_channels
    
    if have_channels:
        return

    channel_list = server.rcd.packsys.get_channels()
    for c in channel_list:
        cached_channels[str(c["id"])] = c

    have_channels = 1


def get_all_channels():
    fetch_all_channels()
    return cached_channels.values()


def get_channel(id):
    fetch_all_channels()
    id = str(id)
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

    if id <= 0:
        return None

    if width > 0 and height > 0:
        key = "%s %d %d" % (str(id), width, height)
    else:
        key = str(id)
    
    if cached_channel_icons.has_key(key):
        return cached_channel_icons[key]

    pixbuf = None
    
    if width > 0 and height > 0:
        
        original = get_channel_icon(id)
        pixbuf = original.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)

    else:

        # FIXME: a hack until the mono icon gets fixed
        if get_channel_name(id) == "mono":
            pixbuf = red_pixbuf.get_pixbuf("mono-override")
            cached_channel_icons[key] = pixbuf
            return pixbuf
            
        #assert server
        try:
            icon_data = server.rcd.packsys.get_channel_icon(id)
        except ximian_xmlrpclib.Fault, f:
            if f.faultCode == fault.no_icon:
                icon_data = None
            else:
                raise

        if icon_data:
            loader = gtk.gdk.gdk_pixbuf_loader_new()
            loader.write(icon_data.data, len(icon_data.data))
            loader.close()
            pixbuf = loader.get_pixbuf()

    if pixbuf is None:
        pixbuf = red_pixbuf.get_pixbuf("empty", width, height)

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
    if pkg.has_key("channel") and pkg["channel"] > 0:
        return get_channel_name(pkg["channel"])
    elif pkg.has_key("channel_guess"):
        return get_channel_name(pkg["channel_guess"])
    else:
        return "None"

def get_package_channel_icon(pkg, width=0, height=0):
    if pkg.has_key("channel") and pkg["channel"] > 0:
        return get_channel_icon(pkg["channel"], width, height)
    elif pkg.has_key("channel_guess"):
        return get_channel_icon(pkg["channel_guess"], width, height)
    else:
        return None

def get_package_EVR(pkg):
    epoch_str = ""
    rel_str = ""
    if pkg["has_epoch"]:
        epoch_str = "%d:" % pkg["epoch"]
    if pkg["release"]:
        rel_str = "-%s" % pkg["release"]
    return "%s%s%s" % (epoch_str, pkg["version"], rel_str)

def get_package_info(pkg):
    if not pkg.has_key("__info"):
        pkg["__info"] = server.rcd.packsys.package_info(pkg)
    return pkg["__info"]

def get_package_history(pkg):
    return server.rcd.log.query_log([["name", "=", pkg["name"]]])

def get_package_key(pkg):
    key = pkg.get("__key")
    if not key:
        key = pkg["__key"] = "%s/%s/%d" % (pkg["name"],
                                           get_package_EVR(pkg),
                                           pkg["channel"])
    return key

def get_dep_EVR(dep):
    evr = get_package_EVR(dep)
    return dep["relation"] + " " + evr

###############################################################################

def filter_package_dups(pkgs):

    def pkg_to_key(p):
        ch = p["channel"] or p.get("channel_guess", 0);
        return "%d:%s:%d:%s:%s" % \
               (ch, p["name"], p["epoch"], p["version"], p["release"])

    in_channel = {}
    for p in pkgs:
        if p["installed"] and p["channel"]:
            in_channel[pkg_to_key(p)] = 1

    filtered = []
    for p in pkgs:
        if p["channel"] != 0 or not in_channel.has_key(pkg_to_key(p)):
            filtered.append(p)

    return filtered

###############################################################################

def byte_size_to_string(sz):
    if sz <= 0:
        return ""
    elif sz < 1024:
        return "%d bytes" % sz
    elif sz < 1048576:
        return "%d kb" % (sz/1024)
    else:
        return "%.1f mb" % (sz/(1048576.0))

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

    lines = []

    if n == -1:
        lines.append(str)
    else:
        lines.append(str[0:n])
        lines = lines + linebreak(str[n+1:], width)

    return lines

###############################################################################

def dialog_from_fault(f, parent=None, post_dialog_thunk=None):
    if not f:
        return
    lines = linebreak(f.faultString, 40)
    lines.append("(fault %d)" % f.faultCode)

    dialog = gtk.MessageDialog(parent, 0, gtk.MESSAGE_WARNING,
                               gtk.BUTTONS_OK,
                               string.join(lines, "\n"))
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
                        parent=None):

    if not message:
        message = _("Please wait while getting data.")

    dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO,
                               gtk.BUTTONS_CANCEL, message)

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
