# Imports and Set-up
import sys
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
from PIL import ImageTk, Image
import webbrowser
import os
import requests

import PII_data_processor

from constant_strings import *

intro_text = "This script is meant to assist in the detection of PII (personally identifiable information) and subsequent removal from a dataset. This is an alpha program, not fully tested yet."
intro_text_p2 = "You will first load a dataset that might contain PII variables. The system will try to identify the PII candidates. Please indicate if you would like to Drop, Encode or Keep them to then generate a new de-identified dataset."#, built without access to datasets containing PII on which to test or train it. Please help improve the program by filling out the survey on your experience using it (Help -> Provide Feedback)."
version_number = "0.2.21"
app_title = "IPA's PII Detector - v"+version_number

#Maps pii to action to do with them
pii_candidates_to_dropdown_element = {}

#Dataset we are working with
dataset = None
dataset_path = None
new_file_path = None
label_dict = None

find_piis_options={}

window_width=None
window_height=None

columns_where_to_replace_piis = None

piis_in_text_box = None

check_survey_cto_checkbutton_var = None
check_locations_pop_checkbutton_var = None
column_level_option_for_unstructured_text_checkbutton_var = None
keep_unstructured_text_option_checkbutton_var = None

country_dropdown = None
language_dropdown = None

piis_frame = None
anonymized_dataset_creation_frame = None
new_dataset_message_frame = None
do_file_message_frame = None

pii_search_in_unstructured_text_enabled = False

