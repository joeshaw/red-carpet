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
import red_listmodel
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

    if pkg["installed"]:
        return "installed"
    elif pkg["name_installed"] > 0: # upgrade
        return "upgrade"
    elif pkg["name_installed"] < 0:
        return "downgrade"
    else:
        return "uninstalled"

__update_icon              = red_pixbuf.get_pixbuf("update")
__downgrade_icon           = red_pixbuf.get_pixbuf("warning", width=24, height=24)
__installed_icon           = red_pixbuf.get_pixbuf("installed")
__uninstalled_icon         = red_pixbuf.get_pixbuf("uninstalled")

def pkg_status_icon(pkg):

    if pkg["installed"]:
        return __installed_icon
    elif pkg["name_installed"] > 0: # upgrade
        return __update_icon
    elif pkg["name_installed"] < 0: # downgrade
        return __downgrade_icon
    return __uninstalled_icon

def pkg_action(pkg):

    pending = red_pendingops.get_action(pkg)
    if pending:
        if pending == red_pendingops.TO_BE_INSTALLED \
           or pending == red_pendingops.TO_BE_INSTALLED_CANCELLED:
            if pkg["name_installed"] > 0:
                str = "upgrade"
            elif pkg["name_installed"] < 0:
                str = "<b>downgrade</b>"
            else:
                str = "install"
            if pending == red_pendingops.TO_BE_INSTALLED_CANCELLED:
                str = "<s>%s</s>" % str
            return str
        
        elif pending == red_pendingops.TO_BE_REMOVED \
             or pending == red_pendingops.TO_BE_REMOVED_CANCELLED:
            str = "remove"
            if pending == red_pendingops.TO_BE_REMOVED_CANCELLED:
                str = "<s>%s</s>" % str
            return str
        
        else:
            return "?Unknown?"
    else:
        return ""

__to_be_installed_icon     = red_pixbuf.get_pixbuf("to-be-installed")
__to_be_removed_icon       = red_pixbuf.get_pixbuf("to-be-removed")
__to_be_installed_xxx_icon = red_pixbuf.get_pixbuf("to-be-installed-cancelled")
__to_be_removed_xxx_icon   = red_pixbuf.get_pixbuf("to-be-removed-cancelled")

def pkg_action_icon(pkg):

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
    else:
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
    ("ACTION",            pkg_action,            gobject.TYPE_STRING),
    ("ACTION_ICON",       pkg_action_icon,       gtk.gdk.Pixbuf),
    )

for i in range(len(COLUMNS)):
    name = COLUMNS[i][0]
    exec("COLUMN_%s = %d" % (name, i))


###
### Sort functions
###

    
def sort_pkgs_by_name(a, b):
    xa = a.get("_lower_name")
    if not xa:
        a["_lower_name"] = xa = string.lower(a["name"])
    xb = b.get("_lower_name")
    if not xb:
        b["_lower_name"] = xb = string.lower(b["name"])
    return cmp(xa, xb)

def sort_pkgs_by_size(a, b):
    return cmp(a["file_size"], b["file_size"])

def sort_pkgs_by_importance(a, b):
    return cmp(a["importance_num"], b["importance_num"])

def sort_pkgs_by_channel(a, b):
    return cmp(rcd_util.get_package_channel_name(a),
               rcd_util.get_package_channel_name(b))

def sort_pkgs_by_status(a, b):
    def rank_status(p):
        if p["installed"]:
            return 1
        elif p["name_installed"] > 0: # upgrade
            return 0
        elif p["name_installed"] < 0: # downgrade
            return 3
        else:
            return 2

    return cmp(rank_status(a), rank_status(b))

def sort_pkgs_by_action(a, b):
    def rank_action(p):
        pending = red_pendingops.get_action(p)
        if pending:
            if pending == red_pendingops.TO_BE_INSTALLED \
               or pending == red_pendingops.TO_BE_INSTALLED_CANCELLED:
                if p["name_installed"] > 0:
                    return 0
                elif p["name_installed"] < 0:
                    return 1
                else:
                    return 2

            elif pending == red_pending.TO_BE_REMOVED \
                 or pending == red_pendingops.TO_BE_REMOVED_CANCELLED:
                return 3
        else:
            return 4

    return cmp(rank_action(a), rank_action(b))

###
### PackageArray: our magic-laden base class
###

