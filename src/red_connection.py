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

import socket
import os
import exceptions
import signal
import string
import time
import gobject
import gtk
import ximian_xmlrpclib
import rcd_util
import red_main
import red_pixbuf
import red_settings
from red_gettext import _

class IncorrectVersionError(exceptions.Exception):
    def __init__(self, args=None):
        self.args = args


def show_error_message(msg, parent=None):
    dialog = gtk.MessageDialog(parent, gtk.DIALOG_MODAL,
                               gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                               _("Unable to connect to the "
                                 "daemon:\n '%s'.") % msg)
    dialog.set_title("") # Gnome HIG says no titles on these sorts of dialogs
    dialog.run()
    dialog.destroy()

def check_rcd_version(major, minor, micro):
    req_major = 1
    req_minor = 3
    req_micro = 2

    # Guard for NoneType
    major = major or 0
    minor = minor or 0
    micro = micro or 0

    req_version = (req_major * 100) + (req_minor * 10) + req_micro
    version = (major * 100) + (minor * 10) + micro

    if version < req_version:
        raise IncorrectVersionError, _("Detected Red Carpet Daemon version %d.%d.%d.\n"
                                       "Version %d.%d.%d (or newer) is required") % \
                                       (major, minor, micro, req_major, req_minor, req_micro)

    return 1

def connect_real(uri, user=None, password=None):
    transport_debug = os.environ.has_key("RC_TRANSPORT_DEBUG")

    server = ximian_xmlrpclib.Server(uri,
                                     auth_username=user,
                                     auth_password=password,
                                     verbose=transport_debug)

    ping = server.rcd.system.ping()
    check_rcd_version(ping.get("major_version"),
                      ping.get("minor_version"),
                      ping.get("micro_version"))

    return server


class StartDaemon:
    def __init__(self):
        self.start_time = 0
        self.service_pid = -1;
        self.rcd_pid = -1;
        self.success = 0

        # LSB compliant distros should have the
        # following
        self.cmd = "/etc/init.d/rcd"
        self.args = (self.cmd, "start")

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

        gtk.timeout_add(500, self.wait_for_daemon_cb)

        response = self.dialog.run()
        self.dialog.destroy()

        if response == gtk.RESPONSE_CANCEL or \
           response == gtk.RESPONSE_DELETE_EVENT:
            if self.service_pid != -1:
                os.kill(self.service_pid, signal.SIGKILL)
            if self.rcd_pid != -1:
                try:
                    os.kill(self.rcd_pid, signal.SIGKILL)
                except OSError, e: # Couldn't kill it, probably already dead
                    pass

        return self.success

    def wait_for_daemon_cb(self):
        if self.service_pid != -1:
            pid, status = os.waitpid(self.service_pid, os.WNOHANG)
            if pid == self.service_pid:
                self.service_pid = -1

                try:
                    pidfile = open("/var/run/rcd.pid")
                except IOError: # File doesn't exist?
                    self.dialog.response(gtk.RESPONSE_CANCEL)
                    return 0
                else:
                    pidstr = pidfile.read()
                    self.rcd_pid = int(pidstr)
                    pidfile.close()

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
                self.success = 1
                return 0

        return 1


def can_start_daemon():
    return os.geteuid() == 0 and os.path.exists("/etc/init.d/rcd")

def start_daemon():
    dialog = gtk.MessageDialog(None,
                               gtk.DIALOG_MODAL,
                               gtk.MESSAGE_WARNING,
                               gtk.BUTTONS_YES_NO,
                               _("Red Carpet requires a Red Carpet "
                                 "Daemon to be running.\n"
                                 "Would you like to start one now?"))
    dialog.set_title("") # Conform to GNOME HIG
    response = dialog.run()
    dialog.destroy()

    if response == gtk.RESPONSE_YES:
        sd = StartDaemon()
        # This will block with a dialog.
        return sd.run()

    return 0


def munge_uri(local, uri):
    if local:
        uri = "/var/run/rcd/rcd"
    elif uri:
        host = uri
        # Prepend "https://" if it isn't already specified
        if string.find(host, "http://") == -1 \
           and string.find(host, "https://") == -1:
            host = "https://" + host

        # Append default port number (505) if one isn't specified
        hparts = string.split(host, ":", 2)
        if len(hparts) < 3:
            hparts.append("505")
        uri = string.join(hparts, ":") + "/RPC2"

    return uri

class ConnectException(Exception):

    def __init__(self, err_msg):
        self.err_msg = err_msg
    def __repr__(self):
        return "<ConnectException '%s'>" % self.err_msg

class ConnectionNotify(gobject.GObject):
    def __init__(self):
        gobject.GObject.__init__(self)
        self.current_host = None

    def notify_real(self, host):
        self.emit("connected", host)

    def notify(self):
        if self.current_host:
            self.emit("connected", self.current_host)

    def notify_new(self, host, local):
        if local:
            host = "Localhost"
        self.current_host = host
        self.notify_real(host)

