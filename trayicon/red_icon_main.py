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

red_name      = "Red Carpet Notification Tray Icon"
red_version   = None
red_copyright = "2002-2004"
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
import red_tray
import red_pixbuf
import os
import threading

red_running = 1

POLL_INTERVAL = 1000*60*30 #half an hour

gtk.threads_init()

class UpdateIcon(red_tray.TrayIcon):

    def __init__(self):
        red_tray.TrayIcon.__init__(self, "Red Carpet Notification Icon")

        self.thread = None

        self.high_priority_icon = red_pixbuf.get_pixbuf('importance-necessary')
        self.low_priority_icon = red_pixbuf.get_pixbuf('importance-urgent')
            
        self.image = gtk.Image()
        self.box = gtk.EventBox()
        self.box.connect('button_press_event',
                         self.image_press_cb, self)
        self.box.add(self.image)
        self.add(self.box)

        self.tooltips = gtk.Tooltips()
        
        self.check_updates(None)
        gtk.timeout_add(POLL_INTERVAL, self.check_updates, self)

    def image_press_cb(self, img, event, data):
        if event.button == 1:
            if not self.thread:
                self.thread = threading.Thread(target=self.run_red_carpet)
                self.thread.start()

    def run_red_carpet(self):
        os.system('red-carpet')
        gtk.idle_add(self.check_updates_idle, self)
        self.thread = None

    def check_updates_idle(self, icon):
        self.check_updates(icon)
        return gtk.FALSE

    def check_updates(self, icon):
        def query_finished_cb(worker, icon):
            if not worker.is_cancelled():
                try:
                    packages = worker.get_result()
                except ximian_xmlrpclib.Fault, f:
                    packages = []
                    print 'Failed to get available updates: ' + str(f)
                else:
                    max_importance = 10
                    importance_str = ""
                    
                    for (old_pkg, new_pkg, history) in packages:
                        if new_pkg.has_key('importance_num') and new_pkg['importance_num'] < max_importance:
                            max_importance = new_pkg['importance_num']
                            importance_str = new_pkg['importance_str']
                            
                if max_importance < 10:
                    update_str = ''

                    if importance_str == 'necessary':
                        self.image.set_from_pixbuf(self.high_priority_icon)
                        update_str = 'Urgent updates available'
                    else:
                        self.image.set_from_pixbuf(self.low_priority_icon)
                        update_str = 'Updates available'

                    self.box.show ()
                    self.tooltips.set_tip(self.box, update_str)
                else:
                    self.box.hide ()
                
        server = rcd_util.get_server_proxy()
        
        self.__worker = server.rcd.packsys.get_updates()
        self.__worker_handler_id = self.__worker.connect("ready",
                                                         query_finished_cb,
                                                         self)

        return gtk.TRUE

        
                

def get_title():
    return red_name + " " + red_version

def get_pid_path():
    return "%s/.red-carpet-icon%s" % (os.getenv('HOME'), os.getenv('DISPLAY'))

def get_pid_file(mode='r'):
    return file(get_pid_path(), mode)

def check_running():
    try:
        f = get_pid_file()
    except Exception, e:
        return 0

    pid = int(f.read())
    f.close()

    try:
        os.kill(pid, 0)
    except OSError, e:
        if e.errno == 3:
            return 0 #that process isn't running now

    return 1

def write_pid():
    f = get_pid_file('w+')
    f.write(str(os.getpid()))
    f.close()

def delete_pid():
    try:
        path = get_pid_path()
        os.unlink(path)
    except Exception, e:
        pass

###
### main
###
   
def main(version):
    if check_running():
        import gtk
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_WARNING,
                                   gtk.BUTTONS_OK,
                                   _("There appears to be a Red Carpet "
                                     "update icon already running.  Exiting."))
        dialog.run()
        dialog.destroy()
        return 1

    write_pid()

    global red_version
    red_version = version
    
    print "Red Carpet Notification Tray Icon %s" % version
    print "Copyright (C) 2002-2004 Novell, Inc."
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
        import red_main
        red_main.red_name = red_name
        red_main.red_version = red_version
        server, local = red_connection.connect_from_window()

    if server is None:
        sys.exit(1)

    rcd_util.register_server(server, local)

    import gtk
    icon = UpdateIcon()
    icon.show_all()

    gtk.main()

    delete_pid()

    global red_running
    red_running = 0

    # This will terminate all our child threads without joining
    os._exit(0)
    


