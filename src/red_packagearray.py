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
import red_pendingops

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
    old_pkg = pkg.get("__old_package")
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

def pkg_locked(pkg):
    return pkg["locked"]

__locked_icon = red_pixbuf.get_pixbuf("lock")

def pkg_locked_icon(pkg):
    if pkg["locked"]:
        return __locked_icon
    else:
        return None

def pkg_is_installed(pkg):
    return pkg["installed"]

def pkg_is_name_installed(pkg):
    return pkg["name_installed"] or pkg["installed"]

def pkg_is_upgrade(pkg):
    return pkg["name_installed"] > 0

def pkg_is_downgrade(pkg):
    return pkg["name_installed"] < 0

def pkg_status(pkg):

    pending = red_pendingops.get_action(pkg)
    if pending:
        if pending == red_pendingops.TO_BE_INSTALLED \
           or pending == red_pendingops.TO_BE_INSTALLED_CANCELLED:
            if pkg["name_installed"] > 0:
                str = "to upgrade"
            elif pkg["name_installed"] < 0:
                str = "to <b>downgrade</b>"
            else:
                str = "to install"
            if pending == red_pendingops.TO_BE_INSTALLED_CANCELLED:
                str = "<s>%s</s>" % str
            return str
        
        elif pending == red_pendingops.TO_BE_REMOVED \
             or pending == red_pendingops.TO_BE_REMOVED_CANCELLED:
            str = "to remove"
            if pending == red_pendingops.TO_BE_REMOVED_CANCELLED:
                str = "<s>%s</s>" % str
            return str
        
        else:
            return "?Unknown?"

    if pkg["installed"]:
        return "installed"
    elif pkg["name_installed"] > 0: # upgrade
        return "upgrade"
    elif pkg["name_installed"] < 0:
        return "downgrade"
    else:
        return ""

__to_be_installed_icon     = red_pixbuf.get_pixbuf("to-be-installed")
__to_be_removed_icon       = red_pixbuf.get_pixbuf("to-be-removed")
__to_be_installed_xxx_icon = red_pixbuf.get_pixbuf("to-be-installed-cancelled")
__to_be_removed_xxx_icon   = red_pixbuf.get_pixbuf("to-be-removed-cancelled")
__update_icon              = red_pixbuf.get_pixbuf("update")
__downgrade_icon           = red_pixbuf.get_pixbuf("warning", width=24, height=24)
__installed_icon           = red_pixbuf.get_pixbuf("installed")

def pkg_status_icon(pkg):
    pending = red_pendingops.get_action(pkg)
    if pending:
        if pending == red_pendingops.TO_BE_INSTALLED:
            return __to_be_installed_icon
        elif pending == red_pendingops.TO_BE_REMOVED:
            return __to_be_removed_icon
        elif pending == red_pendingops.TO_BE_INSTALLED_CANCELLED:
            return __to_be_installed_xxx_icon
        elif pending == red_pendingops.TO_BE_REMOVED_CANCELLED:
            return __to_be_removed_xxx_icon
        else:
            return None
    if pkg["installed"]:
        return __installed_icon
    elif pkg["name_installed"] > 0: # upgrade
        return __update_icon
    elif pkg["name_installed"] < 0: # downgrade
        return __downgrade_icon
    return None

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
    ("LOCKED",            pkg_locked,            gobject.TYPE_BOOLEAN),
    ("LOCKED_ICON",       pkg_locked_icon,       gtk.gdk.Pixbuf),
    ("IS_INSTALLED",      pkg_is_installed,      gobject.TYPE_BOOLEAN),
    ("IS_NAME_INSTALLED", pkg_is_name_installed, gobject.TYPE_BOOLEAN),
    ("IS_UPGRADE",        pkg_is_upgrade,        gobject.TYPE_BOOLEAN),
    ("IS_DOWNGRADE",      pkg_is_downgrade,      gobject.TYPE_BOOLEAN),
    ("STATUS",            pkg_status,            gobject.TYPE_STRING),
    ("STATUS_ICON",       pkg_status_icon,       gtk.gdk.Pixbuf),
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

