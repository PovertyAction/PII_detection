# Imports and Set-up
from tkinter import *
from tkinter.filedialog import askopenfilename
import tkinter
from tkinter import ttk
import tkinter.scrolledtext as tkst
from nltk.stem.porter import *
import time
from datetime import datetime
from multiprocessing import Process, Pipe
import multiprocessing
multiprocessing.freeze_support()
import PII_data_processor
from PIL import ImageTk, Image
import webbrowser

intro_text = "This script is meant to assist in the detection of PII (personally identifiable information) and subsequent removal from a dataset."
intro_text_p2 = "Ensuring the dataset is devoid of PII is ultimately still your responsibility. Be careful with potential identifiers, especially geographic, because they can sometimes be combined with other variables to become identifying."
intro_text_p3 = "*This version is customized for Windows 7. It has limited functionality. It is recommended you use the versions for Windows 10, OSX, or Linux if possible."
app_title = "IPA's PII Detector, Cleaner, and Recoder - Windows 7*"


class GUI:
    def __init__(self, master):
        self.master = master
        # master.frame(self, borderwidth=4)
        master.title(app_title)
        
        if hasattr(sys, "_MEIPASS"):
            icon_location = os.path.join(sys._MEIPASS, 'IPA-Asia-Logo-Image.ico')
        else:
            icon_location = 'IPA-Asia-Logo-Image.ico'

        master.iconbitmap(icon_location)
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
    ttk.Label(frame, text=the_message, wraplength=546, justify=LEFT, font=("Calibri Italic", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    frame.update()

def file_select():

    dataset_path = askopenfilename()

    tkinter_display('Scroll down for status updates.')
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
        if sensitivity.get() == "Medium (Default)":
            sensitivity_score = 3
        elif sensitivity.get() == "Maximum":
            sensitivity_score = 5
        elif sensitivity.get() == "High":
            sensitivity_score = 4
        elif sensitivity.get() == "Low":
            sensitivity_score = 2
        elif sensitivity.get() == "Minimum":
            sensitivity_score = 1

        threshold = 0.75 * sensitivity_score/3
        p_fpsm = Process(target=PII_data_processor.fuzzy_partial_stem_match, args=(identified_pii, restricted_vars, dataset, stemmer, threshold, datap_functions_conn, datap_messages_conn))
        p_fpsm.start()

        tkinter_display(tkinter_messages_conn.recv())
        tkinter_display(tkinter_messages_conn.recv())
        identified_pii = tkinter_functions_conn.recv()

        ### Unique Entries Detection ###
        min_entries_threshold = -1*sensitivity_score/5 + 1.15 #(1: 0.95, 2: 0.75, 3: 0.55, 4: 0.35, 5: 0.15)

        p_uniques = Process(target=PII_data_processor.unique_entries, args=(identified_pii, dataset, min_entries_threshold, datap_functions_conn, datap_messages_conn))
        p_uniques.start()

        tkinter_display(tkinter_messages_conn.recv())
        tkinter_display(tkinter_messages_conn.recv())
        identified_pii = tkinter_functions_conn.recv()

        root.after(2000, next_steps(identified_pii, dataset, datap_functions_conn, datap_messages_conn, tkinter_functions_conn, tkinter_messages_conn))

def about():
    webbrowser.open('https://github.com/PovertyAction/PII_detection/blob/master/README.md#pii_detection') 

def contact():
    webbrowser.open('https://github.com/PovertyAction/PII_detection/issues')

def methods():
    webbrowser.open('https://github.com/PovertyAction/PII_detection/blob/master/README.md#pii_detection')

def comparison():
    webbrowser.open('https://github.com/PovertyAction/PII_detection/blob/master/README.md#pii_detection')

def PII_field_names():
    webbrowser.open('https://github.com/PovertyAction/PII_detection/blob/fa1325094ecdd085864a58374d9f687181ac09fd/PII_data_processor.py#L115')

def next_steps(identified_pii, dataset, datap_functions_conn, datap_messages_conn, tkinter_functions_conn, tkinter_messages_conn):
    ### Date Detection ###
    p_dates = Process(target=PII_data_processor.date_detection, args=(identified_pii, dataset, datap_functions_conn, datap_messages_conn))
    p_dates.start()

    tkinter_display(tkinter_messages_conn.recv())
    tkinter_display(tkinter_messages_conn.recv())
    identified_pii = tkinter_functions_conn.recv()
    identified_pii = set(identified_pii)
    tkinter_display("The following fields appear to be PII: " + str(identified_pii)[1:-1])

    # reviewed_pii, removed_status = review_potential_pii(identified_pii, dataset)
    # dataset, recoded_fields = recode(dataset)
    # path, export_status = export(dataset)
    # log(reviewed_pii, removed_status, recoded_fields, path, export_status)

    ### Exit Gracefully ###
    tkinter_display('Processing complete. You can use the menu option to restart or exit.')

def restart_program():
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    import os
    python = sys.executable
    os.execl(python, python, * sys.argv)


if __name__ == '__main__':

    # GUI

    root = Tk()  # creates GUI window


    my_gui = GUI(root)  # runs code in class GUI

    # Styles
    menubar = tkinter.Menu(root)#.pack()

    # create a pulldown menu, and add it to the menu bar
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="Restart", command=restart_program)
    #filemenu.add_command(label="Save", command=hello)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)

    # create more pulldown menus
    helpmenu = Menu(menubar, tearoff=0)
    helpmenu.add_command(label="About", command=about)
    helpmenu.add_command(label="- Detection Methods", command=methods)
    helpmenu.add_command(label="- Comparison with Other Scripts", command=comparison)
    helpmenu.add_command(label="- PII Field Names", command=PII_field_names)
    helpmenu.add_command(label="- Data Security", command=PII_field_names)
    helpmenu.add_separator()
    helpmenu.add_command(label="File Issue on GitHub", command=contact)
    helpmenu.add_separator()
    helpmenu.add_command(label="Contribute", command=contact)
    menubar.add_cascade(label="Help", menu=helpmenu)

    root.configure(background='light gray', menu=menubar)
    root.style = ttk.Style()
    # root.style.theme_use("clam")  # ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')
    root.style.configure('my.TButton', font=("Calibri", 11, 'bold'), background='white')
    root.style.configure('my.TLabel', background='white')
    root.style.configure('my.TCheckbutton', background='white')
    root.style.configure('my.TMenubutton', background='white')

    root.resizable(False, False) # prevents window from being resized

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

    if hasattr(sys, "_MEIPASS"):
        logo_location = os.path.join(sys._MEIPASS, 'ipa logo.jpg')
    else:
        logo_location = 'ipa logo.jpg'

    logo = ImageTk.PhotoImage(Image.open(logo_location).resize((147, 71), Image.ANTIALIAS)) # Source is 2940 x 1416
    tkinter.Label(frame, image=logo, borderwidth=0).pack(anchor="ne", padx=(0, 30), pady=(30, 0))

    ttk.Label(frame, text=app_title, wraplength=536, justify=LEFT, font=("Calibri", 13, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(30, 10))
    ttk.Label(frame, text=intro_text, wraplength=546, justify=LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    ttk.Label(frame, text=intro_text_p2, wraplength=546, justify=LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    ttk.Label(frame, text=intro_text_p3, wraplength=546, justify=LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 30))

    ttk.Label(frame, text="Start Application: ", wraplength=546, justify=LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 10))
    ttk.Button(frame, text="Select Dataset", command=file_select, style='my.TButton').pack(anchor='nw', padx=(30, 30), pady=(0, 30))

    ttk.Label(frame, text="Options:", justify=LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 10))

    # Dropdown

    ttk.Label(frame, text="Select Detection Sensitivity:", justify=LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30,0))

    sensitivity = StringVar(frame)
    w = ttk.OptionMenu(frame, sensitivity, "Medium (Default)", "Maximum", "High", "Medium (Default)", "Low", "Minimum", style='my.TMenubutton').pack(anchor='nw', padx=(30,0))
    # A combobox may be a better choice
    
    # Checkbox

    # checkTemp = IntVar() #IntVar only necessary if need app to change upon being checked
    # checkTemp.set(0)
    # checkCmd.get() == 0 # tests if unchecked, = 1 if checked

    #checkTemp = 1
    #checkBox1 = ttk.Checkbutton(frame, variable=checkTemp, onvalue=1, offvalue=0, text="Output Session Log", style='my.TCheckbutton').pack(anchor='nw', padx=(30, 0), pady=(10,0), fill=X)

    ttk.Label(frame, text="Status:", justify=LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30,0), pady=(30, 0))
    first_message = "Awaiting dataset selection."
    first_message = datetime.now().strftime("%H:%M:%S") + '     ' + first_message
    ttk.Label(frame, text=first_message, wraplength=546, justify=LEFT, font=("Calibri Italic", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))

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