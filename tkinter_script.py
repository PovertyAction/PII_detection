# Imports and Set-up

import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename

from PIL import ImageTk, Image

import PII_data_processor

# from tkinter import *

# from tkinter import ttk
# import tkinter.scrolledtext as tkst
# from nltk.stem.porter import *
# import time
# from datetime import datetime
# from multiprocessing import Process, Pipe
# import multiprocessing
# multiprocessing.freeze_support()

# import webbrowser
# import os

intro_text = "This script is meant to assist in the detection of PII (personally identifiable information) and subsequent removal from a dataset."
intro_text_p2 = "Ensuring the dataset is devoid of PII is ultimately still your responsibility."
intro_text_p3 = "This is an alpha program, built without access to datasets containing PII on which to test or train it. Please help improve the program by filling out the survey on your experience using it (Help -> Provide Feedback)."
app_title = "IPA's PII Detector - Windows"

window_width = 686
window_height = 1066

#Maps pii to action to do with them
pii_candidates_to_dropdown_element = {}

def input(the_message):
    try:
        ttk.Label(frame, text=the_message, wraplength=546, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))

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


def tkinter_display_title(title):
    ttk.Label(frame, text=title, wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 10))
    frame.update()

def tkinter_display(the_message):
    # the_message = datetime.now().strftime("%H:%M:%S") + '     ' + the_message
    ttk.Label(frame, text=the_message, wraplength=546, justify=tk.LEFT, font=("Calibri Italic", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    frame.update()

def tkinter_display_pii_candidate(pii_candidate):
    #Create a frame for the pii label and action dropdown
    pii_frame = tk.Frame(master=frame, bg="white")
    pii_frame.pack(anchor='nw', padx=(30, 30), pady=(0, 12))

    ttk.Label(pii_frame, text=pii_candidate, wraplength=546, justify=tk.LEFT, font=("Calibri Italic", 11), style='my.TLabel').grid(row=0, column = 0)#pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    
    dropdown = tk.StringVar(pii_frame)
    w = ttk.OptionMenu(pii_frame, dropdown, "Drop", "Encode", "Keep", style='my.TMenubutton').grid(row=0, column = 1)#.pack(anchor='nw', padx=(30,0))

    frame.update()

    return dropdown

def get_sensitivity_score():
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

    return sensitivity_score

def create_anonymized_dataset():
    # we create a new dictionary that maps pii_candidate_to_action based on value of dropdown elements
    pii_candidates_to_action = {}
    for pii, dropdown_elem in pii_candidates_to_dropdown_element.items():
        pii_candidates_to_action[pii] = dropdown_elem.get()
    tkinter_display("Createing new dataset...")
    success = PII_data_processor.create_anonymized_dataset(pii_candidates_to_action)
    tkinter_display("The new dataset has been created and saved")

def read_file_and_find_piis():

    dataset_path = askopenfilename()

    #If no file was selected, do nothing
    if not dataset_path:
        return

    tkinter_display('Reding dataset and looking for PII candidates...')
    reading_status, pii_candidates_or_message = PII_data_processor.read_file_and_find_piis(dataset_path)
    
    if(reading_status is False):
        error_message = pii_candidates_or_message
        tkinter_display(error_message)
        return
    else:
        pii_candidates = pii_candidates_or_message

    tkinter_display_title('PII candidates:')
    tkinter_display('For each select an action and then press "Create anonymized dataset" butoom')
    
    #Display a label for each pii candidate and save their action dropdown element in dictionary for future reference
    for pii_candidate in pii_candidates:    
        pii_dropdown_element = tkinter_display_pii_candidate(pii_candidate)
        pii_candidates_to_dropdown_element[pii_candidate] = pii_dropdown_element

    #Show a create anonymized dataframe buttom
    ttk.Button(frame, text="Create anonymized dataset", command=create_anonymized_dataset, style='my.TButton').pack(anchor='nw', padx=(30, 30), pady=(0, 30))


    # #Two channels of communication between backend and frontend, one for functions results, another for messages
    # tkinter_functions_conn, datap_functions_conn = Pipe()
    # tkinter_messages_conn, datap_messages_conn = Pipe()

    # ### Importing dataset and printing messages ###
    
    # #Send dataset url to backend
    # tkinter_functions_conn.send(dataset_path)

    # #Start import_dataset process in backend
    # p_import = Process(target=PII_data_processor.import_dataset, args=(datap_functions_conn, datap_messages_conn))
    # p_import.start()

    # #Display messages recieved
    # tkinter_display(tkinter_messages_conn.recv())

    # #Get functions messages
    # import_results = tkinter_functions_conn.recv()
    # dataset = import_results[0]
    # dataset_path = import_results[1]
    # label_dict = import_results[2]
    # value_label_dict = import_results[3]

    # sensitivity_score = get_sensitivity_score()
    
    # ### Initialization of lists ###
    # p_initialize_vars = Process(target=PII_data_processor.initialize_lists, args=(datap_functions_conn, ))
    # p_initialize_vars.start()

    # initialize_results = tkinter_functions_conn.recv()
    # identified_pii, restricted_vars = initialize_results[0], initialize_results[1]

    # ### Stemming of restricted list ###
    # p_stemming_rl = Process(target=PII_data_processor.stem_restricted, args=(restricted_vars, datap_functions_conn, datap_messages_conn))
    # p_stemming_rl.start()

    # tkinter_display(tkinter_messages_conn.recv())

    # time.sleep(2)

    # stemming_rl_results = tkinter_functions_conn.recv()
    # restricted_vars, stemmer = stemming_rl_results[0], stemming_rl_results[1]

    # match_sensitivity = 6 - sensitivity_score # Consider making 'minimum' result in no Stata variable label search
    # ### Word Match Stemming ###
    # p_wordm_stem = Process(target=PII_data_processor.word_match_stemming, args=(identified_pii, restricted_vars, dataset, stemmer, label_dict, match_sensitivity, datap_functions_conn, datap_messages_conn))
    # p_wordm_stem.start()

    # tkinter_display(tkinter_messages_conn.recv())
    # tkinter_display(tkinter_messages_conn.recv())
    # identified_pii = tkinter_functions_conn.recv()

    # ### Fuzzy Partial Stem Match ###
    # threshold = 0.75 * sensitivity_score/3
    # p_fpsm = Process(target=PII_data_processor.fuzzy_partial_stem_match, args=(identified_pii, restricted_vars, dataset, stemmer, threshold, datap_functions_conn, datap_messages_conn))
    # p_fpsm.start()

    # tkinter_display(tkinter_messages_conn.recv())
    # tkinter_display(tkinter_messages_conn.recv())
    # identified_pii = tkinter_functions_conn.recv()

    # ### Unique Entries Detection ###
    # min_entries_threshold = -1*sensitivity_score/5 + 1.15 #(1: 0.95, 2: 0.75, 3: 0.55, 4: 0.35, 5: 0.15)

    # p_uniques = Process(target=PII_data_processor.unique_entries, args=(identified_pii, dataset, min_entries_threshold, datap_functions_conn, datap_messages_conn))
    # p_uniques.start()

    # tkinter_display(tkinter_messages_conn.recv())
    # tkinter_display(tkinter_messages_conn.recv())
    # identified_pii = tkinter_functions_conn.recv()

    # root.after(2000, next_steps(identified_pii, dataset, datap_functions_conn, datap_messages_conn, tkinter_functions_conn, tkinter_messages_conn))



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
    python = tk.sys.executable
    os.execl(python, python, * tk.sys.argv)

def window_setup(master):

    #Add window title
    master.title(app_title)
    
    #Add window icon
    if hasattr(tk.sys, "_MEIPASS"):
        icon_location = os.path.join(sys._MEIPASS, 'app.ico')
    else:
        icon_location = 'app.ico'
    imgicon = ImageTk.PhotoImage(Image.open(icon_location))
    master.tk.call('wm', 'iconphoto', master._w, imgicon) 

    #Define window size
    master.minsize(width=window_width, height=window_height)

    #Prevent window from being resized
    master.resizable(False, False)

def menubar_setup(root):

    def about():
        webbrowser.open('https://github.com/PovertyAction/PII_detection/blob/master/README.md#pii_detection') 

    def contact():
        webbrowser.open('https://github.com/PovertyAction/PII_detection/issues')

    def article():
        webbrowser.open('https://povertyaction.force.com/support/s/article/IPAs-Personally-Identifiable-Information-Application')

    def comparison():
        webbrowser.open('https://ipastorage.box.com/s/35jbvflnt6e4ev868290c3hygubofz2r')

    def PII_field_names():
        webbrowser.open('https://github.com/PovertyAction/PII_detection/blob/fa1325094ecdd085864a58374d9f687181ac09fd/PII_data_processor.py#L115')

    def survey():
        webbrowser.open('https://goo.gl/forms/YYOxXJSKBpp60ol32')

    menubar = tk.Menu(root)

    # Create file menu pulldown
    filemenu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=filemenu)

    # Add commands to filemenu menu
    filemenu.add_command(label="Restart", command=restart_program)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    
    # Create help menu pulldown 
    helpmenu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=helpmenu)
    
    # Add commands to help menu
    helpmenu.add_command(label="About (v0.1.2)", command=about)
    helpmenu.add_command(label="- Knowledge Article", command=article)
    helpmenu.add_command(label="- Comparison with Other Scripts", command=comparison)
    #helpmenu.add_command(label="- PII Field Names", command=PII_field_names)
    #helpmenu.add_command(label="- Data Security", command=PII_field_names)
    helpmenu.add_separator()
    helpmenu.add_command(label="File Issue on GitHub", command=contact)
    helpmenu.add_separator()
    #helpmenu.add_command(label="Contribute", command=contact)
    helpmenu.add_command(label="Provide Feedback", command=survey)

    # Add menu bar to window
    root.configure(menu=menubar)

