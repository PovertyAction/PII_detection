import multiprocessing as mp
import child

if __name__ == '__main__':
    queue = mp.Queue()
    proc = mp.Process(target=child.main, args=(queue,))
    proc.daemon = True  
    # This launches the child process, calling child.main()
    proc.start()         
    for i in range(10):
        result = queue.get()  # Get results from child.main
        print(result)