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

import sys, weakref
import rcd_util

package_data = {}
listeners = {}
listener_id = 0

class PendingOpsListener:

    def __init__(self):
        self.lid = register_listener(self)

    def pendingops_disconnect():
        unregister_listener(self.lid)
        self.lid = 0

    def pendingops_changed(self, pkg, key, value, old_value):
        sys.stderr.write("PendingOpsListener.changed not defined.\n")


def register_listener(obj):
    global listeners, listener_id
    listener_id += 1
    listeners[listener_id] = weakref.ref(obj)
    return listener_id

def unregister_listener(lid):
    global listeners
    del listeners[lid]

def signal_listeners(pkg, key, value, old_value):
    for lid in listeners.keys():
        listener_ref = listeners[lid]
        listener = listener_ref()
        if listener:
            listener.pendingops_changed(pkg, key, value, old_value)
        else:
            del listeners[lid]


###############################################################################


class UnknownPackage(Exception):
    def __init__(self, pkg):
        self.pkg = pkg
    def __repr_(self):
        return "<UnknownPackage '%s'>" % self.pkg

class UnknownKey(Exception):
    def __init__(self, key, pkg):
        self.key = key
        self.pkg = pkg
    def __repr_(self):
        return "<UnknownKey '%s' for package '%s'>" % (self.key, self.pkg)

class __NoDefault:
    pass

__no_default = __NoDefault()

def get(pkg, key, default=__no_default):
    pkg_key = rcd_util.get_package_key(pkg)
    dict = package_data.get(pkg_key)
    if not dict:
        raise UnknownPackage, pkg
    if default == __no_default:
        if not dict.has_key(key):
            raise UnknownKey, key, pkg
    return dict.get(key, default)

def set(pkg, key, value):
    global package_data
    pkg_key = rcd_util.get_package_key(pkg)
    dict = package_data.setdefault(pkg_key, {"__package": pkg})
    old_value = dict.get(key)
    if old_value != value:
        dict[key] = value
        signal_listeners(pkg, key, value, old_value)

def clear(pkg, key):
    global package_data
    pkg_key = rcd_util.get_package_key(pkg)
    dict = package_data.get(pkg_key)
    if dict and dict.has_key(key):
        old_value = dict[key]
        del dict[key]
        signal_listeners(pkg, key, None, old_value)

def has_package(pkg):
    pkg_key = rcd_util.get_package_key(pkg)
    return package_data.has_key(pkg_key)

def del_package(pkg):
    global package_data
    pkg_key = rcd_util.get_package_key(pkg)
    if package_data.has_key(pkg_key):
        del package_data[pkg_key]
        signal_listeners()

def packages():
    return map(lambda x:x["__package"], package_data.values())

def keys(pkg):
    pkg_key = rcd_util.get_package_key(pkg)
    dict = package_data.get(pkg_key)
    if not dict:
        return None
    return filter(lambda x:x[0:2] != "__", dict.keys())
        

###############################################################################

NO_ACTION                 = 0
TO_BE_INSTALLED           = 1
TO_BE_REMOVED             = 2
TO_BE_INSTALLED_CANCELLED = 3
TO_BE_REMOVED_CANCELLED   = 4

def get_action(pkg):
    if has_package(pkg):
        return get(pkg, "action", NO_ACTION)
    return NO_ACTION

def set_action(pkg, action):

    ## FIXME!: Setting the action on a package can/should modify the action
    ## for other packages w/ the same name.  The little snippet of code
    ## below is _not_ the correct semantics for this... it is just a
    ## "proof of concept" to ensure that the notification, etc. all works
    ## properly.  The correct behavior needs to be worked out, and might
    ## be a bit tricky to get right.
    key = rcd_util.get_package_key(pkg)
    for p in packages():
        if p["name"] == pkg["name"] and rcd_util.get_package_key(p) != key:
            set(p, "action", NO_ACTION)

    set(pkg, "action", action)

def toggle_action(pkg):
    act = get_action(pkg)
    if act:
        new_act = NO_ACTION
    elif pkg["installed"]:
        new_act = TO_BE_REMOVED
    else:
        new_act = TO_BE_INSTALLED
    set_action(pkg, new_act)

def toggle_action_with_cancellation(pkg):
    act = get_action(pkg)
    new_act = act
    if act == TO_BE_INSTALLED:
        new_act = TO_BE_INSTALLED_CANCELLED
    elif act == TO_BE_INSTALLED_CANCELLED:
        new_act = TO_BE_INSTALLED
    elif act == TO_BE_REMOVED:
        new_act = TO_BE_REMOVED_CANCELLED
    elif act == TO_BE_REMOVED_CANCELLED:
        new_act = TO_BE_REMOVED
    if new_act != act:
        set_action(pkg, new_act)

def packages_with_actions():
    return map(lambda x: x["__package"],
               filter(lambda x: x.get("action", NO_ACTION) != NO_ACTION,
                      package_data.values()))

def clear_action_cancellations():
    for pkg in packages_with_actions():
        act = get(pkg, "action", NO_ACTION)
        if act == TO_BE_INSTALLED_CANCELLED \
           or act == TO_BE_REMOVED_CANCELLED:
            set(pkg, "action", NO_ACTION)

def pending_install_count():
    count = 0
    for dict in package_data.values():
        if dict.get("action", NO_ACTION) == TO_BE_INSTALLED:
            count += 1
    return count

def pending_remove_count():
    count = 0
    for dict in package_data.values():
        if dict.get("action", NO_ACTION) == TO_BE_REMOVED:
            count += 1
    return count

def resolve_dependencies():
    install_packages = []
    remove_packages = []
    for dict in package_data.values():
        action = dict.get("action", NO_ACTION)
        if action == TO_BE_INSTALLED:
            install_packages.append(dict["__package"])
        elif action == TO_BE_REMOVED:
            remove_packages.append(dict["__package"])

    serv = rcd_util.get_server()
    dep_install, dep_remove, dep_info = \
                 serv.rcd.packsys.resolve_dependencies(install_packages,
                                                       remove_packages,
                                                       [])

    return install_packages, remove_packages, dep_install, dep_remove
