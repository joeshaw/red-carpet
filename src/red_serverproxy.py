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

import threading, gobject, gtk
import red_deaddaemon
import ximian_xmlrpclib

class ServerThread(threading.Thread, gobject.GObject):

    def __init__(self, server, method, args):
        threading.Thread.__init__(self)
        gobject.GObject.__init__(self)
        self.__lock = threading.Lock()
        self.__server = server
        self.__method = method
        self.__args = args
        self.__result = None
        self.__fault = None
        self.__ready  = 0
        self.__cancelled = 0

    def run(self):

        try:
            result = getattr(self.__server, self.__method)(*self.__args)
        except ximian_xmlrpclib.Fault, f:
            self.__fault = f
        except:
            # FIXME: Handle the correct exceptions, not just this catch-all.
            # We will re-start the thread if the server comes back.
            red_deaddaemon.show_daemon_dialog()
            return

        self.__lock.acquire()
        if not self.__cancelled and not self.__fault:
            self.__result = result
        self.__ready = 1
        if not self.__cancelled:
            # We want to emit our signal in the main thread.
            def emit_ready_cb(th):
                th.emit("ready")
                return 0
            gtk.idle_add(emit_ready_cb, self)
        self.__lock.release()

    def cancel(self):
        self.__lock.acquire()
        if not self.__cancelled:
            self.__ready = 1
            self.__cancelled = 1
            self.emit("ready")
        self.__lock.release()

    def is_cancelled(self):
        return self.__cancelled

    def is_ready(self):
        return self.__ready

    def get_result(self):
        if self.__fault:
            raise self.__fault
        else:
            return self.__result

gobject.type_register(ServerThread)

gobject.signal_new("ready",
                   ServerThread,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())


class ServerMethod:

    def __init__(self, server, method):
        self.__server = server
        self.__method = method

    def __getattr__(self, name):
        self.__method = "%s.%s" % (self.__method, name)
        return self

    def __call__(self, *args):
        t = ServerThread(self.__server, self.__method, args)
        t.start()
        return t


class ServerProxy:

    def __init__(self, server):
        self.__server = server

    def __nonzero__(self):
        return 1

    def __getattr__(self, method):
        return ServerMethod(self.__server, method)

    def __repr__(self):
        return "<Server Proxy for %s>" % repr(self.__server)

    __str__ = __repr__

    