gobject.signal_new("connected",
                   ConnectionNotify,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))

notifier = None

def get_notifier():
    global notifier

    if not notifier:
        notifier = ConnectionNotify()

    return notifier

# NOTE: password must be md5ified.
def connect(local, host, user, password):
    server = None

    uri = munge_uri(local, host)

    err_msg = None
    try:
        server = connect_real(uri, user, password)
    except IncorrectVersionError, f:
        err_msg = f
    except socket.error, f:
        err_msg = f[1]
    except ximian_xmlrpclib.ProtocolError, f:
        err_msg = f
    except ximian_xmlrpclib.Fault, f:
        err_msg = f.faultString
    except:
        raise

    if err_msg:
        raise ConnectException(err_msg)

    get_notifier().notify_new(host, local)

    return server

def connect_from_window(parent=None):
    server = None
    local = 0

    while server is None:
        window = ConnectionWindow()
        if parent:
            window.set_transient_for(parent)
        response = window.run()

        connect_info = window.get_daemon_info()
        local = connect_info[0]
        window.destroy()

        if response != gtk.RESPONSE_ACCEPT:
            return None, 0

        try:
            server = connect(*connect_info)
        except ConnectException, e:
            if local and can_start_daemon():
                started = start_daemon()
                if started:
                    try:
                        server = connect(*connect_info)
                    except ConnectException, e:
                        show_error_message(e.err_msg, parent=parent)
            else:
                show_error_message(e.err_msg, parent=parent)

    return server, local

class ConnectionWindow(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self, red_main.get_title())

        self.set_icon(red_pixbuf.get_pixbuf("red-carpet"))

        self.local = 1

        self.data = red_settings.DaemonData()
        self.build()
        self.populate()

    def build(self):
        self.local_rb = gtk.RadioButton(None,
                                        _("Connect to daemon on this computer"))
        self.vbox.pack_start(self.local_rb)

        self.remote_rb = gtk.RadioButton(self.local_rb,
                                         _("Connect to a remote daemon"))
        self.vbox.pack_start(self.remote_rb)

        table = gtk.Table(3, 2)
        table.set_border_width(5)
        table.set_col_spacings(5)
        table.set_row_spacings(5)

        l = gtk.Label(_("Server:"))
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 0, 1)

        l = gtk.Label(_("User name:"))
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 1, 2)

        l = gtk.Label(_("Password:"))
        l.set_alignment(0, 0.5)
        table.attach_defaults(l, 0, 1, 2, 3)

        self.url = gtk.Combo()
        self.url.disable_activate() # Don't activate the dropdown with enter
        self.url.entry.set_activates_default(1)
        table.attach_defaults(self.url, 1, 2, 0, 1)

        self.user = gtk.Entry()
        self.user.set_activates_default(1)
        table.attach_defaults(self.user, 1, 2, 1, 2)

        self.password = gtk.Entry()
        self.password.set_visibility(0)
        self.password.set_activates_default(1)
        table.attach_defaults(self.password, 1, 2, 2, 3)
        
        hbox = gtk.HBox()
        hbox.pack_start(table, padding=20)
        self.vbox.pack_start(hbox)

        self.vbox.show_all()

        # desensitize the table by default.
        table.set_sensitive(0)

        def toggled_cb(b, s):
            s.local = b.get_active()
        self.local_rb.connect("toggled", toggled_cb, self)

        self.remote_rb.connect("toggled",
                               lambda x,y:y.set_sensitive(x.get_active()),
                               table)

        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        b = self.add_button(_("Connect"), gtk.RESPONSE_ACCEPT)
        b.grab_default()
        def response_cb(dialog, id, this):
            if id == gtk.RESPONSE_ACCEPT:
                this.save()

        self.connect("response", response_cb, self)

    def populate(self):
        buf = self.data.url_get_list()
        if buf:
            self.url.set_popdown_strings(buf)

        buf = self.data.user_get()
        if buf:
            self.user.set_text(buf)

        buf = self.data.password_get_for_ui()
        if buf:
            self.password.set_text(buf)

        if self.data.local_get():
            self.local_rb.set_active(1)
        else:
            self.remote_rb.set_active(1)

    def save(self):
        self.data.local_set(self.local)

        if not self.local:
            self.data.url_set(self.url.entry.get_text())
            self.data.user_set(self.user.get_text())
            self.data.password_set(self.password.get_text())

        self.data.save_config()

    def get_daemon_info(self):
        local = self.local_rb.get_active()
        url = self.url.entry.get_text()
        user = self.user.get_text()
        password = self.password.get_text()

        if password == "-*-unchanged-*-":
            password = self.data.password_get()
        else:
            password = rcd_util.md5ify_password(password)

        return (local, url, user, password)
