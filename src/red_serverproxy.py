
import threading
import ximian_xmlrpclib
import gobject, gtk

win = None

def show_daemon_dialog():
    def popup_warning_cb():
        global win
        if not win:
            win = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
                                    buttons=gtk.BUTTONS_OK,
                                    message_format="Unable to connect to daemon")
            win.set_modal(1)
            gtk.threads_enter()
            win.run()
            gtk.threads_leave()
            win.destroy()
            win = None

        return 0

    # Popup the dialog in the main thread.
    gtk.idle_add(popup_warning_cb)

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
        try:
            result = getattr(self.__server, self.__method)(*self.__args)
        except:
            # FIXME: Handle the correct exceptions, not just this catch all.
            show_daemon_dialog()
            self.__lock.acquire()
            if not self.__cancelled:
                self.__ready = 1
                self.__cancelled = 1
                self.emit("ready")
            self.__lock.release()
            
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

    
