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

import string
import gobject, gtk
import rcd_util
import red_extra, red_pixbuf
from red_gettext import _

def escape_markup(text):
    text = string.replace(text, "&", "&amp;")
    text = string.replace(text, "<", "&lt;")
    text = string.replace(text, ">", "&gt;")
    text = string.replace(text, "'", "&apos;")
    text = string.replace(text, "\"", "&quot;")

    return text

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

        col = gtk.TreeViewColumn(_("Catalog"), gtk.CellRendererPixbuf(), pixbuf=0)
        self.append_column(col)

        col = gtk.TreeViewColumn(_("Package"), gtk.CellRendererText(), markup=1)
        self.append_column(col)
        
        col = gtk.TreeViewColumn(_("Current Version"), gtk.CellRendererText(), markup=3)
        self.append_column(col)

        col = gtk.TreeViewColumn(_("New Version"), gtk.CellRendererText(), markup=2)
        self.append_column(col)
        
        col = gtk.TreeViewColumn(_("Size"), gtk.CellRendererText(), markup=4)
        self.append_column(col)


    def add_row(self, icon, name, new_version, old_version, size):

        if icon is None:
            icon = red_pixbuf.get_pixbuf("empty")

        iter = self.store.append()
        self.store.set(iter, 0, icon, 1, name, 2, old_version, 3, new_version, 4, size)
        self.row += 1

    def add_empty_row(self, sizer=""):
        self.add_row(None, sizer, "", "", "")

    def add_header(self, msg, fg_color=None, bg_color=None):
        cell = gtk.CellRendererText()

        if fg_color:
            t = '<span foreground="%s">%s</span>' % (fg_color, msg)
        else:
            t = '%s' % msg
        cell.set_property("markup", "<b><big>%s</big></b>" % t)

        if not bg_color:
            bg_color = "red"

        bg = self.get_colormap().alloc_color(bg_color)
            
        self.add_spanner_with_background(self.row, 0, -1, cell, bg)
        self.add_empty_row(sizer="<b><big>Ayq</big></b>")

    def add_note(self, msg):
        cell = gtk.CellRendererText()
        # \u2022 is the unicode bullet
        s = u"    <i>\u2022 %s</i>" % escape_markup(msg)
        cell.set_property("markup", s.encode("utf-8"))
        
        self.add_spanner(self.row, 1, -1, cell)
        self.add_empty_row()

    def add_package(self, pkg, is_removal=0):

        ch_icon = rcd_util.get_package_channel_icon(pkg, width=24, height=24)
        name = pkg.get("name", "???")
        if not is_removal:
            new_evr = rcd_util.get_package_EVR(pkg)
            old_evr = "-"
            if pkg.has_key("__old_package"):
                old_evr = rcd_util.get_package_EVR(pkg["__old_package"])
            size = rcd_util.byte_size_to_string(pkg.get("file_size"))
        else:
            new_evr = "-"
            old_evr = rcd_util.get_package_EVR(pkg)
            size = rcd_util.byte_size_to_string(pkg.get("installed_size"))
            

        self.add_row(ch_icon, name, old_evr, new_evr, size)
        
        
    
