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

import os, stat, string, sys, threading
import gobject, gtk
from red_gettext import _

import ximian_xmlrpclib

import rcd_util
import red_pendingops

try:
    import urllib
except ImportError:
    have_urllib = 0
else:
    have_urllib = 1

def can_install_remote():
    global have_urllib
    return have_urllib

def install_local(parent):
    # FIXME: Add remote daemon support
    
    def get_file_cb(b, fs):
        server = rcd_util.get_server()

        err = 0
        plist = []

        try:
            # We need to do the stat check because if we select something in
            # the filesel and then unselect it (with control-click), we'll
            # get the parent directory for that file, not the file itself.

            def is_valid(x):
                try:
                    return stat.S_ISDIR(os.stat(x).st_mode)
                except OSError, e:
                    # File probably doesn't exist.
                    return 0
            
            plist = [server.rcd.packsys.query_file(x) \
                     for x in fs.get_selections() \
                     if not is_valid(x)]
        except ximian_xmlrpclib.Fault, f:
            if f.faultCode == rcd_util.fault.package_not_found \
               or f.faultCode == rcd_util.fault.invalid_package_file:
                dialog = gtk.MessageDialog(fs, gtk.DIALOG_DESTROY_WITH_PARENT,
                                           gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                           _("%s is not a valid package") % x)
                dialog.run()
                dialog.destroy()
                err = 1
            else:
                raise
        else:
            if not plist:
                dialog = gtk.MessageDialog(fs, gtk.DIALOG_DESTROY_WITH_PARENT,
                                           gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                           _("There are no valid packages to install"))
                dialog.run()
                dialog.destroy()
                err = 1

        if not err:
            fs.destroy()
            [red_pendingops.set_action(x, red_pendingops.TO_BE_INSTALLED) for x in plist]
            

    filesel = gtk.FileSelection(_("Install from File"))
    filesel.set_select_multiple(1)
    filesel.ok_button.connect("clicked", get_file_cb, filesel)
    filesel.cancel_button.connect("clicked", lambda x,y:y.destroy(), filesel)
    filesel.set_transient_for(parent)
    filesel.show()

def install_remote(parent):

    def get_file_cb(b, w, e):
        w.destroy()

        url = e.get_text()

        dialog = gtk.MessageDialog(None, 0,
                                   gtk.MESSAGE_INFO, 0,
                                   _("Downloading %s...") % url)
        button = dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

        progress_bar = gtk.ProgressBar()
        progress_bar.show()
        dialog.vbox.pack_start(progress_bar)

        def pulse_cb(pb):
            pb.pulse()
            return 1
        timeout_id = gtk.timeout_add(100, pulse_cb, progress_bar)

        download_watcher = DownloadWatcher(url)
        def ready_cb(dw, p, d, tid):
            gtk.timeout_remove(tid)
            d.destroy()
            if p:
                red_pendingops.set_action(p, red_pendingops.TO_BE_INSTALLED)
            else:
                if not dw.cancelled:
                    dialog = gtk.MessageDialog(None, 0,
                                               gtk.MESSAGE_ERROR,
                                               gtk.BUTTONS_OK,
                                               _("%s is not a valid package") % dw.url)
                    gtk.threads_enter()
                    dialog.run()
                    gtk.threads_leave()
                    dialog.destroy()

        download_watcher.connect("ready", ready_cb, dialog, timeout_id)

        def cancel_clicked_cb(b, dw, d):
            dw.cancelled = 1
            d.hide()
        button.connect("clicked", cancel_clicked_cb, download_watcher, dialog)

        dialog.show()
        download_watcher.start()
        
    win = gtk.Dialog(_("Install from URL"))
    win.set_has_separator(0)

    hbox = gtk.HBox(0, 4)

    label = gtk.Label(_("Package URL:"))
    hbox.pack_start(label)

    entry = gtk.Entry()
    entry.set_activates_default(1)
    hbox.pack_start(entry)

    hbox.show_all()
    win.vbox.pack_start(hbox)

    button = win.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
    button.connect("clicked", lambda x, y:y.destroy(), win)

    button = win.add_button(gtk.STOCK_OK, gtk.RESPONSE_CLOSE)
    button.grab_default()
    button.connect("clicked", get_file_cb, win, entry)
    button.set_sensitive(0)

    def changed_cb(e, b):
        if string.strip(e.get_text()):
            b.set_sensitive(1)
        else:
            b.set_sensitive(0)
    entry.connect("changed", changed_cb, button)

    win.set_transient_for(parent)
    win.show()

class DownloadWatcher(threading.Thread, gobject.GObject):

    def __init__(self, url):
        threading.Thread.__init__(self)
        gobject.GObject.__init__(self)
        self.lock = threading.Lock()
        self.cancelled = 0
        self.url = url

    def fetch_package(self):
        proto, rest = urllib.splittype(self.url)

        if not proto:
            return None

        name = "open_" + proto
        if "-" in name:
            # replace - with _
            name = string.join(string.split(name, "-"), "_")

        if not hasattr(urllib.URLopener, name):
            return None

        try:
            u = urllib.URLopener().open(self.url)
        except IOError:
            return None

        data = []

        while 1:
            d = u.read(1024)

            if not d:
                break
            data += d

            if self.cancelled:
                return None

        pdata = ximian_xmlrpclib.Binary(data)

        server = rcd_util.get_server()

        try:
            p = server.rcd.packsys.query_file(pdata)
        except ximian_xmlrpclib.Fault, f:
            if f.faultCode == rcd_util.fault.package_not_found \
               or f.faultCode == rcd_util.fault.invalid_package_file:
                return None
            else:
                raise

        p["package_data"] = pdata

        return p

    def run(self):
        self.lock.acquire()

        p = self.fetch_package()

        # emit the signal in the main thread.
        def emit_ready_cb(th, p):
            th.emit("ready", p)
            return 0
        gtk.idle_add(emit_ready_cb, self, p)

        self.lock.release()

gobject.type_register(DownloadWatcher)

gobject.signal_new("ready",
                   DownloadWatcher,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))
