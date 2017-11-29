' world simplest store '

import os
import glob
import json
import tempfile

from ggplib.util.util import path_back

# from https://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-from-json

def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )

def _byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data


class StoreException(Exception):
    pass


class FileStore:
    ' must exist '
    def __init__(self, path):
        self.path = os.path.abspath(path)


class DirectoryStore:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.cached = {}

    def get_directory(self, name, create=False, reenterant=False):
        if name in self.cached:
            if not isinstance(self.cached[name], DirectoryStore):
                raise StoreException("@ %s, get_directory(%s) exist, but not a directory" % (self, name))
            return self.cached[name]

        dir_path = os.path.join(self.path, name)
        if os.path.exists(dir_path):
            if not os.path.isdir(dir_path):
                raise StoreException("@ %s, get_directory(%s) exist, but not a directory" % (self, name))

            dir_store = DirectoryStore(dir_path)
            self.cached[name] = dir_store
            return dir_store

        if not create:
            raise StoreException("@ %s, get_directory(%s) does not exist" % (self, name))

        # potential race condition here...
        try:
            os.mkdir(dir_path)
        except OSError as exc:
            # ignore it first time around
            if reenterant:
                msg = "@ %s, get_directory(%s).  os.mkdir() is failing for some weird reason: %s" % (self, name, exc)
                raise StoreException(msg)

        return self.get_directory(name, reenterant=True)

    def listdir(self, pattern="*"):
         p = os.path.join(self.path, pattern)

         # glob returns list of strings.. so we will replace
         return [c.replace(self.path + os.path.sep, "") for c in glob.glob(p)]

    def file_exists(self, name):
        if name in self.cached:
            if not isinstance(self.cached[name], FileStore):
                raise StoreException("@ %s, get_file(%s) exists, but not a file" % (self, name))
            return True

        path = os.path.join(self.path, name)
        if os.path.exists(path) and os.path.isfile(path):
            #self.cached[name] = FileStore(path)
            return True

        return False

    def load_contents(self, filename):
        path = os.path.join(self.path, filename)
        return open(path).read()

    def load_json(self, filename):
        return json_loads_byteified(self.load_contents(filename))

    def save_contents(self, filename, contents, overwrite=False):
        if not overwrite:
            if self.file_exists(filename):
                raise StoreException("@ %s, Cannot overwrite filename %s" % (self, filename))

        fd, tmppath = tempfile.mkstemp(dir=self.path)
        dst_path = os.path.join(self.path, filename)

        with os.fdopen(fd, 'w') as f:
            f.write(contents)
            f.flush()
            os.fsync(fd)
            os.rename(tmppath, dst_path)

    def save_json(self, filename, context):
        buf = json.dumps(context)
        self.save_contents(filename, buf)

    def __str__(self):
        return "DirectoryStore('%s')" % self.path

    __repr__ = __str__


root = None
def get_root():
    global root
    if root is None:
        root_directory = os.path.join(path_back(__file__, 3), "data")
        root = DirectoryStore(root_directory)
    return root
