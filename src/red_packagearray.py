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

import sys, string, time
import gobject, gtk
import rcd_util
import red_extra
import red_serverlistener, red_pixbuf

###
### Callbacks for our ListModel
###

def pkg(pkg):
    return pkg

def pkg_name(pkg):
    return pkg["name"]

def pkg_EVR(pkg):
    return rcd_util.get_package_EVR(pkg)

def pkg_old_EVR(pkg):
    old_pkg = pkg.get("old_package")
    if old_pkg:
        return rcd_util.get_package_EVR(old_pkg)
    return ""

def pkg_size(pkg):
    return rcd_util.byte_size_to_string(pkg["file_size"])

def pkg_ch_name(pkg):
    return rcd_util.get_package_channel_name(pkg)

def pkg_ch_icon(pkg):
    return rcd_util.get_package_channel_icon(pkg, width=24, height=24)

def pkg_sec_name(pkg):
    return pkg["section_user_str"]

def pkg_sec_icon(pkg):
    pixbuf_name = "section-" + pkg["section_str"]
    return red_pixbuf.get_pixbuf(pixbuf_name, width=16, height=16)

def pkg_importance(pkg):
    return pkg.get("importance_str", "")

def pkg_is_installed(pkg):
    return pkg["installed"]

def pkg_is_name_installed(pkg):
    return pkg["name_installed"]

def pkg_is_upgrade(pkg):
    return pkg["name_installed"] > 0

def pkg_is_downgrade(pkg):
    return pkg["name_installed"] < 0

COLUMNS = (
    ("PKG",               pkg,                   gobject.TYPE_PYOBJECT),
    ("NAME",              pkg_name,              gobject.TYPE_STRING),
    ("EVR",               pkg_EVR,               gobject.TYPE_STRING),
    ("OLD_EVR",           pkg_old_EVR,           gobject.TYPE_STRING),
    ("SIZE",              pkg_size,              gobject.TYPE_STRING),
    ("CH_NAME",           pkg_ch_name,           gobject.TYPE_STRING),
    ("CH_ICON",           pkg_ch_icon,           gtk.gdk.Pixbuf),
    ("SEC_NAME",          pkg_sec_name,          gobject.TYPE_STRING),
    ("SEC_ICON",          pkg_sec_icon,          gtk.gdk.Pixbuf),
    ("IMPORTANCE",        pkg_importance,        gobject.TYPE_STRING),
    ("IS_INSTALLED",      pkg_is_installed,      gobject.TYPE_BOOLEAN),
    ("IS_NAME_INSTALLED", pkg_is_name_installed, gobject.TYPE_BOOLEAN),
    ("IS_UPGRADE",        pkg_is_upgrade,        gobject.TYPE_BOOLEAN),
    ("IS_DOWNGRADE",      pkg_is_downgrade,      gobject.TYPE_BOOLEAN),
    )

for i in range(len(COLUMNS)):
    name = COLUMNS[i][0]
    exec("COLUMN_%s = %d" % (name, i))


###
### Sort functions
###

def sort_pkgs_by_name(a, b):
    return cmp(string.lower(a["name"]), string.lower(b["name"]))

def sort_pkgs_by_size(a, b):
    return cmp(a["file_size"], b["file_size"])

def sort_pkgs_by_importance(a, b):
    return cmp(a["importance_num"], b["importance_num"])

def sort_pkgs_by_channel(a, b):
    return cmp(rcd_util.get_package_channel_name(a),
               rcd_util.get_package_channel_name(b))


###
### PackageArray: our magic-laden base class
###

class PackageArray(red_extra.ListModel):

    def __init__(self):
        gobject.GObject.__init__(self)
        self.__pending_changes = []
        self.__sort_fn = sort_pkgs_by_name

        for name, callback, type in COLUMNS:
            self.add_column(callback, type)

    ## This function should take the data in the array and sort it according
    ## to the specified function.  This is a "protected" function and
    ## shouldn't be called by users of PackageArrays.
    def sort(self, sort_fn):
        assert 0, "PackageArray.sort not defined"

    ## You shouldn't need to ever call this.
    def request_sort(self):
        if self.__sort_fn:
            t1 = time.time()
            self.sort(self.__sort_fn)
            t2 = time.time()

    def do_changed(self):
        operator, args = self.__pending_changes.pop()
        if operator:
            apply(operator, (self,) + args)
            self.request_sort()
            self.set_list(self.get_all())

    def changed(self, operator, *args):
        self.__pending_changes.append((operator, args))
        self.emit("changed")

    def changed_sort_fn(self, sort_fn):
        def set_sort_fn(array, fn):
            array.__sort_fn = fn
        if self.__sort_fn != sort_fn:
            self.changed(set_sort_fn, sort_fn)

    def changed_sort_by_name(self):
        self.changed_sort_fn(sort_pkgs_by_name)

    def changed_sort_by_size(self):
        self.changed_sort_fn(sort_pkgs_by_size)

    def changed_sort_by_importance(self):
        self.changed_sort_fn(sort_pkgs_by_importance)

    def changed_sort_by_channel(self):
        self.changed_sort_fn(sort_pkgs_by_channel)

    ## Fallback implementation
    def len(self):
        all = self.get_all()
        return len(all)

    ## Fallback implementation
    def get(self, i):
        all = self.get_all()
        return all[i]

    def get_all(self):
        print "PackageArray.get_all not defined"
        assert 0

    def spew(self):
        for pkg in self.get_all():
            print pkg["name"]


