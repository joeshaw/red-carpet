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

import sys
import gtk
import rcd_util

class PackagePage:

    def __init__(self):
        pass

    # Define me!
    def name(self):
        return "Unnamed"

    # Define me!
    def visible(self, pkg):
        return 1

    def build_widget(self, pkg, server):
        return gtk.Label("PackagePage.build_widget not implemented")

class PageSummary(PackagePage):

    def name(self):
        return "Summary"

    def visible(self, pkg):
        return pkg

    def build_widget(self, pkg, server):
        box = gtk.VBox(0,0)
        box.pack_start(gtk.Label(pkg["name"]))
        box.show_all()
        return box

class PageHistory(PackagePage):

    def name(self):
        return "History"

    def visible(self, pkg):
        return pkg and pkg.has_key("history")

    def build_widget(self, pkg, server):
        box = gtk.VBox(0, 0)
        for msg in pkg["history"]:
            box.pack_start(gtk.Label(msg), 0, 0, 2)
        box.show_all()
        return box

class PackageBook(gtk.Notebook):

    def switch_page_cb(self, page, num):
        page_box = self.get_nth_page(num)
        if not page_box.initialized and not self.block_builds:
            server = rcd_util.get_server()
            contents = page_box.page.build_widget(self.package,
                                                  rcd_util.get_server())
            page_box.add(contents)
            print "Built page %d: '%s'" % (num, page_box.page.name())
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
                page_box  = gtk.Frame()
                page_box.page = page
                page_box.initialized = 0
                self.append_page(page_box, gtk.Label(name))
                page_box.show()
                # If this is the page that was being displayed before,
                # make it the current page.
                if page == current_page:
                    self.set_current_page(page_count)
                page_count += 1

    def set_package(self, package):
        self.package = package
        self.build_pages()
        


