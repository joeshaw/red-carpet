#!/usr/bin/env python

import string, sys, os, os.path, re

pattern = re.compile("^\s*import\s+")


def check_file(name):
    unseen_modules = {}
    fd = open(name)
    for line in fd.readlines():
        i = string.find(line, "#")
        if i >= 0:
            line = line[:i]
        match = pattern.search(line)
        if match:
            a, b = match.span(0)
            for mod in string.split(line[b:], ","):
                mod = string.strip(mod)
                unseen_modules[mod] = re.compile("%s\." % mod)
        else:
            for mod, mod_pattern in unseen_modules.items():
                if mod_pattern.search(line):
                    del unseen_modules[mod]

    return unseen_modules.keys()

for name in sys.argv[1:]:
    unseen = check_file(name)
    if unseen:
        print "%s:" % name
        for u in unseen:
            print "   %s" % u
        print

    
