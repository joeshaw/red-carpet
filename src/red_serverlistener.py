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
import gobject, gtk
import rcd_util

###
### Set up our polling timeout.  This should be the only place
### where we poll for the world sequence number.
###

poll_count   = 0
last_server  = -1
freeze_count = 0
missed_polls = 0
poll_timeout = 0
timeout_len  = 3000

worker            = None
worker_handler_id = 0

last_package_seqno      = -1
last_channel_seqno      = -1
last_subscription_seqno = -1

listeners = {}
listener_id = 0

def register_listener(obj):
    global listener_id, poll_count, last_seqno, last_server
    global last_package_seqno
    global last_channel_seqno
    global last_subscription_seqno

    # If we haven't polled yet, initialize things so that we won't
    # necessarily get a server change reported on the first poll.
    if poll_count == 0:
        server = rcd_util.get_server()
        last_server = id(server)
        last_package_seqno, last_channel_seqno, last_subscription_seqno \
                            = server.rcd.packsys.world_sequence_numbers()
        poll_count += 1
    
    listener_id += 1
    listeners[listener_id] = weakref.ref(obj)
    return listener_id

def unregister_listener(lid):
    global listeners
    del listeners[lid]

def signal_listeners(server,
                     packages_changed,
                     channels_changed,
                     subscriptions_changed):

    if packages_changed or channels_changed or subscriptions_changed:

        for lid in listeners.keys():
            listener_ref = listeners[lid]
            listener = listener_ref()
            if listener:

                if packages_changed:
                    listener.packages_changed(server)

                if channels_changed:
                    listener.channels_changed(server)

                if subscriptions_changed:
                    listener.subscriptions_changed(server)

            else:
                unregister_listener(lid)

def poll_cb():
    global poll_count, missed_polls, last_server
    global last_package_seqno
    global last_channel_seqno
    global last_subscription_seqno
    global worker, worker_handler_id

    poll_count = poll_count + 1
    
    if freeze_count == 0:

        # This lets us do the right thing if the server changes
        # out from under us.
        server = rcd_util.get_server_proxy()
        if id(server) != last_server:
            last_package_seqno      = -1
            last_channel_seqno      = -1
            last_subscription_seqno = -1
        last_server = id(server)

        if worker:
            if worker_handler_id:
                worker.disconnect(worker_handler_id)
                worker_handler_id = 0
            worker.cancel()

        def sequence_numbers_finished_cb(worker):
            global last_package_seqno
            global last_channel_seqno
            global last_subscription_seqno
            
            if not worker.is_cancelled():
                curr_package_seqno, curr_channel_seqno, curr_subscription_seqno \
                                    = worker.get_result()

                
                if curr_channel_seqno != last_channel_seqno or \
                       curr_subscription_seqno != last_subscription_seqno:
                    rcd_util.reset_channels()

                signal_listeners(server,
                                 curr_package_seqno != last_package_seqno,
                                 curr_subscription_seqno != last_subscription_seqno,
                                 curr_channel_seqno != last_channel_seqno)

                last_package_seqno = curr_package_seqno
                last_subscription_seqno = curr_subscription_seqno
                last_channel_seqno = curr_channel_seqno
        
            missed_polls = 0

        if server:
            worker = server.rcd.packsys.world_sequence_numbers()
            worker_handler_id = worker.connect("ready",
                                               sequence_numbers_finished_cb)
        
    else:
        missed_polls += 1
        
    return 1

def reset_polling(do_immediate_poll=1):
    global poll_timeout
    if poll_timeout:
        gtk.timeout_remove(poll_timeout)
    # do the first poll immediately
    if do_immediate_poll:
        poll_cb()
    poll_timeout = gtk.timeout_add(timeout_len, poll_cb)

def freeze_polling():
    global freeze_count, poll_timeout
    freeze_count += 1

def thaw_polling():
    global freeze_count
    if freeze_count > 0:
        freeze_count -= 1
    if freeze_count == 0:
        if missed_polls:
            poll_cb()       # do the first poll right away
            reset_polling() # and then get poll timeout started again


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
        self.__listener_id = register_listener(self)

    # These are the function that should be overrided in derived classes.
    def packages_changed(self, server):
        pass

    def channels_changed(self, server):
        pass

    def subscriptions_changed(self, server):
        pass

    def process_package_changes(self, server):
        if self.__freeze_count > 0:
            self.__missed_package_changes += 1
        else:
            self.packages_changed(server)
            print "Packages changed!"
            self.__missed_package_changes = 0

    def process_channel_changes(self, server):
        if self.__freeze_count > 0:
            self.__missed_channel_changes += 1
        else:
            self.channels_changed(server)
            print "Channels changed!"
            self.__missed_channel_changes = 0

    def process_subscription_changes(self, server):
        if self.__freeze_count > 0:
            print "Subs changed!"
            self.__missed_subscription_changes += 1
        else:
            self.subscriptions_changed(server)
            self.__missed_subscription_changes = 0

    def freeze(self):
        self.__freeze_count += 1

    def thaw(self):
        if self.__freeze_count > 0:
            self.__freeze_count -= 1
            if self.__freeze_count == 0:
                server = rcd_util.get_server()
                if self.__missed_package_changes > 0:
                    self.process_package_changes(server)
                if self.__missed_channel_changes > 0:
                    self.process_channel_changes(server)
                if self.__missed_subscription_changes > 0:
                    self.process_subscription_changes(server)

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

            if pending:
                msg = string.join(pending, ", ")
                sys.stderr.write(" with pending %s changes" % msg)

            sys.stderr.write("!\n")

        unregister_listener(self.__listener_id)


