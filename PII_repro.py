from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter import ttk
from multiprocessing import Process, Pipe
import other.py

class GUI:
    def __init__(self, master):
        self.master = master

def tkinter_display(the_message):
    ttk.Label(frame, text=the_message, style='my.TLabel').pack()

def select():

    path = askopenfilename()

    tkinter_display('The script is running...')

    if __name__ == '__main__':

        side1, side2 = Pipe()

        tkinter_functions_conn.send(path)

        p_import = Process(target=other.dummy, args=(side2,))
        p_import.start()


if __name__ == '__main__':

    root = Tk() 
    my_gui = GUI(root)

    # Styles
    root.style = ttk.Style()
    root.style.configure('my.TButton')
    root.style.configure('my.TLabel')

    # Display
    frame = Frame()
    frame.pack()

    ttk.Button(frame, text="Select", command=file_select, style='my.TButton').pack()

    # Listener
    root.mainloop()  # constantly looping event listener