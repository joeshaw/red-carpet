#!/usr/bin/env python

import string, sys, os, os.path, re

modules = {}
pattern = re.compile("^\s*import\s+")

def chase_file(name):
    fd = open(name)
    modules[name] = 1
    for line in fd.readlines():
        i = string.find(line, "#")
        if i >= 0:
            line = line[:i]
        match = pattern.search(line)
        if match:
            a, b = match.span(0)
            for mod in string.split(line[b:], ","):
                mod = string.strip(mod) + ".py"
                if os.path.isfile(mod) and not modules.get(mod):
                    chase_file(mod)

args = sys.argv[1:]
find_unused = 0
if args and args[0] == "--find-unused":
    find_unused = 1
    args.pop(0)
        
for name in args:
    chase_file(name)

if find_unused:

    for name in os.listdir("."):
        if name[-3:] == ".py" \
               and not modules.get(name) \
               and name != sys.argv[0]: # don't report ourselves as unused
            print name

else:

    module_names = modules.keys()
    module_names.sort()

    for name in module_names:
        print "%-40s\\" % name
