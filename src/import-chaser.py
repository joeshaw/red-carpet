#!/usr/bin/env python

import string, sys, os.path, re

modules = {}
pattern = re.compile("^\s*import\s+")

def chase_file(name):
    fd = open(name)
    modules[name] = 1
    for line in fd.readlines():
        match = pattern.search(line)
        if match:
            a, b = match.span(0)
            for mod in string.split(line[b:], ","):
                mod = string.strip(mod) + ".py"
                if os.path.isfile(mod) and not modules.get(mod):
                    chase_file(mod)
        
for name in sys.argv[1:]:
    chase_file(name)

module_names = modules.keys()
module_names.sort()

for name in module_names:
    print "%-40s\\" % name
