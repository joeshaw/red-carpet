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

import red_packagearray

class Transaction(red_packagearray.PackageArray):

    def __init__(self):

        red_packagearray.PackageArray.__init__(self)

        self.install_packages = []
        self.uninstall_packages = []

    def get_all(self):
        return self.install_packages + self.uninstall_packages

    def append_op(self, self2, pl, p):
        pl.append(p)

    def remove_op(self, self2, pl, p):
        pl.remove(p)

    def add_install_package(self, package):
        self.changed(self.append_op,
                     self.install_packages, package)

    def remove_install_package(self, package):
        self.changed(self.remove_op,
                     self.install_packages, package)

    def add_uninstall_package(self, package):
        self.changed(self.append_op,
                     self.uninstall_packages, package)

    def remove_uninstall_package(self, package):
        self.changed(self.remove_op,
                     self.uninstall_packages, package)
