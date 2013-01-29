import threading
import Queue

class Job():
    def __init__(self, function, arg):
        self.function=function
        self.arg=arg

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


class QueueTasks(threading.Thread):
    def __init__(self, nb_threads=2):
        threading.Thread.__init__(self)

        self.queue = Queue.Queue()

        #spawn a pool of threads, and pass them queue instance
        for i in range(nb_threads):
            t = Worker(self.queue)
            t.setDaemon(False)
            t.start()


    def add(self, function,arg):
        self.queue.put(Job(function, arg))

    def run(self)  :
        self.queue.join()

