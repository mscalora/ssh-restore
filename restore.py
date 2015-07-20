#! /usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess, re, sys, os
from time import sleep, time

server = sys.argv[1] if len(sys.argv) > 1 else u'backup'
sshdir = sys.argv[2] if len(sys.argv) > 2 else u'backup'

class bcolors:
    BLACK      = '\033[30m'
    RED        = '\033[31m'
    GREEN      = '\033[32m'
    YELLOW     = '\033[33m'
    BLUE       = '\033[34m'
    MAGENTA    = '\033[35m'
    CYAN       = '\033[36m'
    WHITE      = '\033[37m'

    IBLACK     = '\033[90m'
    IRED       = '\033[91m'
    IGREEN     = '\033[92m'
    IYELLOW    = '\033[93m'
    IBLUE      = '\033[94m'
    IMAGENTA   = '\033[95m'
    ICYAN      = '\033[96m'
    IWHITE     = '\033[97m'

    BGBLACK    = '\033[40m'
    BGRED      = '\033[41m'
    BGGREEN    = '\033[42m'
    BGYELLOW   = '\033[43m'
    BGBLUE     = '\033[44m'
    BGMAGENTA  = '\033[45m'
    BGCYAN     = '\033[46m'
    BGWHITE    = '\033[47m'

    IBGBLACK   = '\033[100m'
    IBGRED     = '\033[101m'
    IBGGREEN   = '\033[102m'
    IBGYELLOW  = '\033[103m'
    IBGBLUE    = '\033[104m'
    IBGMAGENTA = '\033[105m'
    IBGCYAN    = '\033[106m'
    IBGWHITE   = '\033[107m'

    ENDC      = '\033[0m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'

    SAVE      = '\033[s'
    RECALL    = '\033[s'

    UP        = '\033[%dA'
    DOWN      = '\033[%dB'
    RIGHT     = '\033[%dC'
    LEFT      = '\033[%dD'
    CLEAREOL  = '\033[K'
    CLEARSCR  = '\033[2J'
    COL0      = '\033[0G'

    NORMAL    = '\033[0m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'
    BLINK     = '\033[5m'
    REVERSE   = '\033[7m'
    INVISIBLE = '\033[8m'

cmd = u'ssh %s \'ls -la --time-style long-iso "%s"\'' % (server, sshdir)
print cmd
try:
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except KeyboardInterrupt, e:
    sys.exit(1)

stdout, stderr = process.communicate()
rc = process.returncode

if rc != 0:
    print "RC: {}".format(rc)
if stderr != '':
    print "STDERR: %s" % stderr

lines = stdout.split("\n")

entries = []

for line in lines:

    m = re.match(ur'^([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +([^ ]+) +(.+)$', line)

    if m:
        entries.append(m.groups())

files = [entry for entry in entries if entry[0][0]=='-']
dirs = [entry for entry in entries if entry[0][0]=='d']
dest = os.path.realpath(os.path.curdir)

fs = list(reversed(sorted(files, key=lambda x : (x[5]+x[6]))))

page = 0

def getchfunc():
    import termios
    import sys, tty
    if sys.stdin.isatty():
        def _getch():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

    else:
        def _getch():
            return sys.stdin.read(1)
    return _getch

def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

getch = getchfunc()
s = 0
k = ''

def subColor(target_re, s, replace=ur'\1',color=bcolors.MAGENTA, reset=bcolors.ENDC):
    return re.sub(target_re, color + replace + reset, s)

pages = (len(fs)+9) / 10

