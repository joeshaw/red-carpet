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

import sys, string
import gobject, gtk
import rcd_util
import red_serverlistener

# FIXME: This sorting function should be smarter, and should
# sort lists into some sort of canonical form that will
# make it inexpensive to figure out if two sorted lists of packages
# are the same.
def pkg_cmp(a,b):
    return cmp(string.lower(a["name"]), string.lower(b["name"]))


class PackageArray(gobject.GObject):

    def __init__(self):
        gobject.GObject.__init__(self)
        self.pending_changes = []

    def do_changed(self):
        operator, args = self.pending_changes.pop()
        if operator:
            apply(operator, (self,) + args)

    def changed(self, operator, *args):
        self.pending_changes.append((operator, args))
        self.emit("changed")

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
        self.store = []

    def get_all(self):
        return self.store

    def clear(self):
        def clear_op(x):
            x.store = []
        self.changed(clear_op)

    def set(self, pkg_list):
        def set_op(x, pl):
            x.store = pl
        self.changed(set_op, pkg_list)

    def add(self, pkg):
        def add_op(x, p):
            x.store.append(p)
        self.changed(add_op, pkg)

    def remove(self, pkg):
        def remove_op(x, i):
            del x.store[i]
        self.changed(remove_op, 0)

        
###############################################################################


class FilteredPackageArray(PackageArray):

    def __init__(self, target=None, filter=None):
        PackageArray.__init__(self)
        self.cache_dirty = 1
        self.ch_id = 0
        self.cache = []
        self.filter = filter
        if target:
            self.set_target(target)

    def fpa_changed_cb(self):
        # We don't need to do anything else, since our cache will
        # get filled the first time we try to look at it.
        self.cache_dirty = 1


    def set_target(self, target):
        if self.ch_id:
            self.target.disconnect(self.ch_id)
        self.ch_id = 0

        self.target = target

        def target_changed_cb(target, us):
            self.changed(lambda x:x.fpa_changed_cb())            
            
        if self.target:
            self.ch_id = self.target.connect("changed",
                                             target_changed_cb,
                                             self)

        self.cache_dirty = 1
        self.changed(lambda x:x.fpa_changed_cb())

    def set_filter(self, filter):
        self.filter = filter
        self.cache_dirty = 1
        self.changed(lambda x:x.fpa_changed_cb())

    def fill_cache(self):
        self.cache = []
        if not (self.cache_dirty and self.target and self.filter):
            return
        for pkg in self.target.get_all():
            if self.filter(pkg):
                self.cache.append(pkg)
        self.cache_dirty = 0

    def len(self):
        if self.cache_dirty:
            self.fill_cache()
        return len(self.cache)

    def get(self, i):
        if self.cache_dirty:
            self.fill_cache()
        assert 0 <= i and i < self.len()
        return self.cache[i]

    def get_all(self):
        if self.cache_dirty:
            self.fill_cache()
            return self.cache


###############################################################################


class PackagesFromDaemon(PackageArray, red_serverlistener.ServerListener):

    def __init__(self):
        PackageArray.__init__(self)
        red_serverlistener.ServerListener.__init__(self)

        self.packages = []
        self.seqno = -1

    # This is the method that derived classes need to implement
    def get_packages_from_daemon(self, server):
        return []

    def server_changed(self, server):

        packages = self.get_packages_from_daemon(server)

        if packages:
            packages.sort(pkg_cmp)

        # FIXME: we should only emit if array.packages != packages
        def set_pkg_cb(array, p):
            array.packages = p
        self.changed(set_pkg_cb, packages)

    def sync_with_daemon(self):
        self.server_changed(rcd_util.get_server())

    def len(self):
        return len(self.packages)

    def get(self, i):
        assert 0 <= i and i < self.len()
        return self.packages[i]

    def get_all(self):
        return self.packages


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

        ## Since we might want to add extra methods for accessing
        ## more of the update data later, there is no harm in keeping
        ## the whole list of updates around.
        self.updates = server.rcd.packsys.get_updates()
        packages = map(lambda x: x[1], self.updates)

        return packages

