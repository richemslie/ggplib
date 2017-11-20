import os
from cffi import FFI
from ggplib import interface

def joins(path, *dirs):
    for d in dirs:
        path = os.path.join(path, d)
    return path

def back(path, depth):
    for i in range(depth):
        path = os.path.dirname(path)
    return path

def get_lib():
    # get the paths
    local_path = joins(back(os.path.abspath(__file__), 2), "cpp")
    ggp_path = joins(back(os.path.abspath(__file__), 4), "src", "cpp")
    def process_line(l):
        # pre-process a line.  Skip any lines with comments.  Replace strings in remap.
        if "//" in l:
            return l
        remap = {
            "StateMachine*" : "void*",
            "PlayerBase*" : "void*",
            "boolean" : "int",
        }

        for k, v in remap.items():
            if k in l:
                l = l.replace(k, v)
                l = l.rstrip()
        return l

    def get_lines(filename):
        # take subset of file (since it is c++, and want only the c portion
        emit = False
        for l in file(filename):
            if "CFFI START INCLUDE" in l:
                emit = True
            elif "CFFI END INCLUDE" in l:
                emit = False
            if emit:
                l = process_line(l)
                if l:
                    yield l

    # get ffi object, and lib object
    ffi = FFI()
    ffi.cdef("\n".join(get_lines(os.path.join(local_path, "interface.h"))))

    return ffi, ffi.verify('#include <interface.h>\n',
                           include_dirs=[local_path],
                           library_dirs=[ggp_path, local_path],
                           libraries=["rt", "ggplib_cpp", "gurgehplayerlib_cpp"])


ffi, lib = get_lib()

def create_gurgeh_cpp_player(sm, our_role_index, *args):
    return interface.CppPlayerWrapper(lib.Player__createGurgehPlayer(sm.c_statemachine,
                                                                     our_role_index,
                                                                     *args))