while True:

    while True:

        print "\n\n  Page %d of %d   Key: %s %s" % (page+1, pages, k, bcolors.CLEAREOL)
        sys.stdout.write(bcolors.CLEAREOL+"\n")
        sys.stdout.write(bcolors.CLEAREOL+"\n")

        width = max([len(f[7]) for f in fs[page*10:page*10+10]])+1

        file_list = fs[page*10:page*10+10]
        file_len = len(file_list)
        s = file_len-1 if s >= file_len else s
        for i, f in enumerate(file_list):

            sel = i == s
            colors = {
                "fg": bcolors.BLACK + bcolors.BOLD if sel else '',
                "bg": bcolors.IBGYELLOW if sel else '',
                "hifg": bcolors.IRED + bcolors.BOLD if sel else bcolors.RED,
                "hibg": bcolors.IBGYELLOW if sel else '',
                "reset": bcolors.ENDC + bcolors.CLEAREOL
            }

            file_name = f[7]
            padded_name = (file_name + " " * width)[0:width]
            padded_size = (" "*7+sizeof_fmt(int(f[4])))[-7:]
            dest_path = os.path.join(dest,file_name)

            exists = "•" if os.path.exists(dest_path) else " "
            line = "  {hifg}{hibg} %d  %s {reset}{fg}{bg} %s %s  %s  %s{reset} " % (i, exists, f[5], f[6], padded_size, padded_name)
            print line.format(**colors)

        if len(file_list) < 10:
            for i in range(0,10-len(file_list)):
                print bcolors.CLEAREOL

        print "\n\n" + bcolors.UP % 2

        more_pages = page*10+10 < len(fs)

        ops = ["Quit"]
        ops += ["Next"] if more_pages else []
        ops += ["Prev"] if page > 0 else []
        upper = '' if len(file_list) == 1 else '-'+"-0123456789"[len(file_list)]
        part1 = "Download 0%s or %s" % (upper, " or ".join(ops))

        part1 = re.sub(ur"([0-9QPN])",bcolors.MAGENTA + ur'\1' + bcolors.ENDC, part1) + " "

        part2 = "  Destination: %s%s %s      "
        dist = len(part2) - 6 + len(dest)
        part2 = part2 % (bcolors.CYAN, dest, bcolors.ENDC + bcolors.CLEAREOL)

        sys.stdout.write(part1 + part2 + bcolors.LEFT % dist)

        c = getch()
        k = ord(c)
        download = False
        up_count = 5 + 10 + 1

        if c == 'q' or c == 'Q':
            sys.stdout.write(bcolors.COL0 + bcolors.CLEAREOL + bcolors.UP % up_count)
            print ""
            sys.exit(0)
        elif c >= '0' and c <= '9':
            sys.stdout.write(bcolors.COL0 + bcolors.CLEAREOL + bcolors.UP % up_count)
            s = int(c)
            download = True
            break
        elif k == 13:
            sys.stdout.write(bcolors.COL0 + bcolors.CLEAREOL + bcolors.UP % up_count)
            download = True
            break
        else:
            sys.stdout.write(bcolors.UP % up_count)
            if more_pages and (c == 'n' or c == 'N'):
                page += 1
            elif page > 0 and (c == 'p' or c == 'P'):
                page -= 1
            elif k == 65 and s > 0:
                s -= 1
            elif k == 65 and page > 0:
                s = 9
                page -= 1
            elif k == 66 and s < 9 and s < len(file_list)-1:
                s += 1
            elif k == 66 and s == 9 and more_pages:
                s = 0
                page += 1

    if download:
        for i in range(0, up_count):
            print bcolors.CLEAREOL
        sys.stdout.write(bcolors.UP % up_count)

        sys.stdout.write(bcolors.CLEAREOL+"\n")
        sys.stdout.write(bcolors.CLEAREOL+"\n")
        sys.stdout.write(bcolors.CLEAREOL+"\n")

        file_info = file_list[s]
        file_name = file_info[7]
        src_path = os.path.join(sshdir,file_name)
        dest_path = os.path.join(dest,file_name)

        print "     Remote:"
        print "         Server: %s%s%s" % (bcolors.RED, server, bcolors.ENDC + bcolors.CLEAREOL)
        print "         Folder: %s%s%s" % (bcolors.RED, sshdir, bcolors.ENDC + bcolors.CLEAREOL)
        print "         File  : %s%s%s" % (bcolors.RED, file_name, bcolors.ENDC + bcolors.CLEAREOL)
        print "     " + bcolors.CLEAREOL
        print "     Local:" + bcolors.CLEAREOL
        print "         Folder: %s%s%s" % (bcolors.RED, dest, bcolors.ENDC + bcolors.CLEAREOL)
        print "     " + bcolors.CLEAREOL
        print("     Overwritting Existing File!" if os.path.exists(os.path.join(dest,file_name)) else "") + bcolors.CLEAREOL
        print "     " + bcolors.CLEAREOL
        sys.stdout.write(subColor(ur'([0-9A-Z])',"     Yes or Cancel or Return to list? "))

        c = ' '
        while c not in "rRyYcC":
            c = getch()

        print "\n"

        if c == 'r' or c == 'R':
            sys.stdout.write(bcolors.COL0 + bcolors.CLEAREOL + bcolors.UP % (up_count - 1))
            continue

        break

if download and (c == 'y' or c == 'Y'):
    print ""
    cmd = u'scp -p %s:"%s" "%s"' % (server, src_path, dest_path)
    print cmd
    stdout = subprocess.Popen(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin)

    # start = time()
    # max_wait = 30.0
    # w = 60
    # pos = 0
    # full = int(file_info[4])
    # seg = full / w
    # cur = 0
    #
    # while (time() - start) < max_wait and cur < full:
    #     if os.path.exists(dest_path):
    #         cur = os.path.getsize(dest_path)
    #         new_pos = int(round(cur / seg))
    #         if new_pos > pos:
    #             sys.stdout.write(u"•" * (new_pos-pos))
    #             pos = new_pos
    #
    #     sleep(0.1)
    print ""

else:
    print ""
