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
import red_packagearray

class PackageView(gtk.TreeView):

    def __init__(self):
        gtk.TreeView.__init__(self)
        self.__changed_id = 0
        self.set_rules_hint(1)

    def thrash_model(self):
        model = self.get_model()
        gtk.TreeView.set_model(self, None)
        gtk.TreeView.set_model(self, model)

    def set_model(self, model):
        assert isinstance(model, red_packagearray.PackageArray)
        old_model = self.get_model()
        if self.__changed_id:
            old_model.disconnect(self.__changed_id)
        self.__changed_id = 0

        gtk.TreeView.set_model(self, model)
        
        if model:
            #self.set_headers_clickable(1)
            self.__changed_id = model.connect_after("changed",
                                                    lambda x:self.thrash_model())

    def append_channel_column(self,
                              column_title="Channel"):
        col = gtk.TreeViewColumn()
        col.set_title(column_title)

        render_icon = gtk.CellRendererPixbuf()
        col.pack_start(render_icon, 0)
        col.set_attributes(render_icon,
                           pixbuf=red_packagearray.COLUMN_CH_ICON)

        render_text = gtk.CellRendererText()
        col.pack_start(render_text, 1)
        col.set_attributes(render_text,
                           text=red_packagearray.COLUMN_CH_NAME)

        def clicked_cb(foo, view):
            array = view.get_model()
            if array:
                array.changed_sort_by_channel()
        col.connect("clicked", clicked_cb, self)
        col.set_clickable(1)

        self.append_column(col)

        return col

    def append_name_column(self,
                           column_title="Package",
                           show_channel_icon=0,
                           show_section_icon=0):
        col = gtk.TreeViewColumn()
        col.set_title(column_title)

        if show_channel_icon:
            render_icon = gtk.CellRendererPixbuf()
            col.pack_start(render_icon, 0)
            col.set_attributes(render_icon,
                               pixbuf=red_packagearray.COLUMN_CH_ICON)

        if show_section_icon:
            render_icon = gtk.CellRendererPixbuf()
            col.pack_start(render_icon, 0)
            col.set_attributes(render_icon,
                               pixbuf=red_packagearray.COLUMN_SEC_ICON)

        render_text = gtk.CellRendererText()
        col.pack_start(render_text, 1)
        col.set_attributes(render_text, text=red_packagearray.COLUMN_NAME)

        def clicked_cb(foo, view):
            array = view.get_model()
            if array:
                array.changed_sort_by_name()
        col.connect("clicked", clicked_cb, self)
        col.set_clickable(1)

        self.append_column(col)
        return col

    def append_version_column(self, column_title="Version"):
        col = gtk.TreeViewColumn(column_title,
                                 gtk.CellRendererText(),
                                 text=red_packagearray.COLUMN_EVR)
        self.append_column(col)
        return col

    def append_current_version_column(self, column_title="Current Version"):
        col = gtk.TreeViewColumn(column_title,
                                 gtk.CellRendererText(),
                                 text=red_packagearray.COLUMN_OLD_EVR)
        self.append_column(col)
        return col

    def append_importance_column(self, column_title="Importance"):
        col = gtk.TreeViewColumn(column_title,
                                 gtk.CellRendererText(),
                                 text=red_packagearray.COLUMN_IMPORTANCE)

        def clicked_cb(foo, view):
            array = view.get_model()
            if array:
                array.changed_sort_by_importance()
        col.connect("clicked", clicked_cb, self)
        col.set_clickable(1)
        
        self.append_column(col)
        return col
        
    def append_size_column(self, column_title="Size"):
        col = gtk.TreeViewColumn(column_title,
                                 gtk.CellRendererText(),
                                 text=red_packagearray.COLUMN_SIZE)

        def clicked_cb(foo, view):
            array = view.get_model()
            if array:
                array.changed_sort_by_size()
        col.connect("clicked", clicked_cb, self)
        col.set_clickable(1)

        self.append_column(col)
        return col
        

        

