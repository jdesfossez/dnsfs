#/usr/bin/env python
#
# DnsFS.py
# Need python-fuse bindings
# usage: ./DnsFS.py <mountpoint>
# unmount with fusermount -u <mountpoint>
#
  
import stat
import errno
import fuse
from time import time
from subprocess import *

import sys
from dnsparser import *
import os

fuse.fuse_python_api = (0, 2)

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = stat.S_IFDIR | 0755
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 2
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 4096
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0

class DnsFS(fuse.Fuse):
    def __init__(self, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)
        self.dnsUtils = DnsFsUtils()
        print self.dnsUtils.getFoldersName(self.dnsUtils.getSubFolders("", TLD))
        print 'Init complete.'

    def getattr(self, path):
        st = MyStat()
        pe = path.split('/')[1:]

        st.st_atime = int(time())
        st.st_mtime = st.st_atime
        st.st_ctime = st.st_atime
        print "getattr", path
        if path == '/':
            pass
        elif self.dnsUtils.getFolderPath(path) != False:
            pass
        elif self.dnsUtils.getFilePath(path) != False:
            filePath = self.dnsUtils.getFilePath(path)
#            print "raw mode", int(self.dnsUtils.getFileMode(self.dnsUtils.getAnswer(filePath)))
#            st.st_mode = stat.S_IFREG | int(self.dnsUtils.getFileMode(self.dnsUtils.getAnswer(filePath)))
#            print "mode", st.st_mode
            st.st_mode = stat.S_IFREG | 0666
            st.st_uid = int(self.dnsUtils.getFileUid(self.dnsUtils.getAnswer(filePath)))
            st.st_gid = int(self.dnsUtils.getFileGid(self.dnsUtils.getAnswer(filePath)))
            st.st_nlink = 1
        elif self.dnsUtils.isNewFile(path):
            st.st_mode = stat.S_IFREG | 0666
            st.st_uid = os.getuid()
            st.st_gid = os.getgid()
            st.st_nlink = 1
            return st
        else:
            return -errno.ENOENT
        return st

    def readdir(self, path, offset):
        dirents = [ '.', '..' ]
        if path == '/':
            dirents.extend(self.dnsUtils.getFoldersName(self.dnsUtils.getSubFolders("", TLD)))
            dirents.extend(self.dnsUtils.getFilesName(self.dnsUtils.getFiles("")))
        else:
            p = self.dnsUtils.getFolderPath(path)
            if p != False:
                dirents.extend(self.dnsUtils.getFoldersName(self.dnsUtils.getSubFolders(p, p + TLD)))
            dirents.extend(self.dnsUtils.getFilesName(self.dnsUtils.getFiles(p)))
        for r in dirents:
            yield fuse.Direntry(r)

    def mknod(self, path, mode, dev):
        print "mknod %s %s %s" % (path, mode, dev)
        dirname = path[path.rfind('/') + 1:]
        folder = path[:-len(dirname)]
        print "filename", dirname
        print "in folder", folder
        self.dnsUtils.mknod(folder, dirname, mode, os.getuid(), os.getgid())
        self.dnsUtils.loadBD()
        return 0
#        pe = path.split('/')[1:]        # Path elements 0 = printer 1 = file
#        self.printers[pe[0]].append(pe[1])
#        self.files[pe[1]] = ""
#        self.lastfiles[pe[1]] = ""
#        return 0
#
#    def unlink(self, path):
#        pe = path.split('/')[1:]        # Path elements 0 = printer 1 = file
#        self.printers[pe[0]].remove(pe[1])
#        del(self.files[pe[1]])
#        del(self.lastfiles[pe[1]])
#        return 0

    def read(self, path, size, offset):
        dnsPath = self.dnsUtils.getFilePath(path)
        ans = self.dnsUtils.getAnswer(dnsPath)
        data = self.dnsUtils.getFileData(ans)
        return str(data)

    def write(self, path, buf, offset):
        print "WRITE", path, buf, offset
        return 0
#        pe = path.split('/')[1:]        # Path elements 0 = printer 1 = file
#        self.files[pe[1]] += buf
#        return len(buf)
#
#    def release(self, path, flags):
#        pe = path.split('/')[1:]        # Path elements 0 = printer 1 = file
#        if len(self.files[pe[1]]) > 0:
#            lpr = Popen(['lpr -P ' + pe[0]], shell=True, stdin=PIPE)
#            lpr.communicate(input=self.files[pe[1]])
#            lpr.wait()
#            self.lastfiles[pe[1]] = self.files[pe[1]]
#            self.files[pe[1]] = ""      # Clear out string
#        return 0
#
#    def open(self, path, flags):
#        return 0
#
#    def truncate(self, path, size):
#        return 0
#
#    def utime(self, path, times):
#        return 0

    def mkdir(self, path, mode):
        print "mkdiring %s %s" % (path, mode)
        dirname = path[path.rfind('/') + 1:]
        folder = path[:-len(dirname)]
        print "dirname", dirname
        print "in folder", folder
        self.dnsUtils.mkdir(folder, dirname, mode, os.getuid(), os.getgid())
        self.dnsUtils.loadBD()
        return 0

#    def rmdir(self, path):
#        return 0
#
#    def rename(self, pathfrom, pathto):
#        return 0
#
#    def fsync(self, path, isfsyncfile):
#        return 0

def main():
    usage="""
        DnsFS: A filesystem to allow printing for applications that can
                only print to file.
    """ + fuse.Fuse.fusage

    server = DnsFS(version="%prog " + fuse.__version__,
                    usage=usage, dash_s_do='setsingle')
    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()

