import pandas as pd
from multiprocessing import Pipe, Process, connection
import time

def smart_print(message, a_pipe = None):
    if __name__ == "__main__":
        print(message)
    else:
        a_pipe.send(message)

def review_with_user(var_names, dataset, a_pipe = None):
    affirmed = []
    review_message = 'Yes or no?'

    if __name__ == "__main__":
        review_response = input(review_message)
    else:
        smart_print(review_message, a_pipe)
        #while a_pipe.poll() != True:
        #    time.sleep(0.1)

        connection.wait([a_pipe], timeout=None)

        review_response = a_pipe.recv()

    if review_response in ['Yes', 'yes']:
        for v in dataset.columns:
            smart_print(dataset[v].dropna(), a_pipe)
            if __name__ == "__main__":
                local_response = input(review_message)
            else:
                connection.wait([a_pipe], timeout=None)
                local_response = a_pipe.recv()
            if local_response in ['Yes', 'yes']:
                affirmed.append(v)

        smart_print(affirmed, a_pipe)

if __name__ == "__main__":
    var_names = ['var1', 'var2']
    df = pd.read_csv('dummy.csv')
    review_with_user(var_names, df)