class PackageArray(red_extra.ListModel,
                   red_pendingops.PendingOpsListener):

    def __init__(self):
        gobject.GObject.__init__(self)
        red_pendingops.PendingOpsListener.__init__(self)
        self.__pending_changes = []
        self.__sort_fn = sort_pkgs_by_name
        self.__reverse_sort = 0
        self.__package_keys = {}

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
            self.sort(self.__sort_fn, self.__reverse_sort)

    def do_changed(self):
        operator, args = self.__pending_changes.pop()
        if operator:
            apply(operator, (self,) + args)
            self.request_sort()
            all = self.get_all()
            self.set_list(self.get_all())
            self.__package_keys = {}
            i = 0
            for p in all:
                key = rcd_util.get_package_key(p)
                indices = self.__package_keys.setdefault(key, [])
                indices.append(i)
                i += 1

    def changed(self, operator, *args):
        self.__pending_changes.append((operator, args))
        self.emit("changed")

    def changed_sort_fn(self, sort_fn, reverse=0):
        def set_sort_fn(array, fn, rev):
            array.__sort_fn = fn
            array.__reverse_sort = rev
        if self.__sort_fn != sort_fn or reverse ^ self.__reverse_sort:
            self.changed(set_sort_fn, sort_fn, reverse)

    def changed_sort_by_name(self, reverse=0):
        self.changed_sort_fn(sort_pkgs_by_name, reverse)

    def changed_sort_by_size(self, reverse=0):
        self.changed_sort_fn(sort_pkgs_by_size, reverse)

    def changed_sort_by_importance(self, reverse=0):
        self.changed_sort_fn(sort_pkgs_by_importance, reverse)

    def changed_sort_by_channel(self, reverse=0):
        self.changed_sort_fn(sort_pkgs_by_channel, reverse)

    def do_changed_one(self, i):
        self.row_changed(i)

    def changed_one(self, i):
        if 0 <= i < self.len():
            self.emit("changed_one", i)
        else:
            # FIXME: Should throw a proper exception
            assert 0, "WARNING! Invalid index %d passed to change_one" % i

    ## Find all instances of pkg in the PackageArray, and cause a
    ## 'changed_one' signal to be emitted for each.
    def changed_one_by_package(self, pkg):
        key = rcd_util.get_package_key(pkg)
        indices = self.__package_keys.get(key, [])
        for i in indices:
            self.changed_one(i)

    ## Implements PendingOpsListener
    def pendingops_changed(self, pkg, key, value, old_value):
        self.changed_one_by_package(pkg)

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

gobject.signal_new("changed_one",
                   PackageArray,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_INT,))


###############################################################################


class PackageStore(PackageArray):

    def __init__(self):
        PackageArray.__init__(self)
        self.__store = []

    def sort(self, sort_fn, reverse):
        self.__store.sort(sort_fn)
        if reverse:
            self._store.reverse()

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

    def sort(self, sort_fn, reverse):
        self.__cache.sort(sort_fn)
        if reverse:
            self.__cache.reverse()

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
        self.pending_refresh = 0

    def sort(self, sort_fn, reverse):
        self.__packages.sort(sort_fn)
        if reverse:
            self.__packages.reverse()

    # This is the method that derived classes need to implement
    def get_packages_from_daemon(self, server):
        return []

    def refresh(self):
        packages = self.get_packages_from_daemon(rcd_util.get_server())
        def set_pkg_cb(me, p):
            me.__packages = p
        self.changed(set_pkg_cb, packages)
        self.pending_refresh = 0

    def schedule_refresh(self):
        if self.pending_refresh == 0:
            self.pending_refresh = gtk.timeout_add(20,
                                                   lambda s: s.refresh(),
                                                   self)

    def packages_changed(self, server):
        self.schedule_refresh()

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
        self.schedule_refresh()


###############################################################################


class UpdatedPackages(PackagesFromDaemon):

    def __init__(self):
        PackagesFromDaemon.__init__(self)
        self.refresh()

    def get_packages_from_daemon(self, server):
        packages = []
        for old_pkg, pkg, history in server.rcd.packsys.get_updates():
            pkg["__old_package"] = old_pkg
            pkg["__history"] = history
            packages.append(pkg)

        return packages

    # The list of updates needs to refresh when the list of available
    # channels or subscriptions change.
    def subscriptions_changed(self, server):
        self.schedule_refresh()

    def channels_changed(self, server):
        self.schedule_refresh()