def display_title(title, frame_where_to_display):
    label = ttk.Label(frame_where_to_display, text=title, wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel')
    label.pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    frame.update()
    return label

def display_message(the_message, frame_where_to_display):
    label = ttk.Label(frame_where_to_display, text=the_message, wraplength=546, justify=tk.LEFT, font=("Calibri Italic", 11), style='my.TLabel')
    label.pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    frame.update()
    return label

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

def display_pii_candidates(pii_candidates, label_dict, frame_where_to_display, default_dropdown_option="Drop"):

    #Create a frame for the pii labels and actions dropdown
    #padx determines space between label and dropdown
    pii_frame = tk.Frame(master=frame_where_to_display, bg="white")
    pii_frame.pack(anchor='nw', padx=(30, 30), pady=(0, 5))

    #Add title to grid
    ttk.Label(pii_frame, text='PII candidate', wraplength=546, justify=tk.LEFT, font=("Calibri", 11, 'bold'), style='my.TLabel').grid(row=0, column = 0, sticky = 'w', pady=(0,2))
    ttk.Label(pii_frame, text='Reason detected', wraplength=546, justify=tk.LEFT, font=("Calibri", 11, 'bold'), style='my.TLabel').grid(row=0, column = 1, sticky = 'w', pady=(0,2))
    ttk.Label(pii_frame, text='Desired action', wraplength=546, justify=tk.LEFT, font=("Calibri", 11, 'bold'), style='my.TLabel').grid(row=0, column = 2, sticky = 'w', padx=(5,0), pady=(0,2))

    #Display a label for each pii candidate and save their action dropdown element in dictionary for future reference
    for idx, (pii_candidate, reason_detected) in enumerate(pii_candidates.items()):

        #Given that in fist row of grid we have title of columns
        idx=idx+1

        #Add labels to pii candidates for better user understanding of column names
        if label_dict and pii_candidate in label_dict and label_dict[pii_candidate]!="":
            pii_candidate_label = pii_candidate + ": "+label_dict[pii_candidate]+"\t"
        else:
            pii_candidate_label = pii_candidate+"\t"

        ttk.Label(pii_frame, text=pii_candidate_label, wraplength=546, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel').grid(row=idx, column = 0, sticky = 'w', pady=(0,2))

        ttk.Label(pii_frame, text=reason_detected+"\t", wraplength=546, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel').grid(row=idx, column = 1, sticky = 'w', pady=(0,2))

        dropdown = tk.StringVar(pii_frame)
        w = ttk.OptionMenu(pii_frame, dropdown, default_dropdown_option, "Drop", "Encode", "Keep", style='my.TMenubutton').grid(row=idx, column = 2, sticky = 'w', pady=(0,2))

        pii_candidates_to_dropdown_element[pii_candidate] = dropdown

    frame.update()

    return pii_frame

def do_file_created_message(creating_do_file_message):
    creating_do_file_message.pack_forget()

    #Automatic scroll up
    canvas.yview_moveto( 0 )

    goodbye_frame = tk.Frame(master=frame, bg="white")
    goodbye_frame.pack(anchor='nw', padx=(0, 0), pady=(0, 0))

    do_file_message_frame = tk.Frame(master=anonymized_dataset_creation_frame, bg="white")
    do_file_message_frame.pack(anchor='nw', padx=(0, 0), pady=(0, 0))

    display_message("The .do file that creates a deidentified dataset has been created and saved in the original file directory.\n", do_file_message_frame)
    display_goodby_message(do_file_message_frame)

def display_goodby_message(goodbye_frame):
    display_message("Do you want to work on a new file? Click File/Restart in the menu bar.", goodbye_frame)

    #Create a frame for the survey link
    survey_frame = tk.Frame(master=goodbye_frame, bg="white")
    survey_frame.pack(anchor='nw', padx=(30, 30), pady=(0, 5))

    survey_text = "Can you provide feedback to improve the app? Please click "
    ttk.Label(survey_frame, text=survey_text, wraplength=546, justify=tk.LEFT, font=("Calibri Italic", 11), style='my.TLabel').grid(row=0, column = 0)
    link = tk.Label(survey_frame, text="here", fg="blue", font=("Calibri Italic", 11), cursor="hand2", background='white')
    link.grid(row = 0, column=1)
    link.bind("<Button-1>", lambda e: open_survey())

def new_dataset_created_message(creating_dataset_message):

    creating_dataset_message.pack_forget()

    global new_dataset_message_frame

    new_dataset_message_frame = tk.Frame(master=anonymized_dataset_creation_frame, bg="white")
    new_dataset_message_frame.pack(anchor='nw', padx=(0, 0), pady=(0, 0))

    if(new_file_path):
        display_message("The new dataset has been created and saved in the original file directory.\nYou will also find a log file describing the detection process.\nIf you encoded variables, you will find a .csv file that maps original to encoded values.\n", new_dataset_message_frame)

        #PENDING: ADD A BUTTOM TO FOLDER WITH OUTPUTS

        display_goodby_message(new_dataset_message_frame)
        #Need this?
        #frame.update()

def remove_previous_dataset_do_file_message():
    global new_dataset_message_frame
    global do_file_message_frame

    if new_dataset_message_frame is not None:
        new_dataset_message_frame.pack_forget()

    if do_file_message_frame is not None:
        do_file_message_frame.pack_forget()

def create_do_file():
    remove_previous_dataset_do_file_message()

    creating_do_file_message = display_message("Creating .do file...", anonymized_dataset_creation_frame)

    #Create dictionary that maps pii_candidate_to_action based on value of dropdown elements
    pii_candidates_to_action = create_pii_candidates_to_action()

    new_file_path = PII_data_processor.create_deidentifying_do_file(dataset_path, pii_candidates_to_action)

    do_file_created_message(creating_do_file_message)

def create_anonymized_dataset_creation_frame():

    global anonymized_dataset_creation_frame
    piis_frame.forget()

    anonymized_dataset_creation_frame = tk.Frame(master=frame, bg="white")
    anonymized_dataset_creation_frame.pack(anchor='nw', padx=(0, 0), pady=(0, 0))

    display_title('Decide how to export your deidentified dataset', anonymized_dataset_creation_frame)

    display_message('You can either directly download a deidentified dataset, and/or download a .do file that creates the deidentified dataset', anonymized_dataset_creation_frame)


    create_dataset_button = ttk.Button(anonymized_dataset_creation_frame, text='Download deidentified dataset', command=create_anonymized_dataset, style='my.TButton')
    create_dataset_button.pack(anchor='nw', padx=(30, 30), pady=(0, 5))

    create_do_file_button = ttk.Button(anonymized_dataset_creation_frame, text='Create .do file for deidentification', command=create_do_file, style='my.TButton')
    create_do_file_button.pack(anchor='nw', padx=(30, 30), pady=(0, 5))

    frame.update()


def create_pii_candidates_to_action():

    pii_candidates_to_action = {}
    for pii, dropdown_elem in pii_candidates_to_dropdown_element.items():
        pii_candidates_to_action[pii] = dropdown_elem.get()
    return pii_candidates_to_action

def create_anonymized_dataset():

    remove_previous_dataset_do_file_message()

    creating_dataset_message = display_message("Creating new dataset...", anonymized_dataset_creation_frame)

    #Automatic scroll down
    canvas.yview_moveto( 1 )
    frame.update()

    global new_file_path

    #We create a new dictionary that maps pii_candidate_to_action based on value of dropdown elements
    pii_candidates_to_action = create_pii_candidates_to_action()

    #Capture words to replace in unstructured text
    if(pii_search_in_unstructured_text_enabled and keep_unstructured_text_option_checkbutton_var.get()==1):
        piis_found_in_ustructured_text = [w.strip() for w in piis_in_text_box.get("1.0", "end").split(',')]
    else:
        piis_found_in_ustructured_text = None

    new_file_path = PII_data_processor.create_anonymized_dataset(dataset, label_dict, dataset_path, pii_candidates_to_action, columns_where_to_replace_piis, piis_found_in_ustructured_text)

    new_dataset_created_message(creating_dataset_message)



def display_piis_found_in_ustructured_text(piis_found_in_ustructured_text, frame_where_to_display):
    global piis_in_text_box
    piis_in_text_box = tk.Text(frame_where_to_display, height=20, width=70)
    piis_in_text_box.pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    piis_in_text_box.insert(tk.END, ", ".join(piis_found_in_ustructured_text))
    return piis_in_text_box


def create_unstructured_piis_frame(next_search_method, next_search_method_button_text, piis_found_in_ustructured_text):

    piis_frame = tk.Frame(master=frame, bg="white")
    piis_frame.pack(anchor='nw', padx=(0, 0), pady=(0, 0))


    display_title('PIIs found in unstructured text:', piis_frame)
    display_message("These are the potential PIIs found in open ended questions and which will be replaced by 'XXXX' in the new de-identified dataset", piis_frame)
    display_message("Feel free to remove from the list if you find wrongly identified PIIs, just keep words separated by commas.", piis_frame)
    display_piis_found_in_ustructured_text(piis_found_in_ustructured_text, piis_frame)


    #COPIED FROM create_piis_frame()
    if(next_search_method is not None):
        buttom_text = next_search_method_button_text
        next_command = find_piis
    else:
        buttom_text = 'Create anonymized dataset and download .do files'
        next_command = create_anonymized_dataset_creation_frame

    next_method_button = ttk.Button(piis_frame, text=buttom_text, command=next_command, style='my.TButton')
    next_method_button.pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    frame.update()

    return piis_frame

def create_piis_frame(next_search_method, next_search_method_button_text, pii_candidates):

    global columns_still_to_check

    piis_frame = tk.Frame(master=frame, bg="white")
    piis_frame.pack(anchor='nw', padx=(0, 0), pady=(0, 0))


    display_title('PII candidates found using '+search_method+':', piis_frame)

    if(len(pii_candidates)==0):
        display_message('No PII candidates found.', piis_frame)
    else:
        #Create title, instructions, and display piis
        display_message('For each PII candidate, select an action', piis_frame)
        display_pii_candidates(pii_candidates, label_dict, piis_frame)

    #Update columns_still_to_check, removing pii candidates found
    columns_still_to_check = [c for c in columns_still_to_check if c not in pii_candidates]


    if(next_search_method is not None):
        buttom_text = next_search_method_button_text
        next_command = find_piis
    else:
        buttom_text = 'Create anonymized dataset and download .do files'
        next_command = create_anonymized_dataset_creation_frame

    next_method_button = ttk.Button(piis_frame, text=buttom_text, command=next_command, style='my.TButton')
    next_method_button.pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    frame.update()

    return piis_frame

def find_piis():

    global columns_still_to_check
    global search_method
    global next_search_method
    global columns_where_to_replace_piis
    global piis_frame

    #Update search method (considering find_piis() is recurrently called)
    search_method = next_search_method

    #Add a 'Working on it...' message
    if (search_method == COLUMNS_NAMES_SEARCH_METHOD):
        display_message('Working on it...', first_view_frame)
    else:
        display_message('Working on it...', piis_frame)


    #Figure out what method for finding pii to use
    if (search_method == COLUMNS_NAMES_SEARCH_METHOD):

        #Check if surveyCTO vars should be considered
        if(check_survey_cto_checkbutton_var.get()==0):
            columns_still_to_check = [column for column in dataset.columns if column not in PII_data_processor.get_surveycto_restricted_vars()]
        else:
            columns_still_to_check = dataset.columns

        #Find piis basen on column names
        #If we are not checking locations populations, then we do include locations column in the next search
        consider_locations_col = 1 if check_locations_pop_checkbutton_var.get()==0 else 0

        pii_candidates = PII_data_processor.find_piis_based_on_column_name(dataset, label_dict, value_label_dict, columns_still_to_check, consider_locations_col)

        #Indicate next search method
        if(check_locations_pop_checkbutton_var.get()==1):
            next_search_method_button_text = "Continue: Find columns with potential PIIs for columns with locations"
            next_search_method = LOCATIONS_POPULATIONS_SEARCH_METHOD
        else:
            next_search_method_button_text = "Continue: Find columns with potential PIIs based on columns format"
            next_search_method = COLUMNS_FORMAT_SEARCH_METHOD

    elif(search_method == LOCATIONS_POPULATIONS_SEARCH_METHOD):
        pii_candidates = PII_data_processor.find_piis_based_on_locations_population(dataset, label_dict, columns_still_to_check, country_dropdown.get())
        next_search_method_button_text = "Continue: Find columns with potential PIIs based on columns format"
        next_search_method = COLUMNS_FORMAT_SEARCH_METHOD

    elif(search_method == COLUMNS_FORMAT_SEARCH_METHOD):
        pii_candidates = PII_data_processor.find_piis_based_on_column_format(dataset, label_dict, columns_still_to_check)

        if (not pii_search_in_unstructured_text_enabled or column_level_option_for_unstructured_text_checkbutton_var.get()==1):
            next_search_method_button_text = "Continue: Find columns with potential PIIs based on sparse entries"
            next_search_method = SPARSE_ENTRIES_SEARCH_METHOD
        else:
            next_search_method_button_text = "Continue: Find PIIs in open ended questions"
            next_search_method = UNSTRUCTURED_TEXT_SEARCH_METHOD

    elif(search_method == SPARSE_ENTRIES_SEARCH_METHOD):
        pii_candidates = PII_data_processor.find_piis_based_on_sparse_entries(dataset, label_dict, columns_still_to_check)
        next_search_method_button_text = "Create anonymized dataset"
        next_search_method = None

    elif(search_method == UNSTRUCTURED_TEXT_SEARCH_METHOD):
        piis_found_in_ustructured_text, columns_where_to_replace_piis = PII_data_processor.find_piis_unstructured_text(dataset, label_dict, columns_still_to_check, language_dropdown.get(), country_dropdown.get())
        next_search_method_button_text = "Create anonymized dataset"
        next_search_method = None
        pii_candidates = None


    #UPDATE VIEW

    #Remove previous view
    if (search_method == COLUMNS_NAMES_SEARCH_METHOD):
        first_view_frame.pack_forget()
    else:
        piis_frame.pack_forget()

    #Create new frame
    if(search_method != UNSTRUCTURED_TEXT_SEARCH_METHOD):
        piis_frame = create_piis_frame(pii_candidates=pii_candidates, next_search_method=next_search_method, next_search_method_button_text=next_search_method_button_text)
    else:
        piis_frame = create_unstructured_piis_frame(piis_found_in_ustructured_text=piis_found_in_ustructured_text, next_search_method=next_search_method, next_search_method_button_text=next_search_method_button_text)

def restart_program():
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    python = tk.sys.executable
    os.execl(python, python, * tk.sys.argv)

def window_setup(master):

    global window_width
    global window_height

    #Add window title
    master.title(app_title)

    #Add window icon
    if hasattr(sys, "_MEIPASS"):
        icon_location = os.path.join(sys._MEIPASS, 'app_icon.ico')
    else:
        icon_location = 'app_icon.ico'
    master.iconbitmap(icon_location)

    #Set window position and max size
    window_width, window_height = master.winfo_screenwidth(), master.winfo_screenheight()
    # master.geometry("%dx%d+0+0" % (window_width, window_height))
    master.state('zoomed')


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
    helpmenu.add_command(label="About", command=about)
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


def create_first_view_page(internet_connection):

    global check_survey_cto_checkbutton_var
    global check_locations_pop_checkbutton_var
    global column_level_option_for_unstructured_text_checkbutton_var
    global keep_unstructured_text_option_checkbutton_var

    global country_dropdown
    global language_dropdown

    first_view_frame = tk.Frame(master=frame, bg="white")
    first_view_frame.pack(anchor='nw', padx=(0, 0), pady=(0, 0))#padx=(30, 30), pady=(0, 5))

    #Add intro text
    intro_text_1_label = ttk.Label(first_view_frame, text=intro_text, wraplength=746, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel')
    intro_text_1_label.pack(anchor='nw', padx=(30, 30), pady=(0, 12))

    intro_text_2_label = ttk.Label(first_view_frame, text=intro_text_p2, wraplength=746, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel')
    intro_text_2_label.pack(anchor='nw', padx=(30, 30), pady=(0, 12))

    #Labels and checkbox for settings
    settings_label = ttk.Label(first_view_frame, text="Settings:", wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel')
    settings_label.pack(anchor='nw', padx=(30, 30), pady=(0, 10))

    if pii_search_in_unstructured_text_enabled:
        #Create a frame for the language selection
        language_frame = tk.Frame(master=first_view_frame, bg="white")
        language_frame.pack(anchor='nw', padx=(30, 30), pady=(0, 5))

        ttk.Label(language_frame, text='In which language are the answers in the dataset?', wraplength=546, justify=tk.LEFT, font=("Calibri", 10), style='my.TLabel').grid(row=0, column = 0, sticky = 'w', pady=(0,2))

        language_dropdown = tk.StringVar(language_frame)
        w = ttk.OptionMenu(language_frame, language_dropdown, SPANISH, ENGLISH, SPANISH, OTHER, style='my.TMenubutton').grid(row=0, column = 1, sticky = 'w', pady=(0,2))

    #Create a frame for country selection
    country_frame = tk.Frame(master=first_view_frame, bg="white")
    country_frame.pack(anchor='nw', padx=(30, 30), pady=(0, 5))

    ttk.Label(country_frame, text='In which country was this survey run?', wraplength=546, justify=tk.LEFT, font=("Calibri", 10), style='my.TLabel').grid(row=0, column = 0, sticky = 'w', pady=(0,2))

    country_dropdown = tk.StringVar(country_frame)
    w = ttk.OptionMenu(country_frame, country_dropdown, MEXICO, *ALL_COUNTRIES, OTHER, style='my.TMenubutton').grid(row=0, column = 1, sticky = 'w', pady=(0,2))

    #Labels and checkbox for options
    options_label = ttk.Label(first_view_frame, text="Options:", wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel')
    options_label.pack(anchor='nw', padx=(30, 30), pady=(0, 10))

    #SurveyCTO vars option
    check_survey_cto_checkbutton_var = tk.IntVar()
    check_survey_cto_checkbutton = tk.Checkbutton(first_view_frame, text="Consider surveyCTO variables for PII detection (ex: 'deviceid', 'subscriberid', 'simid', 'duration','starttime').",
            bg="white",
            activebackground="white",
            variable=check_survey_cto_checkbutton_var,
            onvalue=1, offvalue=0)
    check_survey_cto_checkbutton.pack(anchor='nw', padx=(30, 30), pady=(0, 10))

    #Check locations population option
    check_locations_pop_checkbutton_var = tk.IntVar()
    check_locations_pop_checkbutton = tk.Checkbutton(first_view_frame, text="Flag locations columns (ex: Village) as PII only if population of a location is under 20,000 [Default is to flag all locations columns].",
            bg="white",
            activebackground="white",
            variable=check_locations_pop_checkbutton_var,
            onvalue=1,
            offvalue=0)

    if internet_connection:
        check_locations_pop_checkbutton.pack(anchor='nw', padx=(30, 30), pady=(0, 10))


    if pii_search_in_unstructured_text_enabled:

        #Option related to unstructured text
        unstructured_text_label = ttk.Label(first_view_frame, text="What would you like to do respect to searching PIIs in open ended questions (unstructured text)?", wraplength=546, justify=tk.LEFT, font=("Calibri Italic", 10), style='my.TLabel')
        if internet_connection:
            unstructured_text_label.pack(anchor='nw', padx=(30, 30), pady=(0, 10))

        def column_level_option_for_unstructured_text_checkbutton_command():

            #If both are now off, reselect this one
            if(column_level_option_for_unstructured_text_checkbutton_var.get()==0 and keep_unstructured_text_option_checkbutton_var.get()==0):
                messagebox.showinfo("Error", "You must have one option selected")
                column_level_option_for_unstructured_text_checkbutton_var.set(True)

            #If the other one is on, turn it off.
            if(column_level_option_for_unstructured_text_checkbutton_var.get()==1 and keep_unstructured_text_option_checkbutton_var.get()==1):
                keep_unstructured_text_option_checkbutton.deselect()


        column_level_option_for_unstructured_text_checkbutton_var = tk.IntVar(value=1)
        column_level_option_for_unstructured_text_checkbutton_text = "Identify open ended questions and choose what to do with them at the column level (either drop or keep the whole column)"
        column_level_option_for_unstructured_text_checkbutton = tk.Checkbutton(first_view_frame,
            text=column_level_option_for_unstructured_text_checkbutton_text,
            bg="white",
            activebackground="white",
            variable=column_level_option_for_unstructured_text_checkbutton_var,
            onvalue=1,
            offvalue=0,
            command = column_level_option_for_unstructured_text_checkbutton_command)

        if internet_connection:
            column_level_option_for_unstructured_text_checkbutton.pack(anchor='nw', padx=(30, 30), pady=(0, 10))

        def keep_unstructured_text_option_checkbutton_command():

           #If both are now off, reselect this one
            if(column_level_option_for_unstructured_text_checkbutton_var.get()==0 and keep_unstructured_text_option_checkbutton_var.get()==0):
                messagebox.showinfo("Error", "You must have one option selected")
                keep_unstructured_text_option_checkbutton_var.set(True)

            else:#Disable other option
                column_level_option_for_unstructured_text_checkbutton.deselect()


        keep_unstructured_text_option_checkbutton_var = tk.IntVar(value=0)
        keep_unstructured_text_option_checkbutton_text = "Keep columns with open ended questions, but replace any PIIs found on them with a 'XXXX' string [Slow process, use only if ryou really need to keep unstructured text]"
        keep_unstructured_text_option_checkbutton = tk.Checkbutton(first_view_frame,
            text=keep_unstructured_text_option_checkbutton_text,
            bg="white",
            activebackground="white",
            variable=keep_unstructured_text_option_checkbutton_var,
            onvalue=1,
            offvalue=0,
            command=keep_unstructured_text_option_checkbutton_command)

        if internet_connection:
            keep_unstructured_text_option_checkbutton.pack(anchor='nw', padx=(30, 30), pady=(0, 10))


    def import_file():

        global dataset
        global dataset_path
        global label_dict
        global value_label_dict
        global next_search_method
        global columns_still_to_check

        dataset_path = askopenfilename()

        #If no file was selected, do nothing
        if not dataset_path:
            return

        display_message("Importing file...", first_view_frame)

        #Scroll down
        canvas.yview_moveto( 1 )
        frame.update()

        #Read file
        reading_status, reading_content = PII_data_processor.import_file(dataset_path)

        if(reading_status is False):
            display_message(reading_content[ERROR_MESSAGE], first_view_frame)
            return
        else:
            display_message("Success reading file: "+dataset_path, first_view_frame)
            dataset = reading_content[DATASET]
            label_dict = reading_content[LABEL_DICT]
            value_label_dict = reading_content[VALUE_LABEL_DICT]
            columns_still_to_check = dataset.columns

        #Creat bottom to find piis based on columns names
        next_search_method = COLUMNS_NAMES_SEARCH_METHOD
        buttom_text = "Find PIIs!"

        find_piis_next_step_button = ttk.Button(first_view_frame, text=buttom_text, command=find_piis, style='my.TButton')
        find_piis_next_step_button.pack(anchor='nw', padx=(30, 30), pady=(0, 5))

        #Scroll down
        frame.update()
        canvas.yview_moveto( 1 )

    #Labels and buttoms to run app
    start_application_label = ttk.Label(first_view_frame, text="Run application: ", wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel')
    start_application_label.pack(anchor='nw', padx=(30, 30), pady=(0, 10))

    select_dataset_button = ttk.Button(first_view_frame, text="Select Dataset", command=import_file, style='my.TButton')
    select_dataset_button.pack(anchor='nw', padx=(30, 30), pady=(0, 5))


    print(f'Internet connection: {internet_connection}')
    if(internet_connection is False):
        messagebox.showinfo("Message", "No internet connection, some features are diabled")

    return first_view_frame

def check_for_updates():
    if internet_connection:
        #Get version of latest release
        response = requests.get("https://api.github.com/repos/PovertyAction/PII_detection/releases/latest")
        latest_version = response.json()["tag_name"]

        #Case it has a v before version number, remove it
        latest_version = latest_version.replace("v","")

        #Check if this version_number is different to latest
        if version_number != latest_version:

           messagebox.showinfo("Message", "Version "+latest_version+ " is available. You can uninstall this version from Control Panel and download latest from https://github.com/PovertyAction/PII_detection/releases/latest")

if __name__ == '__main__':

    #Check internet connection
    internet_connection = PII_data_processor.internet_on()

    # Create GUI window
    root = tk.Tk()

    window_setup(root)

    menubar_setup(root)

    window_style_setup(root)

    # Create canvas where app will displayed
    canvas = tk.Canvas(root, width=window_width, height=window_height, bg="white")
    canvas.pack(side="left", fill="both", expand=True)

    # Create main frame inside canvas
    frame = tk.Frame(canvas, width=window_width, height=window_height, bg="white")
    frame.pack(side="left", fill="both", expand=True)

    #Add scrollbar
    canvas.create_window(0,0, window=frame, anchor="nw")
    add_scrollbar(root, canvas, frame)

    #Add logo
    if hasattr(tk.sys, "_MEIPASS"):
        logo_location = os.path.join(sys._MEIPASS, 'ipa_logo.jpg')
    else:
        logo_location = 'ipa_logo.jpg'
    logo = ImageTk.PhotoImage(Image.open(logo_location).resize((147, 71), Image.ANTIALIAS)) # Source is 2940 x 1416
    tk.Label(frame, image=logo, borderwidth=0).pack(anchor="nw", padx=(30, 30), pady=(30, 0))

    #Add app title
    app_title_label = ttk.Label(frame, text=app_title, wraplength=536, justify=tk.LEFT, font=("Calibri", 13, 'bold'), style='my.TLabel')
    app_title_label.pack(anchor='nw', padx=(30, 30), pady=(30, 10))

    #Create first view page
    first_view_frame = create_first_view_page(internet_connection)

    #Check for updates of this program
    check_for_updates()

    # Constantly looping event listener
    root.mainloop()
