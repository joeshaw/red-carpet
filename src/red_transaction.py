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

import gobject

class Transaction(gobject.GObject):

    def __init__(self):

        gobject.GObject.__init__(self)

        self.install_packages = []
        self.uninstall_packages = []

    def add_install_package(self, package):
        self.install_packages.append(package)
        self.emit("changed")

    def remove_install_package(self, package):
        self.install_packages.remove(package)
        self.emit("changed")

    def add_uninstall_package(self, package):
        self.uninstall_packages.append(package)
        self.emit("changed")

    def remove_uninstall_package(self, package):
        self.uninstall_packages.remove(package)
        self.emit("changed")

gobject.type_register(Transaction)

gobject.signal_new("changed",
                   Transaction,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())
