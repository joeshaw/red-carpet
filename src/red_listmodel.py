###
### Copyright 2002-2003 Ximian, Inc.
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
import red_extra

###
### ListModel: our magic-laden base class
###

class ListModel(red_extra.ListModel):

    def __init__(self, sort_fn=None, filter_fn=None):
        gobject.GObject.__init__(self)
        self.__pending_changes = []
        self.__sort_fn = sort_fn
        self.__filter_fn = filter_fn
        self.__reverse_sort = 0

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

    def changed_sort_fn(self, sort_fn, reverse=0):
        def set_sort_fn(model, fn, rev):
            model.__sort_fn = fn
            model.__reverse_sort = rev
        if self.__sort_fn != sort_fn or reverse ^ self.__reverse_sort:
            self.changed(set_sort_fn, sort_fn, reverse)

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
