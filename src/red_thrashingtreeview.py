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
        self.saved_cursor_column = 0
        self.saved_cursor_item = None
        
        model = self.get_model()
        selected_items = []
        
        if model:
            def add_path(model, path, iter, list):
                if iter:
                    list.append(model.get_list_item(path[0]))

            select = self.get_selection()
            select.selected_foreach(add_path, selected_items)

            cursor_path, self.saved_cursor_column = self.get_cursor()
            if cursor_path:
                self.saved_cursor_item = model.get_list_item(cursor_path[0])
 
        self.saved_items = selected_items
        self.saved_model = model
        
        gtk.TreeView.set_model(self, None)

    def post_thrash_model(self):
        selected_items = self.saved_items

        model = self.saved_model
        gtk.TreeView.set_model(self, model)

        select = self.get_selection()

        if model:
            # We want (as many of) the same items to be selected even if
            # we sort it differently.  We have to make two passes since
            # setting the cursor after the selection seems to break some
            # of the time.

            def set_cursor_cb(model, path, iter, (view, curitem)):
                model_item = model.get_list_item(path[0])

                if model_item == curitem:
                    view.set_cursor(path, view.saved_cursor_column)

            model.foreach(set_cursor_cb, (self, self.saved_cursor_item))

            def set_selection_cb(model, path, iter, (select, selitems)):
                model_item = model.get_list_item(path[0])

                if model_item in selitems:
                    select.select_iter(iter)

            model.foreach(set_selection_cb, (select, selected_items))

        self.columns_autosize()

    def thrash_model(self):
        self.pre_thrash_model()
        self.post_thrash_model()

    def add_column(self, column,
                   sort_id=None,
                   title=None,
                   widget=None,
                   initially_visible=0,
                   resizable=1):

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

        if resizable:
            column.set_resizable(1)

        column.set_visible(initially_visible)
        self.append_column(column)

        model = self.get_model()
        if sort_id and model.can_sort(sort_id):
            column.data_id = sort_id
            column.connect("clicked", lambda x,y,z:y.sort_by(z), self, sort_id)
            column.set_clickable(1)

    def get_column_by_sort_id(self, sort_id):
        info = self.__column_info
        for key in info.keys():
            if info[key].get("sort_id") == sort_id and \
               key.get_visible():
                return key

    def sort_by(self, sort_id):
        column = self.get_column_by_sort_id(sort_id)
        if not column:
            return

        reverse = 0
        if self.__sorted_by == column:
            reverse = not self.__reverse_sort
        else:
            if self.__sorted_by:
                # Fix the old column header
                self.__sorted_by.set_sort_indicator(0)
            column.set_sort_indicator(1)

        if reverse:
            order = gtk.SORT_DESCENDING
        else:
            order = gtk.SORT_ASCENDING
        column.set_sort_order(order)

        model = self.get_model()
        model.sort(sort_id, reverse)

        self.__sorted_by = column
        self.__reverse_sort = reverse
