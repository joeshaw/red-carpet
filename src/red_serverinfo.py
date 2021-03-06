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

import sys, os, string, gtk, zlib
import rcd_util

from red_gettext import _

def destroy_server_info(app):
    if getattr(app.server_info_window, "__filesel", None):
        app.server_info_window.__filesel.destroy()

    app.server_info_window.destroy()
    app.server_info_window = None


def view_server_info_cb(app):

    # We only allow one server info window at a time
    if getattr(app, "server_info_window", None):
        destroy_server_info(app)
    
    server = rcd_util.get_server()
    try:
        results = server.rcd.system.ping()
    except:
        results = None

    if results:
        dialog_type = gtk.MESSAGE_INFO

        messages = [_("The daemon identified itself as:"), ""]

        if results.has_key("name"):
            messages.append("%s" % results["name"])

        if results.has_key("copyright"):
            messages.append(results["copyright"])

        messages.append("")

        if results.has_key("distro_info"):
            messages.append(_("System type") + ": " + results["distro_info"])

        if results.has_key("server_url"):
            messages.append(_("Server URL") + ": " + results["server_url"])

        if results.get("server_premium", 0):
            messages.append(_("Server supports enhanced features."))

    else: # couldn't ping the server

        dialog_type = gtk.MESSAGE_WARNING
        messages = [_("Unable to contact the daemon.")]

    dialog = gtk.MessageDialog(app, 0, dialog_type, gtk.BUTTONS_CLOSE,
                               string.join(messages, "\n"))
    dialog.set_default_response(gtk.RESPONSE_OK)
    if results:
        bbox = gtk.HButtonBox()
        dialog.vbox.pack_start(bbox, expand=0, fill=0, padding=6)
        button = gtk.Button(_("Dump daemon info to XML file"))
        button.connect("clicked", lambda x,y:select_and_dump(y), dialog)
        bbox.add(button)

    def destroy_cb(x, y, z):
        destroy_server_info(z)
    dialog.connect("response", destroy_cb, app)
    dialog.show_all()

    app.server_info_window = dialog


def dump_xml(filename):
    try:
        f = open(filename, "w")
    except IOError, e:
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                                   gtk.BUTTONS_OK,
                                   _("Could not open file '%s': %s") % (filename, e.strerror))
        dialog.run()
        dialog.destroy()
        return

    server = rcd_util.get_server_proxy()

    def dump_finished_cb(worker, f):
        if not worker.is_cancelled():
            try:
                dump = worker.get_result()
            except ximian_xmlrpclib.Fault, f:
                rcd_util.dialog_from_fault(f)
            else:
                f.write(zlib.decompress(dump.data))
        f.close()

    worker = server.rcd.packsys.dump()
    rcd_util.server_proxy_dialog(worker,
                                 callback=dump_finished_cb,
                                 user_data=f)


def select_and_dump(parent):

    def filesel_destroy(app):
        if getattr(app, "__filesel", None):
            app.__filesel.destroy()
            app.__filesel = None

    def get_file_cb(button, parent):
        filename = parent.__filesel.get_filename()
        if filename:
            dump_xml(filename)
            filesel_destroy(parent)

    # We only allow one filesel window at a time
    if getattr(parent, "__filesel", None):
        parent.__filesel.present()
        return

    filesel = gtk.FileSelection(_("Choose file to write XML to"))
    filesel.set_filename(os.environ.get("HOME", "") + "/") # need trailing /
    filesel.ok_button.connect("clicked", get_file_cb, parent)
    filesel.cancel_button.connect("clicked", lambda x,y:filesel_destroy(y), parent)
    filesel.set_transient_for(parent)
    filesel.show()

    parent.__filesel = filesel