def window_style_setup(root):
    root.style = ttk.Style()
    # # root.style.theme_use("clam")  # ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')
    root.style.configure('my.TButton', font=("Calibri", 11, 'bold'), background='white')
    root.style.configure('my.TLabel', background='white')
    root.style.configure('my.TCheckbutton', background='white')
    root.style.configure('my.TMenubutton', background='white')

def add_scrollbar(root, canvas, frame):
    
    #Configure frame to recognize scrollregion
    def onFrameConfigure(canvas):
        '''Reset the scroll region to encompass the inner frame'''
        canvas.configure(scrollregion=canvas.bbox("all"))
    frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))

    #Create scrollbar
    vsb = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")


if __name__ == '__main__':

    # Create GUI window
    root = tk.Tk()  

    window_setup(root)  

    menubar_setup(root)
    
    window_style_setup(root)

    # Create canvas where app will displayed

    canvas = tk.Canvas(root)
    canvas.pack(side="left", fill="both", expand=True)

    # Create frame inside canvas
    frame = tk.Frame(canvas, width=window_width, height=window_height, bg="white")
    frame.pack(side="left", fill="both", expand=True)
    # frame.place(x=0, y=0)
    canvas.create_window(0,0, window=frame, anchor="nw")

    add_scrollbar(root, canvas, frame)

    #Add logo
    if hasattr(tk.sys, "_MEIPASS"):    
        logo_location = os.path.join(sys._MEIPASS, 'ipa logo.jpg')
    else:
        logo_location = 'ipa logo.jpg'
    logo = ImageTk.PhotoImage(Image.open(logo_location).resize((147, 71), Image.ANTIALIAS)) # Source is 2940 x 1416
    ttk.Label(frame, image=logo, borderwidth=0).pack(anchor="ne", padx=(0, 30), pady=(30, 0))

    #Add intro text
    ttk.Label(frame, text=app_title, wraplength=536, justify=tk.LEFT, font=("Calibri", 13, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(30, 10))
    ttk.Label(frame, text=intro_text, wraplength=546, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    ttk.Label(frame, text=intro_text_p2, wraplength=546, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    ttk.Label(frame, text=intro_text_p3, wraplength=546, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 30))

    #Labels and buttoms to run app
    ttk.Label(frame, text="Start Application: ", wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 10))
    ttk.Button(frame, text="Select Dataset", command=read_file_and_find_piis, style='my.TButton').pack(anchor='nw', padx=(30, 30), pady=(0, 30))




    # ttk.Label(frame, text="Options:", justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 10))

    # # Sensitivity dropdown
    # ttk.Label(frame, text="Select Detection Sensitivity:", justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30,0))
    # sensitivity = StringVar(frame)
    # w = ttk.OptionMenu(frame, sensitivity, "Medium (Default)", "Maximum", "High", "Medium (Default)", "Low", "Minimum", style='my.TMenubutton').pack(anchor='nw', padx=(30,0))

    # # Status
    # ttk.Label(frame, text="Status:", justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30,0), pady=(30, 0))
    # first_message = "Awaiting dataset selection."
    # first_message = datetime.now().strftime("%H:%M:%S") + '     ' + first_message
    # ttk.Label(frame, text=first_message, wraplength=546, justify=tk.LEFT, font=("Calibri Italic", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))


    # Constantly looping event listener
    root.mainloop()  