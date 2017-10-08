# Imports and Set-up
from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter import ttk
from nltk.stem.porter import *
import time
import multiprocessing as mp
import PII_data_processor

intro_text = "This script is meant to assist in the detection of PII (personally identifiable information) and subsequent removal from a dataset."
intro_text_p2 = "Ensuring the dataset is devoid of PII is ultimately still your responsibility. Be careful with potential identifiers, especially geographic, because they can sometimes be combined with other variables to become identifying."
app_title = "IPA's PII Detector, Cleaner, and Recoder"


class GUI:
    def __init__(self, master):
        self.master = master
        # master.frame(self, borderwidth=4)
        master.title(app_title)
        master.minsize(width=666, height=666)

def input(the_message):
    try:
        ttk.Label(frame, text=the_message, wraplength=546, justify=LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))

        def evaluate(event=None):
            pass
            # if __name__ == '__main__':
            #     queue = mp.Queue()
            #     #proc = mp.Process(target=PII_data_processor.driver, args=(queue,))
            #     proc.daemon = True
            #     proc.start()  # This launches the child process, calling child.run()
            #     queue.put(str(entry.get()))  # Get results from child.run

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
    ttk.Label(frame, text=the_message, wraplength=546, justify=LEFT, font=("Calibri", 11), style='my.TLabel')  # .pack(anchor='nw', padx=(30, 30), pady=(0, 12))


def file_select():

    dataset_path = askopenfilename()

    print('The script is running...')

    if __name__ == '__main__':
        queue = mp.Queue()
        queue.put(dataset_path)
        proc = mp.Process(target=PII_data_processor.import_dataset, args=(queue,))
        proc.daemon = True
        proc.start()  # This launches the child process, calling child.run()
        tkinter_display(queue.get())
        #queue.put(str(entry.get()))  # Get results from child.run

    #import_results = import_dataset(dataset_path)  # dataset, label_dict, value_label_dict

    # dataset = import_results[0]
    # dataset_path = import_results[1]

    # identified_pii, restricted_vars = initialize_lists()
    # restricted_vars, stemmer = stem_restricted(restricted_vars)

    # identified_pii = word_match_stemming(identified_pii, restricted_vars, dataset, stemmer)
    # identified_pii = fuzzy_partial_stem_match(identified_pii, restricted_vars, dataset, stemmer, threshold=0.75)
    # identified_pii = unique_entries(identified_pii, dataset, min_entries_threshold=0.5)
    # identified_pii = date_detection(identified_pii, dataset)

    # reviewed_pii, removed_status = review_potential_pii(identified_pii, dataset)
    # dataset, recoded_fields = recode(dataset)
    # path, export_status = export(dataset)
    # log(reviewed_pii, removed_status, recoded_fields, path, export_status)


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

frame = Frame(width=606, height=636, bg="white")
frame.place(x=30, y=30)
frame.pack_propagate(False)
frame.pack()

# Instructions

ttk.Label(frame, text=app_title, wraplength=536, justify=LEFT, font=("Calibri", 13, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(30, 10))
ttk.Label(frame, text=intro_text, wraplength=546, justify=LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))
ttk.Label(frame, text=intro_text_p2, wraplength=546, justify=LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 30))
ttk.Button(frame, text="Select Dataset", command=file_select, style='my.TButton').pack(anchor='nw', padx=(30, 30), pady=(0, 30))

# Listener

root.mainloop()  # constantly looping event listener

# Extra code

#     ### Implement this for improvements to formatting
#     # text = tk.Text(frame, height=1, font="Helvetica 12")
#     # text.tag_configure("bold", font="Helvetica 12 bold")

#     # text.insert("end", the_message)
#     # text.insert("end", "world", "bold")
#     # text.configure(state="disabled")
#     # text.pack()