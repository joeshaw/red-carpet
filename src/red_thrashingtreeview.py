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

from red_gettext import _

class TreeView(gtk.TreeView):

    def __init__(self, model=None):
        gobject.GObject.__init__(self)

        gtk.TreeView.set_model(self, model)
        
        self.__pre_changed_id = 0
        self.__post_changed_id = 0

        self.__column_info = {}
        self.__column_order = []
        self.__sorted_by = None
        self.__reverse_sort = 0
        self.__activated_fn = None

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
        self.saved_curpath, self.saved_column = self.get_cursor()
        
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

        if self.saved_curpath:
            self.set_cursor(self.saved_curpath, self.saved_column)

    def thrash_model(self):
        self.pre_thrash_model()
        self.post_thrash_model()

    def add_column(self, column,
                   sort_id=None,
                   title=None,
                   widget=None,
                   initially_visible=0):

        if not title and not widget:
            title = _("Untitled")

        self.__column_info[column] = { "title":title,
                                       "widget":widget,
                                       "visible":initially_visible,
                                       "sort_id":sort_id,
                                     }

        self.__column_order.append(column)

        if title:
            column.set_title(title)
            column.set_alignment(0.0)
            
        if widget:
            column.set_widget(widget)
            column.set_alignment(0.5)

        column.set_visible(initially_visible)
        self.append_column(column)

        def sort_cb(sort_id, view):
            if view.__sorted_by == column:
                view.sort_by(sort_id, not self.__reverse_sort)
            else:
                view.sort_by(sort_id, 0)

        model = self.get_model()
        if sort_id and model.can_sort(sort_id):
            column.data_id = sort_id
            column.connect("clicked", lambda x,c,v:sort_cb(c,v), sort_id, self)
            column.set_clickable(1)

    def get_column_by_sort_id(self, sort_id):
        info = self.__column_info
        for key in info.keys():
            if info[key].get("sort_id") == sort_id:
                return key

    def sort_by(self, sort_id, reverse=0):
        column = self.get_column_by_sort_id(sort_id)
        if not column:
            return

        if self.__sorted_by == column and not reverse ^ self.__reverse_sort:
            return

        # Fix the old column header
        if self.__sorted_by:
            self.__sorted_by.set_sort_indicator(0)

        model = self.get_model()
        if model.can_sort(sort_id):
            model.sort(sort_id, reverse)

        column.set_sort_indicator(1)
        if reverse:
            order = gtk.SORT_DESCENDING
        else:
            order = gtk.SORT_ASCENDING
        column.set_sort_order(order)

        self.__sorted_by = column
        self.__reverse_sort = reverse
