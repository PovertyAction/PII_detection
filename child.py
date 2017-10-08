import time

def main(queue=None):
    for i in range(10):
        # do a computation
        result = i
        if queue:
            # Put a result in the queue for the parent to get
            queue.put(result)   
        time.sleep(.5)

if __name__=='__main__':  
    # We reach here only when child.py is run as a script 
    # (as opposed to child being imported as a module).
    main()  