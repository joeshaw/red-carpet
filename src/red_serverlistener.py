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

import sys, weakref, threading
import gobject, gtk
import rcd_util

###
### Set up our polling timeout.  This should be the only place
### where we poll for the world sequence number.
###

poll_lock = threading.RLock()

poll_count   = 0
last_server  = -1
freeze_count = 0
missed_polls = 0
poll_timeout = 0
timeout_len  = 3000

last_package_seqno      = -1
last_channel_seqno      = -1
last_subs_seqno = -1
last_user_seqno         = -1

listeners = {}
listener_id = 0

def register_listener(obj):
    global listener_id
    listener_id += 1
    listeners[listener_id] = weakref.ref(obj)
    return listener_id

def unregister_listener(lid):
    global listeners
    del listeners[lid]

def signal_listeners(packages_changed,
                     channels_changed,
                     subscriptions_changed,
                     users_changed):

    if packages_changed \
           or channels_changed \
           or subscriptions_changed \
           or users_changed:

        for lid in listeners.keys():
            listener_ref = listeners[lid]
            listener = listener_ref()
            if listener:

                if packages_changed:
                    listener.packages_changed()

                if channels_changed:
                    listener.channels_changed()

                if subscriptions_changed:
                    listener.subscriptions_changed()

                if users_changed:
                    listener.users_changed()

            else:
                unregister_listener(lid)

def poll_cb():
    global poll_count, missed_polls

    poll_lock.acquire()

    if freeze_count == 0:

        server = rcd_util.get_server()
        if server is None:
            return

        class SeqNoChecker(threading.Thread):

            def run(self):
                global last_server
                global poll_count
                global last_package_seqno
                global last_subs_seqno
                global last_channel_seqno
                global last_user_seqno

                poll_lock.acquire()

                server = rcd_util.get_server()

                (curr_package_seqno,
                 curr_channel_seqno,
                 curr_subs_seqno) = server.rcd.packsys.world_sequence_numbers()
                curr_user_seqno = server.rcd.users.sequence_number()

                # This lets us do the right thing if the server changes
                # out from under us.
                if id(server) != last_server:
                    last_package_seqno      = -1
                    last_channel_seqno      = -1
                    last_subs_seqno = -1
                    last_user_seqno         = -1
                last_server = id(server)

                if curr_channel_seqno != last_channel_seqno or \
                       curr_subs_seqno != last_subs_seqno:
                    rcd_util.reset_channels()

                if curr_user_seqno != last_user_seqno:
                    rcd_util.reset_server_permissions()

                # Ignore any problems on the first poll, since we know we
                # don't have valid server information before that point.
                if poll_count != 0:
                    # We signal the listeners in an idle function so that
                    # it will always happen in the main thread.
                    gtk.idle_add(signal_listeners,
                                 curr_package_seqno != last_package_seqno,
                                 curr_channel_seqno != last_channel_seqno,
                                 curr_subs_seqno != last_subs_seqno,
                                 curr_user_seqno != last_user_seqno)

                last_package_seqno = curr_package_seqno
                last_subs_seqno = curr_subs_seqno
                last_channel_seqno = curr_channel_seqno
                last_user_seqno = curr_user_seqno

                poll_lock.release()

                poll_count += 1

        th = SeqNoChecker()
        th.start()

        missed_polls = 0
        
    else:
        missed_polls += 1

    poll_lock.release()
        
    return 1

def reset_polling(do_immediate_poll=1):
    global poll_timeout
    poll_lock.acquire()
    if poll_timeout:
        gtk.timeout_remove(poll_timeout)
    # do the first poll immediately
    if do_immediate_poll:
        poll_cb()
    poll_timeout = gtk.timeout_add(timeout_len, poll_cb)
    poll_lock.release()

def freeze_polling():
    global freeze_count
    poll_lock.acquire()
    freeze_count += 1
    poll_lock.release()

def thaw_polling(do_immediate_poll=0):
    global freeze_count
    poll_lock.acquire()
    if freeze_count > 0:
        freeze_count -= 1
    if freeze_count == 0:
        if missed_polls:
            do_immediate_poll = 1
        reset_polling(do_immediate_poll)    # get poll timeout started again
    poll_lock.release()


# Start polling.  We skip our first poll, since we won't have made a
# connection to the server yet.
reset_polling(do_immediate_poll=0)

###############################################################################

###
###  The ServerListener class: a base class for objects that need to
### detect when the state of the world changes on the server
###        

class ServerListener:

    def __init__(self):
        self.__freeze_count = 0
        self.__missed_package_changes = 0
        self.__missed_channel_changes = 0
        self.__missed_subscription_changes = 0
        self.__missed_user_changes = 0
        self.__listener_id = register_listener(self)

    # These are the function that should be overrided in derived classes.
    def packages_changed(self):
        pass

    def channels_changed(self):
        pass

    def subscriptions_changed(self):
        pass

    def users_changed(self):
        pass

    def process_package_changes(self):
        if self.__freeze_count > 0:
            self.__missed_package_changes += 1
        else:
            self.packages_changed()
            self.__missed_package_changes = 0

    def process_channel_changes(self):
        if self.__freeze_count > 0:
            self.__missed_channel_changes += 1
        else:
            self.channels_changed()
            self.__missed_channel_changes = 0

    def process_subscription_changes(self):
        if self.__freeze_count > 0:
            self.__missed_subscription_changes += 1
        else:
            self.subscriptions_changed()
            self.__missed_subscription_changes = 0

    def process_user_changes(self):
        if self.__freeze_count > 0:
            self.__missed_user_changes += 1
        else:
            self.users_changed()
            self.__missed_user_changes = 0


    def freeze(self):
        self.__freeze_count += 1

    def thaw(self):
        if self.__freeze_count > 0:
            self.__freeze_count -= 1
            if self.__freeze_count == 0:
                if self.__missed_package_changes > 0:
                    self.process_package_changes()
                if self.__missed_channel_changes > 0:
                    self.process_channel_changes()
                if self.__missed_subscription_changes > 0:
                    self.process_subscription_changes()
                if self.__missed_user_changes > 0:
                    self.process_user_changes()

    def shutdown_listener(self):
        if self.freeze_count > 0:
            sys.stderr.write("Shutting down frozen listener")

            pending = []
            if self.__missed_package_changes > 0:
                pending.append("package")
            if self.__missed_channel_changes > 0:
                pending.append("channel")
            if self.__missed_subscription_changes > 0:
                pending.append("subscription")
            if self.__missed_user_changes > 0:
                pending.append("user")

            if pending:
                msg = string.join(pending, ", ")
                sys.stderr.write(" with pending %s changes" % msg)

            sys.stderr.write("!\n")

        unregister_listener(self.__listener_id)


