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
        self.changed_id = 0

        self.constructed = 0
        self.construct()
        

    def construct(self):
        assert not self.constructed
        self.constructed = 1
        
        self.chanpix_col = gtk.TreeViewColumn("",
                                              gtk.CellRendererPixbuf(),
                                              pixbuf=red_packagearray.COLUMN_CHANNEL_PIXBUF)
        self.append_column(self.chanpix_col)

        
        self.name_col = gtk.TreeViewColumn("Name",
                                           gtk.CellRendererText(),
                                           markup=red_packagearray.COLUMN_NAME)
        self.append_column(self.name_col)
        

        self.evr_col = gtk.TreeViewColumn("Version",
                                           gtk.CellRendererText(),
                                           markup=red_packagearray.COLUMN_EVR)
        self.append_column(self.evr_col)

        rdr = gtk.CellRendererText()
        rdr.set_property("xalign", 1.0)
        self.size_col = gtk.TreeViewColumn("Size",
                                           rdr,
                                           markup=red_packagearray.COLUMN_INSTALLED_SIZE_STRING)
        self.append_column(self.size_col)


    def thrash_model(self):
        # FIXME: we will probably want to do something clever here
        # to keep the selection from getting messed up.
        model = self.get_model()
        gtk.TreeView.set_model(self, None)
        gtk.TreeView.set_model(self, model)

    def set_model(self, model):

        # FIXME: make sure that we are passing in a PackageArray
        # for the model.

        old_model = self.get_model()
        if self.changed_id:
            old_model.disconnect(self.changed_id)
            self.changed_id = 0

        gtk.TreeView.set_model(self, model)

        if model:
            self.changed_id = model.connect_after("changed",
                                                  lambda x:self.thrash_model())
                                            
