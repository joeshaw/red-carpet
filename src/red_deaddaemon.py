###
### Copyright (C) 2002-2003 Ximian, Inc.
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

import threading
import gtk

import rcd_util, red_serverlistener

_daemon_is_dead = 0
_dead_daemon_lock = threading.Lock()
_post_restore_thunk_list = []

def show_server_is_alive_dialog():

    global _daemon_is_dead
    global _post_restore_thunk_list

    dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO,
                               gtk.BUTTONS_CLOSE,
                               "Connection to daemon restored.\n" \
                               "(We need a better message here too.)")
    dialog.show()
    gtk.threads_enter()
    dialog.run()
    gtk.threads_leave()
    dialog.destroy()

    _dead_daemon_lock.acquire()
    for thunk in _post_restore_thunk_list:
        thunk()
    _post_restore_thunk_list = []
    _daemon_is_dead = 0
    red_serverlistener.thaw_polling()
    _dead_daemon_lock.release()


def wait_for_server_cb(dialog):
    try:
        server = rcd_util.get_server()
        ping = server.rcd.system.ping()
        if ping:
            dialog.destroy()
            show_server_is_alive_dialog()
            return 0
    except: # FIXME: don't just mindlessly catch all exceptions
        print "waiting for server..."
        return 1


def show_daemon_dialog_real():

    dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                               gtk.BUTTONS_NONE,
                               "Lost contact with the daemon!\n" \
                               "(We need a better message here)" )
    dialog.add_button("Exit Red Carpet", 1)
    dialog.set_modal(1)

    def dialog_response_cb(dialog, val):
        gtk.mainquit()

    dialog.connect("response", dialog_response_cb)
    dialog.show_all()

    gtk.timeout_add(500, wait_for_server_cb, dialog)

    return 0


def show_daemon_dialog(post_restore_thunk=None):
    global _daemon_is_dead

    _dead_daemon_lock.acquire()

    if post_restore_thunk:
        assert callable(post_restore_thunk)
        _post_restore_thunk_list.append(post_restore_thunk)

    if not _daemon_is_dead:
        red_serverlistener.freeze_polling()
        gtk.idle_add(show_daemon_dialog_real)

    _daemon_is_dead = 1

    _dead_daemon_lock.release()


