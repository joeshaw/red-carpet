###
### Copyright 2002 Ximian, Inc.
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

import sys
import gobject, gtk
import string
import zlib

import ximian_xmlrpclib
import rcd_util

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

        messages = ["The server identified itself as:", ""]

        if results.has_key("name"):
            messages.append("%s" % results["name"])

        if results.has_key("copyright"):
            messages.append(results["copyright"])

        messages.append("")

        if results.has_key("distro_info"):
            messages.append("System type: %s" % results["distro_info"])

        if results.has_key("server_url"):
            messages.append("Server URL: %s" % results["server_url"])

        if results.get("server_premium", 0):
            messages.append("Server supports enhanced features.")

    else: # couldn't ping the server

        dialog_type = gtk.MESSAGE_WARNING
        messages = ["Unable to contact the server."]

    dialog = gtk.MessageDialog(app, 0, dialog_type, gtk.BUTTONS_OK,
                               string.join(messages, "\n"))
    if results:
        bbox = gtk.HButtonBox()
        dialog.vbox.add(bbox)
        button = gtk.Button("Dump server info to XML file")
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
                                   "Could not open file '%s': %s" % (filename, e.strerror))
        dialog.run()
        dialog.destroy()
        return

    server = rcd_util.get_server()
    f.write(zlib.decompress(server.rcd.packsys.dump().data))
    f.close()

def select_and_dump(parent):
    def get_file_cb(button, filesel):
        filename = filesel.get_filename()
        if filename:
            dump_xml(filename)
            filesel.destroy()

    # We only allow one filesel window at a time
    if getattr(parent, "__filesel", None):
        parent.__filesel.present()
        return

    filesel = gtk.FileSelection("Choose file to dump")
    filesel.ok_button.connect("clicked", get_file_cb, filesel)
    filesel.cancel_button.connect("clicked", lambda x,y:y.destroy(), filesel)
    filesel.show()

    parent.__filesel = filesel
