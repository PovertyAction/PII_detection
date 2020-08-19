# Imports and Set-up
import sys
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

import webbrowser
import os

intro_text = "This script is meant to assist in the detection of PII (personally identifiable information) and subsequent removal from a dataset."
# intro_text_p2 = "Ensuring the dataset is devoid of PII is ultimately still your responsibility."
intro_text_p2 = "This is an alpha program, not fully tested yet."#, built without access to datasets containing PII on which to test or train it. Please help improve the program by filling out the survey on your experience using it (Help -> Provide Feedback)."
app_title = "IPA's PII Detector - Windows"

window_width = 586
window_height = 466

#Maps pii to action to do with them
pii_candidates_to_dropdown_element = {}

#Dataset we are working with
dataset = None
dataset_path = None
new_file_path = None
label_dict = None

finished = False

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
    ttk.Label(frame, text=title, wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    frame.update()

def tkinter_display(the_message):
    # the_message = datetime.now().strftime("%H:%M:%S") + '     ' + the_message
    ttk.Label(frame, text=the_message, wraplength=546, justify=tk.LEFT, font=("Calibri Italic", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    frame.update()

def tkinter_display_pii_candidate(pii_candidate):
    #Create a frame for the pii label and action dropdown
    pii_frame = tk.Frame(master=frame, bg="white")
    pii_frame.pack(anchor='nw', padx=(30, 30), pady=(0, 5))

    ttk.Label(pii_frame, text=pii_candidate, wraplength=546, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel').grid(row=0, column = 0)
    
    dropdown = tk.StringVar(pii_frame)
    w = ttk.OptionMenu(pii_frame, dropdown, "Drop", "Drop", "Encode", "Keep", style='my.TMenubutton').grid(row=0, column = 1)

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

def open_deidentified_file():
    os.system("start " + new_file_path)

def create_anonymized_dataset():
    global finished
    global new_file_path

    if(finished):
        return

    # we create a new dictionary that maps pii_candidate_to_action based on value of dropdown elements
    pii_candidates_to_action = {}
    for pii, dropdown_elem in pii_candidates_to_dropdown_element.items():
        pii_candidates_to_action[pii] = dropdown_elem.get()
    tkinter_display("Creating new dataset...")

    new_file_path = PII_data_processor.create_anonymized_dataset(dataset, label_dict, dataset_path, pii_candidates_to_action)
    
    if(new_file_path):
        tkinter_display("The new dataset has been created and saved in the file directory. You will also find a log file on piis found and work done.")
        ttk.Button(frame, text="Open de-identified dataset", command=open_deidentified_file, style='my.TButton').pack(anchor='nw', padx=(30, 30), pady=(0, 5))        
        
        tkinter_display("Do you want to work on a new file? Click Restart buttom.")
        ttk.Button(frame, text="Restart program", command=restart_program, style='my.TButton').pack(anchor='nw', padx=(30, 30), pady=(0, 5))
        frame.update()

        finished = True
    #Automatic scroll down
    canvas.yview_moveto( 1 )

def read_file_and_find_piis():
    global dataset
    global dataset_path
    global label_dict

    if(finished):
        return

    dataset_path = askopenfilename()

    #If no file was selected, do nothing
    if not dataset_path:
        return

    tkinter_display('Reding dataset and looking for PII candidates...')
    reading_status, pii_candidates_or_message, dataset, label_dict = PII_data_processor.read_file_and_find_piis(dataset_path)
    
    if(reading_status is False):
        error_message = pii_candidates_or_message
        tkinter_display(error_message)
        return
    else:
        pii_candidates = pii_candidates_or_message

    if(len(pii_candidates)==0):
        tkinter_display_title('No PII candidates found.')
        return

    tkinter_display_title('PII candidates found:')
    tkinter_display('For each PII candidate, select an action and then press the "Create anonymized dataset" button')
    
    #Display a label for each pii candidate and save their action dropdown element in dictionary for future reference
    for pii_candidate in pii_candidates:    
        pii_dropdown_element = tkinter_display_pii_candidate(pii_candidate)
        pii_candidates_to_dropdown_element[pii_candidate] = pii_dropdown_element

    #Show a create anonymized dataframe buttom
    ttk.Button(frame, text="Create anonymized dataset", command=create_anonymized_dataset, style='my.TButton').pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    frame.update()

    # #Automatic scroll down
    # canvas.yview_moveto( 1 )

def restart_program():
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    python = tk.sys.executable
    os.execl(python, python, * tk.sys.argv)

def window_setup(master):

    #Add window title
    master.title(app_title)
    
    #Add window icon
    if hasattr(sys, "_MEIPASS"):
        icon_location = os.path.join(sys._MEIPASS, 'app.ico')
    else:
        icon_location = 'app.ico'
    master.iconbitmap(icon_location)

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
    # helpmenu.add_command(label="- Knowledge Article", command=article)
    # helpmenu.add_command(label="- Comparison with Other Scripts", command=comparison)
    #helpmenu.add_command(label="- PII Field Names", command=PII_field_names)
    #helpmenu.add_command(label="- Data Security", command=PII_field_names)
    helpmenu.add_separator()
    helpmenu.add_command(label="File Issue on GitHub", command=contact)
    # helpmenu.add_separator()
    #helpmenu.add_command(label="Contribute", command=contact)
    # helpmenu.add_command(label="Provide Feedback", command=survey)

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

    def onMouseWheel(canvas, event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    #Bind mousewheel to scrollbar
    frame.bind_all("<MouseWheel>", lambda event, canvas=canvas: onMouseWheel(canvas, event))


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

    canvas = tk.Canvas(root, width=window_width, height=window_height, bg="white")
    canvas.pack(side="left", fill="both", expand=True)

    # Create frame inside canvas
    frame = tk.Frame(canvas, width=window_width, height=window_height, bg="white")
    frame.pack(side="left", fill="both", expand=True)
    # frame.place(x=0, y=0)

    #This create_window is related to the scrollbar. Im going to delete it atm
    canvas.create_window(0,0, window=frame, anchor="nw")

    add_scrollbar(root, canvas, frame)

    #Add logo
    if hasattr(tk.sys, "_MEIPASS"):    
        logo_location = os.path.join(sys._MEIPASS, 'ipa_logo.jpg')
    else:
        logo_location = 'ipa_logo.jpg'
    logo = ImageTk.PhotoImage(Image.open(logo_location).resize((147, 71), Image.ANTIALIAS)) # Source is 2940 x 1416
    tk.Label(frame, image=logo, borderwidth=0).pack(anchor="ne", padx=(0, 30), pady=(30, 0))

    #Add intro text
    ttk.Label(frame, text=app_title, wraplength=536, justify=tk.LEFT, font=("Calibri", 13, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(30, 10))
    ttk.Label(frame, text=intro_text, wraplength=546, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    ttk.Label(frame, text=intro_text_p2, wraplength=546, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    # ttk.Label(frame, text=intro_text_p3, wraplength=546, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 30))

    #Labels and buttoms to run app
    ttk.Label(frame, text="Start Application: ", wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel').pack(anchor='nw', padx=(30, 30), pady=(0, 10))
    ttk.Button(frame, text="Select Dataset", command=read_file_and_find_piis, style='my.TButton').pack(anchor='nw', padx=(30, 30), pady=(0, 5))




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