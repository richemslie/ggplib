import os

def path_back(filename, back_count=0):
    ' return the directory/path by going back_count times backwards.  Like cd ../../../../ '
    path = os.path.dirname(filename)
    for ii in range(back_count):
        path = os.path.dirname(path)
    return path