class PackageArray(red_listmodel.ListModel,
                   red_pendingops.PendingOpsListener):

    def __init__(self):
        gobject.GObject.__init__(self)
        red_listmodel.ListModel.__init__(self, sort_fn=sort_pkgs_by_name)
        red_pendingops.PendingOpsListener.__init__(self)

        self.__package_keys = {}
        self.__busy_flag = 0

        for name, callback, type in COLUMNS:
            self.add_column(callback, type)

    ## This function should take the data in the array and sort it according
    ## to the specified function.  This is a "protected" function and
    ## shouldn't be called by users of PackageArrays.
    #def sort(self, sort_fn):
    #    assert 0, "PackageArray.sort not defined"

    def do_changed(self):
        operator, args = red_listmodel.ListModel.do_changed(self)

        if operator:
            self.__package_keys = {}
            for i in xrange(self.length()):
                p = self.get_list_item(i)
                key = rcd_util.get_package_key(p)
                indices = self.__package_keys.setdefault(key, [])
                indices.append(i)

    ## Sort functions
                
    def changed_sort_by_name(self, reverse=0):
        self.changed_sort_fn(sort_pkgs_by_name, reverse)

    def changed_sort_by_size(self, reverse=0):
        self.changed_sort_fn(sort_pkgs_by_size, reverse)

    def changed_sort_by_importance(self, reverse=0):
        self.changed_sort_fn(sort_pkgs_by_importance, reverse)

    def changed_sort_by_channel(self, reverse=0):
        self.changed_sort_fn(sort_pkgs_by_channel, reverse)

    def changed_sort_by_status(self, reverse=0):
        self.changed_sort_fn(sort_pkgs_by_status, reverse)

    def changed_sort_by_action(self, reverse=0):
        self.changed_sort_fn(sort_pkgs_by_action, reverse)

    ## Find all instances of pkg in the PackageArray, and cause a
    ## 'changed_one' signal to be emitted for each.
    def changed_one_by_package(self, pkg):
        key = rcd_util.get_package_key(pkg)
        indices = self.__package_keys.get(key, [])
        for i in indices:
            self.changed_one(i)

    ## Busy/message functions

    def message_push(self, msg, context_id=-1):
        if context_id < 0:
            context_id = hash(self)
        self.emit("message_push", msg, context_id)

    def message_pop(self, context_id=-1):
        if context_id < 0:
            context_id = hash(self)
        self.emit("message_pop", context_id)

    def busy(self, flag):
        if self.__busy_flag ^ flag:
            self.__busy_flag = flag
            self.emit("busy", flag)

    ## Implements PendingOpsListener
    def pendingops_changed(self, pkg, key, value, old_value):
        self.changed_one_by_package(pkg)
        
    def spew(self):
        for pkg in self.get_all():
            print pkg["name"]


gobject.type_register(PackageArray)

gobject.signal_new("busy",
                   PackageArray,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_BOOLEAN,))

gobject.signal_new("message_push",
                   PackageArray,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING, gobject.TYPE_UINT))

gobject.signal_new("message_pop",
                   PackageArray,
                   gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_UINT,))

###############################################################################


class PackageStore(PackageArray):

    def __init__(self):
        PackageArray.__init__(self)
        self.__store = []

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
        self.__target = None
        if target:
            self.set_target(target)

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
        self.__length = 0


    # This is the method that derived classes need to implement
    def get_packages_from_daemon(self):
        return []

    # The derived class should use this function to report the packages
    # it received from the daemon.
    def set_packages(self, packages):
        self.__length = len(packages)
        def set_pkg_cb(me, p):
            me.__packages = p
        self.changed(set_pkg_cb, packages)

    def refresh(self):
        self.get_packages_from_daemon()
        self.pending_refresh = 0

    def schedule_refresh(self):
        if self.pending_refresh == 0:
            def schedule_cb(s):
                s.refresh()
                return 0
            self.pending_refresh = gtk.timeout_add(20, schedule_cb, self)

    def packages_changed(self):
        self.schedule_refresh()

    def locks_changed(self):
        self.schedule_refresh()

    def len(self):
        return self.__length

    def get(self, i):
        assert 0 <= i < self.len()
        return self.__packages[i]

    def get_all(self):
        return self.__packages


###############################################################################

_query_cache = {}

def _query_to_key(query):
    key = str(query)
    return key

