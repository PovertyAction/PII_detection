# Imports and Set-up
from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter import ttk
import tkinter.scrolledtext as tkst
from nltk.stem.porter import *
import time
from datetime import datetime
from multiprocessing import Process, Pipe
import PII_data_processor

intro_text = "This script is meant to assist in the detection of PII (personally identifiable information) and subsequent removal from a dataset."
intro_text_p2 = "Ensuring the dataset is devoid of PII is ultimately still your responsibility. Be careful with potential identifiers, especially geographic, because they can sometimes be combined with other variables to become identifying."
app_title = "IPA's PII Detector, Cleaner, and Recoder"


class GUI:
    def __init__(self, master):
        self.master = master
        # master.frame(self, borderwidth=4)
        master.title(app_title)
        master.minsize(width=686, height=666)

def input(the_message):
    try:
        ttk.Label(frame, text=the_message, wraplength=546, justify=LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))

        def evaluate(event=None):
            pass

            #if entry.get() in ['y', 'yes']:
            #    return True
            #res.configure(text="Ergebnis: " + )

    except:  # ## add specific Jupyter error here
        pass

    Label(frame, text="Your Expression:").pack()
    entry = Entry(frame)
    entry.bind("<Return>", evaluate)
    if ttk.Button(frame, text="Submit", command=evaluate, style='my.TButton').pack() is True:
        return True
    entry.pack()
    time.sleep(8)
    res = Label(frame)
    res.pack()
    return ('No')


def tkinter_display(the_message):
    the_message = datetime.now().strftime("%H:%M:%S") + '     ' + the_message
    ttk.Label(frame, text=the_message, wraplength=546, justify=LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    frame.update()

def file_select():

    dataset_path = askopenfilename()

    tkinter_display('The script is running...')

    if __name__ == '__main__':

        tkinter_functions_conn, datap_functions_conn = Pipe()
        tkinter_messages_conn, datap_messages_conn = Pipe()

        ### Importing dataset and printing messages ###
        tkinter_functions_conn.send(dataset_path)

        p_import = Process(target=PII_data_processor.import_dataset, args=(datap_functions_conn, datap_messages_conn))
        p_import.start()

        tkinter_display(tkinter_messages_conn.recv())

        import_results = tkinter_functions_conn.recv()  # dataset, dataset_path, label_dict, value_label_dict
        dataset = import_results[0]
        dataset_path = import_results[1]

        
        ### Initialization of lists ###
        p_initialize_vars = Process(target=PII_data_processor.initialize_lists, args=(datap_functions_conn, ))
        p_initialize_vars.start()

        initialize_results = tkinter_functions_conn.recv()
        identified_pii, restricted_vars = initialize_results[0], initialize_results[1]

        ### Stemming of restricted list ###
        p_stemming_rl = Process(target=PII_data_processor.stem_restricted, args=(restricted_vars, datap_functions_conn, datap_messages_conn))
        p_stemming_rl.start()

        tkinter_display(tkinter_messages_conn.recv())

        time.sleep(2)

        stemming_rl_results = tkinter_functions_conn.recv()
        restricted_vars, stemmer = stemming_rl_results[0], stemming_rl_results[1]

        ### Word Match Stemming ###
        p_wordm_stem = Process(target=PII_data_processor.word_match_stemming, args=(identified_pii, restricted_vars, dataset, stemmer, datap_functions_conn, datap_messages_conn))
        p_wordm_stem.start()

        tkinter_display(tkinter_messages_conn.recv())
        tkinter_display(tkinter_messages_conn.recv())
        identified_pii = tkinter_functions_conn.recv()

        ### Fuzzy Partial Stem Match ###
        threshold = 0.75
        p_fpsm = Process(target=PII_data_processor.fuzzy_partial_stem_match, args=(identified_pii, restricted_vars, dataset, stemmer, threshold, datap_functions_conn, datap_messages_conn))
        p_fpsm.start()

        tkinter_display(tkinter_messages_conn.recv())
        tkinter_display(tkinter_messages_conn.recv())
        identified_pii = tkinter_functions_conn.recv()

        ### Unique Entries Detection ###
        min_entries_threshold = 0.5
        p_uniques = Process(target=PII_data_processor.unique_entries, args=(identified_pii, dataset, min_entries_threshold, datap_functions_conn, datap_messages_conn))
        p_uniques.start()

        tkinter_display(tkinter_messages_conn.recv())
        tkinter_display(tkinter_messages_conn.recv())
        identified_pii = tkinter_functions_conn.recv()

        root.after(2000, next_steps(identified_pii, dataset, datap_functions_conn, datap_messages_conn, tkinter_functions_conn, tkinter_messages_conn))

def next_steps(identified_pii, dataset, datap_functions_conn, datap_messages_conn, tkinter_functions_conn, tkinter_messages_conn):
    ### Date Detection ###
    tkinter_display('in next steps')

    p_dates = Process(target=PII_data_processor.date_detection, args=(identified_pii, dataset, datap_functions_conn, datap_messages_conn))
    p_dates.start()

    tkinter_display(tkinter_messages_conn.recv())
    tkinter_display(tkinter_messages_conn.recv())
    identified_pii = tkinter_functions_conn.recv()

    # reviewed_pii, removed_status = review_potential_pii(identified_pii, dataset)
    # dataset, recoded_fields = recode(dataset)
    # path, export_status = export(dataset)
    # log(reviewed_pii, removed_status, recoded_fields, path, export_status)


if __name__ == '__main__':

    # GUI

    root = Tk()  # creates GUI window


    my_gui = GUI(root)  # runs code in class GUI

    # Styles
    root.configure(background='light gray')
    root.style = ttk.Style()
    # root.style.theme_use("clam")  # ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')
    root.style.configure('my.TButton', font=("Calibri", 11, 'bold'), background='white')
    root.style.configure('my.TLabel', background='white')

    # Display

    def onFrameConfigure(canvas):
        '''Reset the scroll region to encompass the inner frame'''
        canvas.configure(scrollregion=canvas.bbox("all"))

    canvas = Canvas(root)
    frame = Frame(canvas, width=606, height=636, bg="white")
    frame.place(x=30, y=30)
    #frame.pack_propagate(False)
    #frame.pack()

    vsb = Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((35,30), window=frame, anchor="nw")

    frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))

    # Instructions

    ttk.Label(frame, text=app_title, wraplength=536, justify=LEFT, font=("Calibri", 13, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(30, 10))
    ttk.Label(frame, text=intro_text, wraplength=546, justify=LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    ttk.Label(frame, text=intro_text_p2, wraplength=546, justify=LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 30))
    ttk.Button(frame, text="Select Dataset", command=file_select, style='my.TButton').pack(anchor='nw', padx=(30, 30), pady=(0, 30))

    # Listener

    root.mainloop()  # constantly looping event listener

try:
    if len(messages_pipe) != 0:
        ttk.Label(frame, text=messages_pipe.get(), wraplength=546, justify=LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 30))
except NameError:
    pass


# Extra code

#     ### Implement this for improvements to formatting
#     # text = tk.Text(frame, height=1, font="Helvetica 12")
#     # text.tag_configure("bold", font="Helvetica 12 bold")

#     # text.insert("end", the_message)
#     # text.insert("end", "world", "bold")
#     # text.configure(state="disabled")
#     # text.pack()