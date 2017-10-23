from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter import ttk
from multiprocessing import Process, Pipe, connection
import pandas as pd
import temp_processor
import time

class GUI:
    def __init__(self, master):
        self.master = master

def gui_input(message, a_pipe = None):
    def input_done(event=None):
        entry.pack_forget()
        input_label.pack_forget()
        submit_button.pack_forget()
        a_pipe.send(entry.get())
        next_one(a_pipe)

    entry = Entry(frame)
    input_label = ttk.Label(frame, text=message)
    entry.bind("<Return>", input_done)
    submit_button = ttk.Button(frame, text="Submit", command=input_done)
    input_label.pack()
    entry.pack()
    submit_button.pack()

def file_select():
    dataset_path = askopenfilename()

    if __name__ == '__main__':
        pipe1, pipe2 = Pipe()

        some_vars = ['a var', 'another var']
        a_df = pd.read_csv(dataset_path)

        p_review = Process(target=Processor_child.review_with_user, args=(some_vars, a_df, pipe2))
        p_review.start()

        gui_input(pipe1.recv(), pipe1)

        #time.sleep(1)
def next_one(pipe1):
    connection.wait([pipe1], timeout=None)
    #while pipe1.poll() != True:
    #    time.sleep(0.1)

    gui_input(pipe1.recv(), pipe1)

if __name__ == '__main__':
    root = Tk()
    my_gui = GUI(root)
    root.style = ttk.Style()
    root.style.configure('my.TButton')
    root.style.configure('my.TLabel')

    canvas = Canvas(root)
    frame = Frame(canvas)
    frame.place()
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((45,50), window=frame, anchor="nw")

    ttk.Button(frame, text="Select", command=file_select).pack()

    root.mainloop()