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

import gobject, gtk
import rcd_util
import red_extra, red_pixbuf

class DepView(red_extra.ListView):

    def __init__(self):
        red_extra.ListView.__init__(self)
        self.store = gtk.ListStore(gtk.gdk.Pixbuf.__gtype__,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING, gobject.TYPE_STRING,
                                   gobject.TYPE_STRING)
        self.set_model(self.store)
        self.row = 0

        sel = self.get_selection()
        sel.set_mode(gtk.SELECTION_NONE)

        col = gtk.TreeViewColumn("Channel", gtk.CellRendererPixbuf(), pixbuf=0)
        self.append_column(col)

        col = gtk.TreeViewColumn("Package", gtk.CellRendererText(), markup=1)
        self.append_column(col)
        
        col = gtk.TreeViewColumn("New Version", gtk.CellRendererText(), markup=2)
        self.append_column(col)
        
        col = gtk.TreeViewColumn("Current Version", gtk.CellRendererText(), markup=3)
        self.append_column(col)
        
        col = gtk.TreeViewColumn("Size", gtk.CellRendererText(), markup=4)
        self.append_column(col)


    def add_row(self, icon, name, new_version, old_version, size, bold=0):

        if icon is None:
            icon = red_pixbuf.get_pixbuf("lock", width=1, height=1)

        if bold:
            name        = "<b>%s</b>" % name
            new_version = "<b>%s</b>" % new_version
            old_version = "<b>%s</b>" % old_version
            size        = "<b>%s</b>" % size

        iter = self.store.append()
        self.store.set(iter, 0, icon, 1, name, 2, new_version, 3, old_version, 4, size)
        self.row += 1

    def add_empty_row(self, sizer=""):
        self.add_row(None, sizer, "", "", "")

    def add_header(self, msg, fg_color=None, bg_color=None):
        cell = gtk.CellRendererText()
        cell.set_property("markup", "<b><big>%s</big></b>" % msg)

        # FIXME: We ignore the fg_color for now.

        if not bg_color:
            bg_color = self.get_colormap().alloc_color("red")
            
        self.add_spanner_with_background(self.row, 0, -1, cell, bg_color)
        self.add_empty_row(sizer="<b><big>Ayq</big></b>")

    def add_note(self, msg):
        cell = gtk.CellRendererText()
        cell.set_property("markup", "* " + msg)

        self.add_spanner(self.row, 1, -1, cell)
        self.add_empty_row()

    def add_package(self, pkg):

        ch_icon = rcd_util.get_package_channel_icon(pkg, width=24, height=24)
        name = pkg.get("name", "???")
        new_evr = rcd_util.get_package_EVR(pkg)
        old_evr = "-"
        if pkg.has_key("__old_package"):
            old_evr = rcd_util.get_package_EVR(pkg["__old_package"])
        size = rcd_util.byte_size_to_string(pkg.get("file_size"))

        self.add_row(ch_icon, name, new_evr, old_evr, size, bold=1)
        
        
    