def _get_query_from_cache(query):
    key = _query_to_key(query)
    return _query_cache.get(key)

def _cache_query_results(query, results):
    key = _query_to_key(query)
    _query_cache[key] = results

def _reset_query_cache():
    _query_cache.clear()

class PackagesFromQuery(PackagesFromDaemon):

    def __init__(self, query=None):
        PackagesFromDaemon.__init__(self)
        self.__worker = None
        self.__worker_handler_id = 0
        self.__query_msg = None
        self.__query_filter = None
        self.set_query(query)

    def get_packages_from_daemon(self):

        if self.query is None:
            self.set_packages([])
            return

        cached = _get_query_from_cache(self.query)
        if cached is not None:
            if self.__query_filter:
                cached = filter(self.__query_filter, cached)
            self.set_packages(cached)
            return
        
        server = rcd_util.get_server_proxy()
            
        if self.__worker:
            if self.__worker_handler_id:
                self.__worker.disconnect(self.__worker_handler_id)
                self.__worker_handler_id = 0
            self.__worker.cancel()

        def query_finished_cb(worker, array):
            if not worker.is_cancelled():
                packages = worker.get_result()
                elapsed = time.time() - worker.t1
                print "query time=%.2fs" % elapsed
                print "got %d packages" % len(packages)

                _cache_query_results(self.query, packages)

                if self.__query_filter:
                    packages = filter(self.__query_filter, packages)
                packages = self.filter_duplicates(packages)
                
                array.set_packages(packages or [])
            array.message_pop()
            array.busy(0)


        print "launching query"
        self.busy(1)
        if self.__query_msg:
            self.message_push(self.__query_msg)
        self.set_packages([])

        self.__worker = server.rcd.packsys.search(self.query)
        self.__worker.t1 = time.time()
        self.__worker_handler_id = self.__worker.connect("ready",
                                                         query_finished_cb,
                                                         self)
        
    def set_query(self, query, query_msg=None, query_filter=None):
        self.query = query
        self.__query_msg = query_msg
        self.__query_filter = query_filter
        self.schedule_refresh()

    def packages_changed(self):
        _reset_query_cache()
        PackagesFromDaemon.packages_changed(self)

    def channels_changed(self):
        _reset_query_cache()
        pass

    def locks_changed(self):
        _reset_query_cache()
        PackagesFromDaemon.locks_changed(self)

    def filter_duplicates(self, packages):
        if self.query:
            for r in self.query:
                if r[0] == "package-installed":
                    if r[2] == "false":
                        # Shouldn't contain duplicates
                        return packages
                    else:
                        break

        in_system = {}
        for p in packages:
            if p["installed"] and not p["channel"]:
                # System package
                key = "%s/%s" % (p["name"], rcd_util.get_package_EVR(p))
                in_system[key] = 1

        for p in packages:
            key = "%s/%s" % (p["name"], rcd_util.get_package_EVR(p))
            if p["channel"] and in_system.has_key(key):
                # Channel package, has system package.
                packages.remove(p)

        return packages

###############################################################################


class UpdatedPackages(PackagesFromDaemon):

    def __init__(self):
        PackagesFromDaemon.__init__(self)
        self.__worker = None
        self.__worker_handler_id = 0
        self.refresh()

    def get_packages_from_daemon(self):

        if self.__worker:
            if self.__worker_handler_id:
                self.__worker.disconnect(self.__worker_handler_id)
                self.__worker_handler_id = 0
            self.__worker.cancel()

        def query_finished_cb(worker, array):
            if not worker.is_cancelled():
                updates = worker.get_result()
                packages = []
                for old_pkg, pkg, history in updates:
                    pkg["__old_package"] = old_pkg
                    pkg["__history"] = history
                    packages.append(pkg)
                array.set_packages(packages)
            array.message_pop()
            array.busy(0)

        self.busy(1)
        self.message_push("Looking for updates...")
        self.set_packages([])

        server = rcd_util.get_server_proxy()
        self.__worker = server.rcd.packsys.get_updates()
        self.__worker_handler_id = self.__worker.connect("ready",
                                                         query_finished_cb,
                                                         self)

    # The list of updates needs to refresh when the list of available
    # channels or subscriptions change.
    def subscriptions_changed(self):
        self.schedule_refresh()

    def channels_changed(self):
        self.schedule_refresh()

    def locks_changed(self):
        self.schedule_refresh()
