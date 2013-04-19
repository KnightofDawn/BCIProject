""" Objects and methods for serializing and writing objects to a file without blocking.
    You should instantiate the QuickSave object somewhere where blocking is OK.
"""
import time
import cPickle as pickle
import threading

class SaveException(Exception):
    pass



class QuickSave(object):
    def __init__(self, filename):
        self.fh = open(filename, 'wb')
        self.saveQueue = []
        self.queueLength = 0
        self.queueLock = threading.Lock()
        self.finishWriting = False

        # start the file write thread

        threading.Thread(target=self._saveThread, name="Object Serializer, file {}".format(self.fh.name)).start()



    def _saveThread(self):
        while True:
            if self.queueLength == 0:
                continue
            with self.queueLock:
                obj = self.saveQueue.pop(0)
                self.queueLength -= 1
            pickle.dump(obj, file=self.fh)
            if (self.queueLength == 0) and self.finishWriting:
                print ">> closing thread"
                self.fh.close()
                break

    def saveObject(self, obj):
        """ Appends an object for saving to file
        """

        if not self.finishWriting:
            with self.queueLock:
                self.saveQueue.append(obj)
                self.queueLength += 1
        else:
            raise SaveException("Cannot save, finish method called")


    def finish(self):

        """ Finalize the saveQueue
        """
        self.finishWriting = True


def loadListFromFile(filename):

    """ Loads the list of objects stored in a pickled file
    """
    objList = []
    fh = open(filename, 'r')
    while True:
        try:
            objList.append(pickle.load(fh))
        except (EOFError, pickle.UnpicklingError):
            break

    fh.close()
    return objList

