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

import getpass, os, string, sys, time, threading, gtk

red_name      = "ZENworks 7 Linux Management Update Manager"
red_version   = None
red_copyright = u"Copyright \u00a9 2000-2005 Novell, Inc. All Rights Reserved."
debug         = os.getenv("RC_GUI_DEBUG")

help_path     = None

from red_gettext import _
import rcd_util
import red_connection
import red_console
import red_appwindow
import red_search
import red_updates
import red_transaction
import red_history
import red_option
import red_settings
import red_software
import red_installfiles
import red_bundlecomponent

import red_patches

red_running = 1

gtk.threads_init()

###
### This is some code to help us track down performance problems
### in GtkTreeView, etc.  Turned off by default.
###

last_tick = time.time()
def tick_cb():
    global last_tick
    last_tick = time.time()
    return 1

class TickThread(threading.Thread):

    def run(self):
        self.last_tick = last_tick
        self.last_block = 0
        while red_running:
            now = time.time()
            if now - last_tick > 0.25:
                if self.last_block == 0:
                    print "**** UI is blocking!"
                    #os.kill(os.getpid(), signal.SIGTRAP)
                self.last_block = now
                self.last_tick = last_tick
            else:
                if self.last_block:
                    t = self.last_block - self.last_tick
                    print "**** UI blocked for approx %.2fs" % t
                self.last_block = 0
                #os.kill(os.getpid(), signal.SIGTRAP)
            time.sleep(0.1)

def ticker():
    gtk.timeout_add(50, tick_cb);
    TickThread().start()

def get_title():
    return red_name

###
### main
###
   
def main(version):
    global red_version
    red_version = version
    
    print "%s %s" % (red_name, version)
    print red_copyright
    print

    argv = sys.argv[1:]
    opt_dict, args = red_option.process_argv(argv)

    if opt_dict.has_key("version"):
        sys.exit(0)

    if opt_dict.has_key("help"):
        red_option.usage()
        sys.exit(0)

    if opt_dict.has_key("local") and opt_dict.has_key("host"):
        print _("ERROR: You cannot specify both -h/--host and -l/--local options")
        sys.exit(1)

    local = 0
    host = None
    username = None
    password = None

    if opt_dict.has_key("local"):
        local = 1

    if opt_dict.has_key("host"):
        host = opt_dict["host"]
        if host[0] == "/":
            local = 1
    elif opt_dict.has_key("user"):
        local = 0

    if host:
        if opt_dict.has_key("user"):
            username = opt_dict["user"]
        else:
            username = getpass.getuser()

        if opt_dict.has_key("password"):
            password = opt_dict["password"]
        else:
            # This'll always fail and pop up the dialog.
            password = ""
    else:
        if opt_dict.has_key("user"):
            print _("ERROR: You cannot specify a user to a local daemon")
            sys.exit(1)

        if opt_dict.has_key("host"):
            url = opt_dict["host"]

    # Try the command-line options or the saved data first
    # Enclosed in an empty try-except because we don't care about the
    # error on the first connect.
    server = None
    dd = red_settings.DaemonData()
    try:
        if local or host:
            if password:
                pw_md5 = rcd_util.md5ify_password(password)
            else:
                pw_md5 = None
            
            dd.data_set((local, host, username, password))

            server = red_connection.connect(local, host, username, pw_md5)
        else:
            connect_info = dd.data_get()
            local = connect_info[0]
            server = red_connection.connect(*connect_info)
    except:
        pass

    # That failed, pop up the dialog
    if server is None:
        server, local = red_connection.connect_from_window()

    if server is None:
        sys.exit(1)

    rcd_util.register_server(server, local)

    if debug:
        ticker()

    app = red_appwindow.AppWindow(server)
    app.set_title(get_title())

    app.register_component(red_updates.UpdatesComponent())
    app.register_component(red_software.InstalledComponent())
    app.register_component(red_software.AvailableComponent())
    app.register_component(red_search.SearchComponent())
    app.register_component(red_bundlecomponent.BundleComponent())

    if rcd_util.server_has_patch_support(server):
        app.register_component(red_patches.PatchComponent())

    app.register_component(red_history.HistoryComponent())
    app.register_component(red_transaction.TransactionComponent())

    app.show()

    #add files to install from the cmdline
    if len(args) > 0:
        ret = red_installfiles.install_files(args)
        if not ret:
            red_appwindow.run_transaction_cb(app)

    gtk.main()

    global red_running
    red_running = 0

    # This will terminate all our child threads without joining
    os._exit(0)
    


