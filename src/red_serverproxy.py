
import threading
import ximian_xmlrpclib
import gobject, gtk
import rcd_util, red_serverlistener

_dead_daemon_lock = threading.Lock()

def show_daemon_dialog(thread):

    def server_is_alive_cb(thread):
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO,
                                   gtk.BUTTONS_CLOSE,
                                   "Connection to daemon restored.\n" \
                                   "(We need a better message here too.)")
        dialog.show()
        gtk.threads_enter()
        dialog.run()
        gtk.threads_leave()
        dialog.destroy()
        _dead_daemon_lock.release()
        red_serverlistener.thaw_polling()

        # This is an EVIL HACK to allow us to re-start the same thread.
        # It probably isn't portable, and will probably break in the
        # next version of python.  Basically, I suck.
        threading.Thread.__init__(thread)
        thread.start()
        
        return 0

    def wait_for_server_cb(dialog, thread):
        try:
            server = rcd_util.get_server()
            ping = server.rcd.system.ping()
            if ping:
                dialog.destroy()
                gtk.idle_add(server_is_alive_cb, thread)
                return 0
        except: # FIXME: don't just mindlessly catch all exceptions
            print "waiting for server..."
            return 1

    def dialog_response_cb(dialog, val):
        gtk.mainquit()

    def create_warning_dialog_cb(thread):
        _dead_daemon_lock.acquire()
        red_serverlistener.freeze_polling()
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                                   gtk.BUTTONS_NONE,
                                   "Lost contact with the daemon!\n" \
                                   "(We need a better message here)" )
        dialog.add_button("Exit Red Carpet", 1)
        dialog.set_modal(1)
        dialog.connect("response", dialog_response_cb)
        dialog.show_all()
        gtk.timeout_add(500, wait_for_server_cb, dialog, thread)
        print "Lost Server!"
        return 0

    # Popup the dialog in the main thread.
    gtk.idle_add(create_warning_dialog_cb, thread)

class ServerThread(threading.Thread, gobject.GObject):

    def __init__(self, server, method, args):
        threading.Thread.__init__(self)
        gobject.GObject.__init__(self)
        self.__lock = threading.Lock()
        self.__server = server
        self.__method = method
        self.__args = args
        self.__result = None
        self.__ready  = 0
        self.__cancelled = 0

    def run(self):

        # We acquire and release the dead daemon lock before
        # trying any xmlrpc call.  The lock gets acquired when our
        # "daemon is dead" warning dialog pops up -- this allows us
        # to block any more proxied xmlrpc calls until contact with
        # the daemon is re-established.
        _dead_daemon_lock.acquire()
        _dead_daemon_lock.release()
        
        try:
            result = getattr(self.__server, self.__method)(*self.__args)
        except:
            # FIXME: Handle the correct exceptions, not just this catch all.
            # We will re-start the thread if
            show_daemon_dialog(self)
            return
            
            # If we return from the call to show_daemon_dialog, the
            # server must have come back --- so we re-try the xmlrpc
            # call.
            self.run()
            return

        self.__lock.acquire()
        if not self.__cancelled:
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

    
