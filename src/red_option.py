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

import getopt, string, sys

from red_gettext import _
import rcd_util

opt_table = [
    ["l", "local",    "",            _("Connect to a locally running daemon")],
    ["h", "host",     _("hostname"), _("Contact daemon on specified host")],
    ["U", "user",     _("username"), _("Specify user name")],
    ["P", "password", _("password"), _("Specify password")],
    ["",  "version",  "",            _("Print client version and exit")],
    ["?", "help",     "",            _("Get usage information")]
]

def process_argv(argv):
    ###
    ### Expand our synthetic args.
    ### Then compile our list of arguments into something that getopt can
    ### understand.  Finally, call getopt on argv and massage the results
    ### in something easy-to-use.
    ###

    short_opt_getopt = ""
    long_opt_getopt  = []

    short2long_dict = {}

    for o in opt_table:

        short_opt = o[0]
        long_opt  = o[1]
        opt_desc  = o[2]

        if short_opt:

            if short2long_dict.has_key(short_opt):
                print "Short option collision!"
                print "-" + short_opt + ", --" + long_opt
                print "  vs."
                print "-" + short_opt + ", --" + short2long_dict[short_opt]
                sys.exit(1)

            short2long_dict[short_opt] = long_opt
            short_opt_getopt = short_opt_getopt + short_opt
            if opt_desc:
                short_opt_getopt = short_opt_getopt + ":"

        if opt_desc:
            long_opt_getopt.append(long_opt + "=")
        else:
            long_opt_getopt.append(long_opt)

    try:
        optlist, args = getopt.getopt(argv, short_opt_getopt, long_opt_getopt)
    except getopt.error:
        did_something = 0
        for a in argv:
            if string.find(a,"--") == 0:
                if not a[2:] in map(lambda x:x[1], opt_table):
                    print "Invalid argument " + a
                    did_something = 1
            elif string.find(a, "-") == 0:
                if not a[1:] in map(lambda x:x[0], opt_table):
                    print "Invalid argument " + a
                    did_something = 1

        # Just in case something strange went wrong and we weren't
        # able to describe quite why the options parsing failed,
        # we print a catch-all error message.
        if not did_something:
            print "Invalid arguments"

        usage()

        sys.exit(1)

    ###
    ### Walk through our list of options and replace short options with the
    ### corresponding long option.
    ###

    i = 0
    while i < len(optlist):
        key = optlist[i][0]
        if key[0:2] != "--":
            optlist[i] = ("--" + short2long_dict[key[1:]], optlist[i][1])
        i = i + 1


    ###
    ### Store our options in a dictionary
    ###

    opt_dict = {}

    for key, value in optlist:
        opt_dict[key[2:]] = value


    return opt_dict, args

def usage():
    print _("Usage: %s <options> ...") % sys.argv[0]
    print
    print _("The following options are understood:")

    opt_list = []

    for r in opt_table:
        opt = "--" + r[1]
        if r[0]:
            opt = "-" + r[0] + ", " + opt
        if r[2]:
            opt = opt + "=<" + r[2] + ">"

        opt_list.append([opt + "  ", r[3]])

    # By appending [0,0], we insure that this will work even if
    # opt_list is empty (which it never should be)
    max_len = apply(max, map(lambda x:len(x[0]), opt_list) + [0,0])

    for opt, desc_str in opt_list:

        if 79 - max_len > 10:
            desc = rcd_util.linebreak(desc_str, 79 - max_len)
        else:
            desc = [desc_str]

        desc_first = desc.pop(0)
        print string.ljust(opt, max_len) + desc_first
        for d in desc:
            print " " * max_len + d