gobject.type_register(PackageArray)

gobject.signal_new("changed",
                   PackageArray,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   ())


###############################################################################


class PackageStore(PackageArray):

    def __init__(self):
        PackageArray.__init__(self)
        self.__store = []

    def sort(self, sort_fn):
        self.__store.sort(sort_fn)

    def get_all(self):
        return self.__store

    def clear(self):
        def clear_op(x):
            x.__store = []
        self.changed(clear_op)

    def set(self, pkg_list):
        def set_op(x, pl):
            x.__store = pl
        self.changed(set_op, pkg_list)

    def add(self, pkg):
        def add_op(x, p):
            x.__store.append(p)
        self.changed(add_op, pkg)

    def remove(self, pkg):
        def remove_op(x, i):
            del x.__store[i]
        self.changed(remove_op, 0)

        
###############################################################################


class FilteredPackageArray(PackageArray):

    def __init__(self, target=None, filter=None):
        PackageArray.__init__(self)
        self.__ch_id = 0
        self.__cache = []
        self.__filter = filter
        if target:
            self.set_target(target)

    def sort(self, sort_fn):
        self.__cache.sort(sort_fn)

    def fpa_changed_cb(self):
        self.__cache = []
        if not self.__target:
            return
        if self.__filter:
            for pkg in self.__target.get_all():
                if self.__filter(pkg):
                    self.__cache.append(pkg)
        else:
            self.__cache = self.__target.get_all()

    def set_target(self, target):
        if self.__ch_id:
            self.__target.disconnect(self.__ch_id)
        self.__ch_id = 0

        self.__target = target

        def target_changed_cb(target, us):
            self.changed(lambda x:x.fpa_changed_cb())            
            
        if self.__target:
            self.__ch_id = self.__target.connect_after("changed",
                                                       target_changed_cb,
                                                       self)
        self.changed(lambda x:x.fpa_changed_cb())

    def set_filter(self, filter):
        self.__filter = filter
        self.changed(lambda x:x.fpa_changed_cb())

    def len(self):
        return len(self.__cache)

    def get(self, i):
        assert 0 <= i < self.len()
        return self.__cache[i]

    def get_all(self):
        return self.__cache


###############################################################################


class PackagesFromDaemon(PackageArray, red_serverlistener.ServerListener):

    def __init__(self):
        PackageArray.__init__(self)
        red_serverlistener.ServerListener.__init__(self)

        self.__packages = []

    def sort(self, sort_fn):
        self.__packages.sort(sort_fn)

    # This is the method that derived classes need to implement
    def get_packages_from_daemon(self, server):
        return []

    def server_changed(self, server):

        packages = self.get_packages_from_daemon(server)

        def set_pkg_cb(array, p):
            array.__packages = p
        self.changed(set_pkg_cb, packages)

    def sync_with_daemon(self):
        self.server_changed(rcd_util.get_server())

    def len(self):
        return len(self.__packages)

    def get(self, i):
        assert 0 <= i < self.len()
        return self.__packages[i]

    def get_all(self):
        return self.__packages


###############################################################################


class PackagesFromQuery(PackagesFromDaemon):

    def __init__(self, query=None):
        PackagesFromDaemon.__init__(self)
        self.set_query(query)

    def get_packages_from_daemon(self, server):

        if not self.query:
            return []

        print "query:", self.query
        import time
        start = time.time()
        packages = server.rcd.packsys.search(self.query)
        end = time.time()
        print "time=%.2f" % (end - start)
        print "got %d packages (%.2f pkgs/sec)" \
              % (len(packages), len(packages)/(end-start))

        return packages
        
    def set_query(self, query):
        self.query = query
        self.sync_with_daemon()


###############################################################################


class UpdatedPackages(PackagesFromDaemon):

    def __init__(self):
        PackagesFromDaemon.__init__(self)
        self.sync_with_daemon()

    def get_packages_from_daemon(self, server):

        packages = []
        for old_pkg, pkg, history in server.rcd.packsys.get_updates():
            pkg["old_package"] = old_pkg
            pkg["history"] = history
            packages.append(pkg)

        return packages

