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

import gobject
import red_extra
from red_gettext import _

###
### ListModel: our magic-laden base class
###

COL_NAME     = 0
COL_VALUE_FN = 1
COL_SORT_FN  = 2
COL_TYPE     = 3

class ListModel(red_extra.ListModel):

    def __init__(self, sort_fn=None, filter_fn=None):
        gobject.GObject.__init__(self)

        self.__busy_flag = 0
        self.__pending_changes = []
        self.__sort_fn = sort_fn
        self.__filter_fn = filter_fn
        self.__reverse_sort = 0

        self.__sort_cols = {}
        self.__sorted_by = None

    def do_changed(self):
        operator, args = self.__pending_changes.pop()
        if operator:
            apply(operator, (self,) + args)

            self.set_list(self.get_all())
            self.set_sort_magic(self.__sort_fn, self.__reverse_sort)
            self.set_filter_magic(self.__filter_fn)

        return (operator, args)

    def changed(self, operator, *args):
        self.__pending_changes.append((operator, args))
        self.emit("changed")

    def changed_filter_fn(self, filter_fn):
        def set_filter_fn(model, fn):
            model.__filter_fn = fn
        if self.__filter_fn != filter_fn:
            self.changed(set_filter_fn, filter_fn)

    def add_columns(self, columns_array):
        for i in range(len(columns_array)):
            col = columns_array[i]
            self.add_column(col[COL_VALUE_FN], col[COL_TYPE])

            self.__sort_cols[col[COL_NAME]] = col[COL_SORT_FN]

    def can_sort(self, column):
        if self.__sort_cols.has_key(column):
            return self.__sort_cols[column]

    def sort(self, column, reverse=0):
        if not self.can_sort(column):
            return

        def set_sort_fn(model, fn, rev):
            model.__sort_fn = fn
            model.__reverse_sort = rev

        # FIXME: We should just reverse our list if possible
        if self.__sorted_by != column or self.__reverse_sort ^ reverse:
            self.changed(set_sort_fn, self.__sort_cols[column], reverse)
            self.__sorted_by = column

    def do_changed_one(self, i):
        self.row_changed(i)

    def changed_one(self, i):
        if 0 <= i < self.len():
            self.emit("changed_one", i)
        else:
            # FIXME: Should throw a proper exception
            assert 0, "WARNING! Invalid index %d passed to change_one" % i

    ## Fallback implementation
    def len(self):
        all = self.get_all()
        return len(all)

    ## Fallback implementation
    def get(self, i):
        all = self.get_all()
        return all[i]

    def get_all(self):
        print "ListModel.get_all not defined"
        assert 0

        ## Busy/message functions

    def message_push(self, msg, context_id=-1, transient=0):
        if transient:
            context_id = 0
        elif context_id < 0:
            context_id = hash(self)
        self.emit("message_push", msg, context_id)

    def message_pop(self, context_id=-1):
        if context_id < 0:
            context_id = hash(self)
        self.emit("message_pop", context_id)

    def busy(self, flag):
        if self.__busy_flag ^ flag:
            self.__busy_flag = flag
            self.emit("busy", flag)


gobject.type_register(ListModel)

gobject.signal_new("changed",
                   ListModel,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())

gobject.signal_new("changed_one",
                   ListModel,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_INT,))

gobject.signal_new("busy",
                   ListModel,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_BOOLEAN,))

gobject.signal_new("message_push",
                   ListModel,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING, gobject.TYPE_UINT))

gobject.signal_new("message_pop",
                   ListModel,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_UINT,))
