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

import gtk
import rcd_util
import red_packagepage
import red_packagepage_deps
import red_packagepage_info
from red_gettext import _

package_infos = {}

def show_package_info(pkg, parent=None):

    key = rcd_util.get_package_key(pkg)
    if package_infos.has_key(key):
        dialog = package_infos[key]
        dialog.present()
        return

    book = PackageBook()
    book.set_tab_pos(gtk.POS_TOP)
    book.add_page(red_packagepage_info.PackagePage_Info())
    book.add_page(red_packagepage.PackagePage_History())
    book.add_page(red_packagepage_deps.PackagePage_Deps())

    book.set_package(pkg)

    title = _("Package Information") + ": " + pkg["name"]
    dialog = gtk.Dialog(title, parent=parent)
    dialog.set_default_size(450, 350)
    button = dialog.add_button(gtk.STOCK_OK, 0)
    # grab_default() is not sufficient here.
    button.grab_focus()
    dialog.vbox.add(book)
    dialog.connect("response", lambda d, code: d.destroy())

    def destroy_cb(dialog, key):
        del package_infos[key]

    package_infos[key] = dialog
    dialog.connect("destroy", destroy_cb, key)

    book.show_all()
    dialog.show_all()


class PackageBook(gtk.Notebook):

    def switch_page_cb(self, page, num):
        page_box = self.get_nth_page(num)
        if not page_box.initialized and not self.block_builds:
            server = rcd_util.get_server()
            contents = page_box.page.build_widget(self.package,
                                                  rcd_util.get_server())
            page_box.add(contents)
            #print "Built page %d: '%s'" % (num, page_box.page.name())
            contents.show()
            page_box.initialized = 1

    def __init__(self):
        gtk.Notebook.__init__(self)
        self.pages = []
        self.package = None
        self.block_builds = 0

        self.connect("switch-page", PackageBook.switch_page_cb)

    def add_page(self, page):
        self.pages.append(page)

    def build_pages(self):

        # If a page is currently set, remember it.
        current_page = None
        n = self.get_current_page()
        if n >= 0:
            page_box = self.get_nth_page(n)
            current_page = page_box.page
            
        # We don't want to build page widgets if pages become visible
        # as other pages are removed.
        self.block_builds = 1
        for c in self.get_children():
            self.remove(c)
            c.destroy()
        self.block_builds = 0

        page_count = 0
        for page in self.pages:
            if page.visible(self.package):
                name = page.name()
                page_box  = gtk.EventBox()
                page_box.page = page
                page_box.initialized = 0
                style = page_box.get_style().copy()
                color = page_box.get_colormap().alloc_color("white")
                style.bg[gtk.STATE_NORMAL] = color
                page_box.set_style(style)
                self.append_page(page_box, gtk.Label(name))
                page_box.show()
                # If this is the page that was being displayed before,
                # make it the current page.
                if page == current_page:
                    self.set_current_page(page_count)
                page_count += 1

        # If no page was set previously, go to the first page.
        if current_page is None:
            self.set_current_page(0)


    def set_package(self, package):
        self.package = package
        self.build_pages()
        


