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

import gtk

import red_packagearray
import red_history

class PackagePage:

    def __init__(self):
        pass

    # Define me!
    def name(self):
        return "Unnamed"

    # Define me!
    def visible(self, pkg):
        return 1

    # Define me!
    def build_widget(self, pkg, server):
        return gtk.Label("PackagePage.build_widget not implemented")

class PackagePage_History(PackagePage):

    def name(self):
        return "History"

    def visible(self, pkg):
        return pkg and red_packagearray.pkg_name(pkg)

    def build_widget(self, pkg, server):
        pkg_name = red_packagearray.pkg_name(pkg)
        if pkg_name:
            return red_history.PackageHistory(pkg_name)

