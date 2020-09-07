# Imports and Set-up
import sys
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from PIL import ImageTk, Image

import find_piis_in_unstructured_text_backend
import PII_data_processor

from constant_strings import *

import webbrowser
import os

intro_text = "This script is meant to assist in the detection of PII (personally identifiable information) and subsequent replacement from a dataset. This is an alpha program, not fully tested yet."
intro_text_p2 = "You will first load a dataset that might contain PII variables. The system will search for PIIs in all unstructured text in the dataset to later replace them by a 'xxxx' string."#, built without access to datasets containing PII on which to test or train it. Please help improve the program by filling out the survey on your experience using it (Help -> Provide Feedback)."
app_title = "IPA's Find PIIs in unstructured text - v0.0.1"

window_width = 1086
window_height = 466

#Maps pii to action to do with them
pii_candidates_to_dropdown_element = {}

#Dataset we are working with
dataset = None
dataset_path = None
new_file_path = None
label_dict = None

widgets_visible_ready_to_remove = []
find_piis_options={}

def tkinter_display_title(title):
    label = ttk.Label(frame, text=title, wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel')
    label.pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    frame.update()
    return label

def tkinter_display(the_message):
    # the_message = datetime.now().strftime("%H:%M:%S") + '     ' + the_message
    label = ttk.Label(frame, text=the_message, wraplength=546, justify=tk.LEFT, font=("Calibri Italic", 11), style='my.TLabel')
    label.pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    frame.update()
    return label


def clear_window_removing_all_widgets():
    #Remove widgets currently visible
    for widget in widgets_visible_ready_to_remove:
        widget.pack_forget()
    widgets_visible_ready_to_remove.clear()

    canvas.yview_moveto(0)


def find_piis():
    global dataset
    global dataset_path
    global label_dict
    global columns_still_to_check
    
    new_file_path = find_piis_in_unstructured_text_backend.find_piis_and_create_deidentified_dataset(dataset, dataset_path, label_dict)

    #Clean and display pii found
    clear_window_removing_all_widgets()
    

    if(new_file_path):
        tkinter_display_title("Congratulations! Task ready!")
        tkinter_display("The new dataset has been created and saved in the original file directory.\nYou will also find a log file describing the detection process.")
        
        tkinter_display("Do you want to work on a new file? Click Restart buttom.")
        ttk.Button(frame, text="Restart program", command=restart_program, style='my.TButton').pack(anchor='nw', padx=(30, 30), pady=(0, 5))

        frame.update()


def import_file():

    global dataset
    global dataset_path
    global label_dict
    global next_search_method
    global columns_still_to_check

    dataset_path = askopenfilename()

    #If no file was selected, do nothing
    if not dataset_path:
        return

    importing_file_label = tkinter_display("Importing file...")
    
    #Scroll down
    canvas.yview_moveto( 1 )
    frame.update()

    widgets_visible_ready_to_remove.append(importing_file_label)

    #Read file
    reading_status, reading_content = PII_data_processor.import_file(dataset_path)
    
    #Remove 'importiung file label'
    importing_file_label.pack_forget()

    if(reading_status is False):
        reading_status_label = tkinter_display(reading_content[ERROR_MESSAGE])
        return
    else:
        reading_status_label = tkinter_display("Success reading file: "+dataset_path)
        dataset = reading_content[DATASET]
        label_dict = reading_content[LABEL_DICT]
        columns_still_to_check = dataset.columns

    buttom_text = "Find PIIs"

    find_piis_next_step_button = ttk.Button(frame, text=buttom_text, command=find_piis, style='my.TButton')
    find_piis_next_step_button.pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    
    #Scroll down
    frame.update()
    canvas.yview_moveto( 1 )

    widgets_visible_ready_to_remove.extend([reading_status_label, find_piis_next_step_button])


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
    master.minsize(width=1, height=1)

    #Make window reziable
    master.resizable(True, True)

def open_survey():
        webbrowser.open('https://docs.google.com/forms/d/e/1FAIpQLSfxB_pnReUd0EvFfQxPu5JI9oRGCpDgULWkTeDHYoqx8x7q-Q/viewform')

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
    helpmenu.add_command(label="Provide Feedback", command=open_survey)

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
    tk.Label(frame, image=logo, borderwidth=0).pack(anchor="nw", padx=(30, 30), pady=(30, 0))

    #Add intro text
    app_title_label = ttk.Label(frame, text=app_title, wraplength=536, justify=tk.LEFT, font=("Calibri", 13, 'bold'), style='my.TLabel')
    app_title_label.pack(anchor='nw', padx=(30, 30), pady=(30, 10))
    
    intro_text_1_label = ttk.Label(frame, text=intro_text, wraplength=546, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel')
    intro_text_1_label.pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    

    intro_text_2_label = ttk.Label(frame, text=intro_text_p2, wraplength=546, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel')
    intro_text_2_label.pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    
    #Labels and buttoms to run app
    start_application_label = ttk.Label(frame, text="Run application: ", wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel')
    start_application_label.pack(anchor='nw', padx=(30, 30), pady=(0, 10))
    
    select_dataset_button = ttk.Button(frame, text="Select Dataset", command=import_file, style='my.TButton')
    select_dataset_button.pack(anchor='nw', padx=(30, 30), pady=(0, 5))

    #Add widgets to list of widgets to remove later on
    widgets_visible_ready_to_remove.extend([intro_text_1_label, intro_text_2_label, start_application_label, select_dataset_button])

    # Constantly looping event listener
    root.mainloop()  