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

import gobject, gtk
import red_listmodel

class TreeView(gtk.TreeView):

    def __init__(self, model=None):
        gobject.GObject.__init__(self)

        gtk.TreeView.set_model(self, model)
        
        self.__pre_changed_id = 0
        self.__post_changed_id = 0

        if model:
            assert isinstance(model, red_listmodel.ListModel)
            self.__pre_changed_id = model.connect("changed",
                                                  lambda x:self.pre_thrash_model())

            self.__post_changed_id = model.connect_after("changed",
                                                         lambda x:self.post_thrash_model())

    def set_model(self, model):
        old_model = self.get_model()
        if self.__pre_changed_id:
            old_model.disconnect(self.__pre_changed_id)
        if self.__post_changed_id:
            old_model.disconnect(self.__post_changed_id)

        self.__pre_changed_id = 0
        self.__post_changed_id = 0

        def no_op(model):
            pass
        model.changed(no_op)

        gtk.TreeView.set_model(self, model)

        if model:
            self.__pre_changed_id = model.connect("changed",
                                                  lambda x:self.pre_thrash_model())

            self.__post_changed_id = model.connect_after("changed",
                                                         lambda x:self.post_thrash_model())
        
    def pre_thrash_model(self):
        model = self.get_model()
        selpath = None
        if model:
            select = self.get_selection()
            m, iter = select.get_selected()
            if iter:
                selpath = m.get_path(iter)
        self.saved_selpath = selpath
        self.saved_model = model
        gtk.TreeView.set_model(self, None)

    def post_thrash_model(self):
        selpath = self.saved_selpath
        model = self.saved_model
        gtk.TreeView.set_model(self, model)
        if selpath:
            try:
                iter = model.get_iter(selpath)
            except ValueError:
                # If there's nothing left in the tree, we'll get a
                # ValueError when we try to get an iter from the
                # (now invalid) path.
                iter = None
                
            if iter:
                select = self.get_selection()
                select.select_iter(iter)

    def thrash_model(self):
        self.pre_thrash_model()
        self.post_thrash_model()
