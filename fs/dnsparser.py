#!/usr/bin/python

import os

FILE = "datas"
TLD = "ZONE"

class DnsFsUtils:
    def __init__(self):
        self.loadBD()

    def loadBD(self):
        self.bd = []
        f = open(FILE, 'r')
        lines = f.readlines()
        f.close()
        for line in lines:
            if line[0] in ["#", "\n"]:
                continue
            else:
                self.bd.append(line[:-1].split('#'))

    def getAnswer(self, request):
        for req in self.bd:
            if req[0] == request:
                return req[1]
        return False

    # Folders
    def getFolderMode(self, response):
        return response.split(':')[0]

    def getFolderUid(self, response):
        return response.split(':')[1]

    def getFolderGid(self, response):
        return response.split(':')[2]

    def getFolderName(self, response):
        return response.split(':')[3]

    def getFoldersName(self, list):
        # [['0.ZONE', '755:0:0:a::'], ['1.ZONE', '755:0:0:b::']]
        names = []
        for i in list:
            names.append(self.getFolderName(i[1]))
        return names

    # Files
    def getFileMode(self, response):
        return response.split(':')[0]

    def getFileUid(self, response):
        return response.split(':')[1]

    def getFileGid(self, response):
        return response.split(':')[2]

    def getFileName(self, response):
        return response.split(':')[3]

    def getFileData(self, response):
        tab = response.split(':')[4:]
        str = ""
        for i in tab:
            if len(i) == 2:
                str = str + chr(int(i, 16))
            elif len(i) == 4:
                str = str + chr(int(i[0:2], 16)) + chr(int(i[2:4], 16))
            else:
                pass
        return str

    def getFilesName(self, list):
        names = []
        for i in list:
            names.append(self.getFileName(i[1]))
        return names

    def getSubFolders(self, root, fullPath):
        path = fullPath[len(root):]
        id = 0
        list = []
        req = root + str(id) + "." + path
        res = self.getAnswer(req)
        while res != False:
            list.append([req, res])
            id = id + 1
            req = root + str(id) + "." + path
            res = self.getAnswer(req)
        return list

    def getFiles(self, folder):
        id = 0
        list = []
        if folder == False:
            return False
        req = folder + "ffff." + str(id) + "." + TLD
        res = self.getAnswer(req)
        while res != False:
            list.append([req, res])
            id = id + 1
            req = folder + "ffff." + str(id) + "." + TLD
            res = self.getAnswer(req)
        return list

    def isFile(self, path):
        try:
            path.split('.').index('ffff')
            return True
        except ValueError:
            return False

    def getFolderPath(self, path):
        """Find the name for a path (ex : /a/b --> 0.1.TLD)"""
        root = ""
        id = 0
        next = False

        if path == '/':
            return ""
        # ['', 'a', 'b']
        hierarchy = path.split('/')
        try:
            # ['a', 'b']
            while True:
                hierarchy.remove('')
        except ValueError:
            pass

        while True:
            subs = self.getSubFolders(root, root+TLD)
            next = False
            for sub in subs:
                name = self.getFolderName(sub[1])
                try:
                    if name == hierarchy[id]:
                        root = sub[0][:-len(TLD)]
                        id = id + 1
                        next = True
                        if id == len(hierarchy):
                            return root
                except IndexError:
                    return False
            if not next:
                return False

    def getFilePath(self, path):
        # path = /a/b/cc
        # get folder path : /a/b -> 0.1.TLD
        # find file path in that folder : 0.1.ffff.0.TLD

        print "getFilePath", path
        filename = path[path.rfind('/') + 1:]
        folder = path[:path.rfind('/')+1]
        fpath = self.getFolderPath(folder)
        print filename, folder, fpath
        if fpath == False:
            return False
        files = self.getFiles(fpath)
        for file in files:
            if self.getFileName(file[1]) == filename:
                return file[0]
        return False

    def findNextFolderId(self, folder):
        """Return the next usable ID for a folder"""
        subs = self.getSubFolders(folder, folder + TLD)
        if len(subs) == 0:
            return 0
        next = int(subs[len(subs)-1][0][:-len(TLD)-1].split('.')[-1]) + 1
        if next < 0xffff:
            return next
        return False

    def findNextFileId(self, folder):
        """Return the next usable ID for a file"""
        subs = self.getFiles(folder)
        if len(subs) == 0:
            return 0
        print subs
        next = int(subs[len(subs)-1][0][:-len(TLD)-1].split('.')[-1]) + 1
        if next < 0xffff:
            return next
        return False

    def mkdir(self, folder, dirname, mode, uid, gid):
        print "MKDIR : ", folder, dirname, mode, uid, gid
        if folder == '/':
            rootpath = ""
        else:
            rootpath = self.getFolderPath(folder)
        next = self.findNextFolderId(rootpath)
        req = "%s%s.%s" % (rootpath, next, TLD)
        resp = "%s:%s:%s:%s::" % (mode, uid, gid, dirname)
        f = open(FILE, 'a')
        f.write("%s#%s\n" % (req, resp))
        f.close()

    def mknod(self, folder, filename, mode, uid, gid):
        print "MKNOD : ", folder, filename, mode, uid, gid
        if folder == '/':
            rootpath = ""
        else:
            rootpath = self.getFolderPath(folder)
        next = self.findNextFileId(rootpath)
        req = "%sffff.%s.%s" % (rootpath, next, TLD)
        resp = "%s:%s:%s:%s::aa" % (mode, uid, gid, filename)
        print ("%s#%s\n" % (req, resp))
        # write tmp file
        f = open('/tmp/'+filename, 'w')
        f.write(' ')
        f.close()
#        f.write("%s#%s\n" % (req, resp))
#        f.close()

    def isNewFile(self, path):
        name = '/tmp/' + path[path.rfind('/') + 1:]
        print "isNewFile", name
        try:
            os.stat(name)
            os.remove(name)
            return True
        except OSError:
            return False


if __name__ == "__main__":
    a = DnsFsUtils()
    #print getFolderName("755:0:0:acc::")
    print "root"
    print a.getSubFolders("", TLD)
    print a.getFoldersName(a.getSubFolders("", TLD))
    print "sub"
    print a.getSubFolders("1.", "1.ZONE")
    print "files"
    print a.getFiles("1.2.")

    print "folder path"
    p = a.getFolderPath("/a/c")
    print p
    print a.getSubFolders(p, p+TLD)

    print "file path"
    print a.getFilePath("/a/ca")

    print "next folder"
    print a.findNextFolderId("1.")
    print a.findNextFolderId("")


    print "file ID"
    print a.findNextFileId("2.")

    print "get Files in root"
    print a.getFiles("")

    print "file path"
    print a.getFilePath("/kkk")
    print "answer"
    print a.getAnswer(a.getFilePath("/kkk"))


