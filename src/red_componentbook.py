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
import red_pixbuf, red_component
from red_gettext import _

class ComponentPage(red_component.ComponentListener):

    def __init__(self, comp, parent_book):
        red_component.ComponentListener.__init__(self)
        self.set_component(comp)
        self.__component = comp
        self.__parent_book = parent_book
        self.__displayed = None
        self.__box = gtk.HBox(0, 0)
        self.__box.set_border_width(6)

    def build_page_label(self):
        img = None
        if self.__component.stock():
            img = gtk.Image()
            img.set_from_stock(self.__component.stock(),
                               gtk.ICON_SIZE_SMALL_TOOLBAR)
        elif self.__component.pixbuf():
            img = red_pixbuf.get_widget(self.__component.pixbuf(),
                                        width=16, height=16)

        label = gtk.Label(self.__component.name())

        if img:
            box = gtk.HBox(0, 0)
            box.pack_start(img, expand=0, fill=0, padding=2)
            box.pack_start(label, expand=1, fill=1)
            return box
        
        return label

    def get_page_widget(self):
        return self.__box

    def page_show(self):
        self.__component.visible(1)
        self.__component.activated()
        self.__component.pull_widget()

    def page_hide(self):
        self.__component.visible(0)
        self.__component.deactivated()

    def do_component_display(self, w):
        # Clean any old widgets out of self.container,
        # then stick in our new widget and show it.
        if self.__displayed is w:
            return
        self.__displayed = w
        for c in self.__box.get_children():
            self.__box.remove(c)
        self.__box.add(w)
        w.show()

    def do_component_packages_selected(self, pkgs):
        self.__parent_book.emit("packages_selected",
                                self.__component,
                                pkgs)


class ComponentBook(gtk.HBox):

    def __init__(self):
        gobject.GObject.__init__(self)
        self.__book = gtk.Notebook()
        self.__pages = []
        self.__comp_pagenum = {}
        self.__visible_page = -1
        def switch_page_cb(nb, page, num):
            self.switch_page(page, num)
            comp = self.__pages[num].get_component()
            self.emit("switched", comp)
            
        self.__book.connect("switch-page", switch_page_cb)
        self.__pushed_comp = None

        self.add(self.__book)
        self.__book.show()

    def switch_page(self, page, num):
        if self.__visible_page >= 0:
            self.__pages[self.__visible_page].page_hide()
        self.__pages[num].page_show()
        self.__visible_page = num

    def add_component(self, comp):
        page = ComponentPage(comp, self)
        self.__comp_pagenum[comp] = len(self.__pages)
        self.__pages.append(page)

        label = page.build_page_label()
        label.show_all()
        
        w = page.get_page_widget()
        w.show()
        self.__book.append_page(w, label)

    def push_component(self, comp):
        assert self.__pushed_comp is None
        self.__pushed_comp = comp
        for c in self.get_children():
            self.remove(c)
        def display_cb(comp, w):
            for c in self.get_children():
                self.remove(c)
            self.add(w)
            w.show_all()
        self.__id = comp.connect("display", display_cb)
        comp.pull_widget()
        self.emit("switched", comp)

    def pop_component(self):
        assert self.__pushed_comp is not None
        self.__pushed_comp = None
        for c in self.get_children():
            self.remove(c)
        self.add(self.__book)
        comp = self.get_visible_component()
        self.emit("switched", comp)

    def view_component(self, comp):
        num = self.__comp_pagenum.get(comp, -1)
        if num >= 0:
            if self.__pushed_comp:
                self.pop_component()
            self.__book.set_current_page(num)

    def get_visible_component(self):
        if self.__pushed_comp:
            return self.__pushed_comp
        if self.__visible_page >= 0:
            return self.__pages[self.__visible_page].get_component()
        return None


gobject.type_register(ComponentBook)

gobject.signal_new("switched",
                   ComponentBook,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,))

gobject.signal_new("packages_selected",
                   ComponentBook,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_PYOBJECT,    # component
                    gobject.TYPE_PYOBJECT, )) # list of packages
