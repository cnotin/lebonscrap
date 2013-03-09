import threading
import Queue


class Job():
    def __init__(self, function, arg):
        self.function = function
        self.arg = arg

    def do(self):
        return self.function(self.arg)


class Worker(threading.Thread):
    """Threaded File Downloader"""

    #----------------------------------------------------------------------
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    #----------------------------------------------------------------------
    def run(self):
        while True:
            job = self.queue.get()
            job.do()

            # send a signal to the queue that the job is done
            self.queue.task_done()


class QueueTasks():
    def __init__(self, nb_threads=5):
        self.queue = Queue.Queue()

        #spawn a pool of threads, and pass them queue instance
        for i in range(nb_threads):
            t = Worker(self.queue)
            t.setDaemon(True)
            t.start()


    def add(self, fn, arg):
        self.queue.put(Job(fn, arg))

    def empty(self):
        return self.queue.empty()

    def size(self):
        return self.queue.qsize()
