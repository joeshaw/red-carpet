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
import gtk
import ximian_xmlrpclib
import rcd_util
import red_settings
from red_gettext import _

class IncorrectVersionError(exceptions.Exception):
    def __init__(self, args=None):
        self.args = args


def show_error_message(msg):
    dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                               gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                               _("Unable to connect to the "
                                 "daemon:\n '%s'.") % msg)
    dialog.set_title("") # Gnome HIG says no titles on these sorts of dialogs
    gtk.threads_enter()
    dialog.run()
    gtk.threads_leave()
    dialog.destroy()


def get_credentials(show_dialog):
    if show_dialog:
        dialog = red_settings.ConnectionWindow()
        dialog.run()
        gtk.threads_leave()
        uri, user, pwd, local = dialog.get_server_info()
        dialog.destroy()
        if not uri:
            return (None, None, None, None)
        return (uri, user, pwd, local)

    else:
        data = red_settings.DaemonData()
        return data.data_get()

def save_credentials(uri, user, password, local):
    data = red_settings.DaemonData()

    data.local_set(local)
    data.url_set(uri)
    data.user_set(user)
    data.password_set(password)
    data.save_config()

def check_rcd_version(major, minor, micro):
    req_major = 1
    req_minor = 2
    req_micro = 1

    # Guard for NoneType
    major = major or 0
    minor = minor or 0
    micro = micro or 0

    req_version = (req_major * 100) + (req_minor * 10) + req_micro
    version = (major * 100) + (minor * 10) + micro

    if version < req_version:
        raise IncorrectVersionError, _("Detected Red Carpet Daemon version %d.%d.%d.\n"
                                       "Version %d.%d.%d (or newer) is required.") % \
                                       (major, minor, micro, req_major, req_minor, req_micro)

    return 1

def connect_real(uri, user=None, password=None):
    transport_debug = os.environ.has_key("RC_TRANSPORT_DEBUG")

    try:
        server = ximian_xmlrpclib.Server(uri,
                                         auth_username=user,
                                         auth_password=password,
                                         verbose=transport_debug)

        ping = server.rcd.system.ping()
        check_rcd_version(ping.get("major_version"),
                          ping.get("minor_version"),
                          ping.get("micro_version"))
    except:
        raise

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

        gtk.threads_enter()
        response = self.dialog.run()
        gtk.threads_leave()
        self.dialog.destroy()

        if response == gtk.RESPONSE_CANCEL or \
           response == gtk.RESPONSE_DELETE_EVENT:
            if self.service_pid != -1:
                os.kill(self.service_pid, signal.SIGKILL)
            if self.rcd_pid != -1:
                os.kill(self.rcd_pid, signal.SIGKILL)

        return self.success

    def wait_for_daemon_cb(self):
        if self.service_pid != -1:
            pid, status = os.waitpid(self.service_pid, os.WNOHANG)
            if pid == self.service_pid:
                self.service_pid = -1

                pidfile = open("/var/run/rcd.pid")
                pidstr = pidfile.read()
                self.rcd_pid = int(pidstr)

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


def start_daemon():
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


def connect(local=0,
            host=None,
            user=None,
            password=None,
            show_dialog=0):

    server = None
    valid_credentials = 0

    if local:
        valid_credentials = 1

    if host:
        valid_credentials = 1
        if password:
            password = rcd_util.md5ify_password(password)

    while 1:
        if not valid_credentials:
            host, user, password, local = get_credentials(show_dialog)

        uri = munge_uri(local, host)
        valid_credentials = 0

        if not uri:
            break

        err_msg = None
        try:
            server = connect_real(uri, user, password)
        except IncorrectVersionError, f:
            show_error_message(f)
            show_dialog = 1
            continue
        except socket.error, f:
            err_msg = f[1]
        except ximian_xmlrpclib.ProtocolError, f:
            err_msg = f
        except ximian_xmlrpclib.Fault, f:
            err_msg = f.faultString
        except:
            raise

        else:
            break

        if not show_dialog:
            show_dialog = 1
            continue

        elif local and os.geteuid() == 0 and os.path.exists("/sbin/service"):
            if start_daemon():
                valid_credentials = 1
                continue

        show_error_message(err_msg)


    if isinstance(server, ximian_xmlrpclib.Server):
#        save_credentials(host, user, password, local)
        return server, local

    return None
