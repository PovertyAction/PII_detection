# Imports and Set-up
import sys
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
from PIL import ImageTk, Image
import webbrowser
import os

import PII_data_processor
import find_piis_in_unstructured_text
from constant_strings import *

intro_text = "This script is meant to assist in the detection of PII (personally identifiable information) and subsequent removal from a dataset. This is an alpha program, not fully tested yet."
intro_text_p2 = "You will first load a dataset that might contain PII variables. The system will try to identify the PII candidates. Please indicate if you would like to Drop, Encode or Keep them to then generate a new de-identified dataset."#, built without access to datasets containing PII on which to test or train it. Please help improve the program by filling out the survey on your experience using it (Help -> Provide Feedback)."
app_title = "IPA's PII Detector - v0.2.12"

#Maps pii to action to do with them
pii_candidates_to_dropdown_element = {}

#Dataset we are working with
dataset = None
dataset_path = None
new_file_path = None
label_dict = None

widgets_visible_ready_to_remove = []
find_piis_options={}

window_width=None
window_height=None

columns_where_to_replace_piis = None

piis_in_text_box = None

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

def tkinter_display_pii_candidates(pii_candidates, label_dict, default_dropdown_option="Drop"):

    #Create a frame for the pii labels and actions dropdown
    #padx determines space between label and dropdown
    pii_frame = tk.Frame(master=frame, bg="white")
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

def create_anonymized_dataset():

    creating_new_dataset_message = tkinter_display("Creating new dataset...")
    widgets_visible_ready_to_remove.append(creating_new_dataset_message)
    #Automatic scroll down
    canvas.yview_moveto( 1 )
    frame.update()

    global new_file_path

    #We create a new dictionary that maps pii_candidate_to_action based on value of dropdown elements
    pii_candidates_to_action = {}
    for pii, dropdown_elem in pii_candidates_to_dropdown_element.items():
        pii_candidates_to_action[pii] = dropdown_elem.get()
    
    #Capture words to replace in unstructured text
    # if(keep_unstructured_text_option_checkbutton_var.get()==1):
    piis_found_in_ustructured_text = [w.strip() for w in piis_in_text_box.get("1.0", "end").split(',')]

    new_file_path = PII_data_processor.create_anonymized_dataset(dataset, label_dict, dataset_path, pii_candidates_to_action, columns_where_to_replace_piis, piis_found_in_ustructured_text)
    
    clear_window_removing_all_widgets()

    if(new_file_path):
        tkinter_display_title("Congratulations! Task ready!")
        tkinter_display("The new dataset has been created and saved in the original file directory.\nYou will also find a log file describing the detection process.\nIf you encoded variables, you will find a .csv file that maps original to encoded values.\n")
        
        tkinter_display("Do you want to work on a new file? Click Restart buttom.")
        ttk.Button(frame, text="Restart program", command=restart_program, style='my.TButton').pack(anchor='nw', padx=(30, 30), pady=(0, 5))
        
        #Create a frame for the survey link
        survey_frame = tk.Frame(master=frame, bg="white")
        survey_frame.pack(anchor='nw', padx=(30, 30), pady=(0, 5))
        survey_text = "Can you provide feedback to improve the app? Please click "
        ttk.Label(survey_frame, text=survey_text, wraplength=546, justify=tk.LEFT, font=("Calibri Italic", 11), style='my.TLabel').grid(row=0, column = 0)
        link = tk.Label(survey_frame, text="here", fg="blue", font=("Calibri Italic", 11), cursor="hand2", background='white')
        link.grid(row = 0, column=1)
        link.bind("<Button-1>", lambda e: open_survey())

        frame.update()

def clear_window_removing_all_widgets():
    #Remove widgets currently visible
    for widget in widgets_visible_ready_to_remove:
        widget.pack_forget()
    widgets_visible_ready_to_remove.clear()

    canvas.yview_moveto(0)

def display_pii_found_in_ustructured_text(piis_found_in_ustructured_text):
    global piis_in_text_box
    piis_in_text_box = tk.Text(frame, height=20, width=70)
    piis_in_text_box.pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    piis_in_text_box.insert(tk.END, ", ".join(piis_found_in_ustructured_text))
    return piis_in_text_box


def find_piis():
    global dataset
    global dataset_path
    global label_dict
    global value_label_dict
    global columns_still_to_check
    
    global search_method
    global next_search_method

    global columns_where_to_replace_piis

    #Update search method (considering find_piis() is recurrently called)
    search_method = next_search_method

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
        pii_candidates = PII_data_processor.find_piis_based_on_locations_population(dataset, label_dict, columns_still_to_check)
        next_search_method_button_text = "Continue: Find columns with potential PIIs based on columns format"
        next_search_method = COLUMNS_FORMAT_SEARCH_METHOD

    elif(search_method == COLUMNS_FORMAT_SEARCH_METHOD):
        pii_candidates = PII_data_processor.find_piis_based_on_column_format(dataset, label_dict, columns_still_to_check)

        if(column_level_option_for_unstructured_text_checkbutton_var.get()==1):
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
        piis_found_in_ustructured_text, columns_where_to_replace_piis = find_piis_in_unstructured_text.find_piis(dataset, label_dict, columns_still_to_check, language_dropdown.get(), country_dropdown.get())
        next_search_method_button_text = "Create anonymized dataset"
        next_search_method = None

    #Clean and display pii found
    clear_window_removing_all_widgets()

    #If we are displaying PII columns, which is the case for all search methods but the unstructured text one
    if search_method != UNSTRUCTURED_TEXT_SEARCH_METHOD:
        pii_candidates_title_label = tkinter_display_title('PII candidates found using '+search_method+':')
        widgets_visible_ready_to_remove.extend([pii_candidates_title_label])
        
        if(len(pii_candidates)==0):
            no_pii_label = tkinter_display('No PII candidates found.')
            widgets_visible_ready_to_remove.extend([no_pii_label])
        else:
            #Create title, instructions, and display piis
            pii_candidates_instruction_label = tkinter_display('For each PII candidate, select an action')
            piis_frame = tkinter_display_pii_candidates(pii_candidates, label_dict)
            widgets_visible_ready_to_remove.extend([pii_candidates_instruction_label, piis_frame])


        #Update columns_still_to_check, removing pii candidates found
        columns_still_to_check = [c for c in columns_still_to_check if c not in pii_candidates]
    
    else: #We are in the unstructure text search. Display PIIs found.
        t1 = tkinter_display("This are the potential PIIs found in open ended questions and which will be replaced by 'XXXX' in the new de-identified dataset")
        t2 = tkinter_display("Feel free to edit the list if you find wrongly identified PIIs, just keep words separated by commas.")
        t3 = display_pii_found_in_ustructured_text(piis_found_in_ustructured_text)
        widgets_visible_ready_to_remove.extend([t1, t2, t3])


    if(next_search_method is not None):
        buttom_text = next_search_method_button_text
        next_command = find_piis
    else:
        buttom_text = 'Create anonymized dataset'
        next_command = create_anonymized_dataset

    next_method_button = ttk.Button(frame, text=buttom_text, command=next_command, style='my.TButton')
    next_method_button.pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    frame.update()

    widgets_visible_ready_to_remove.extend([next_method_button])


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
        value_label_dict = reading_content[VALUE_LABEL_DICT]
        columns_still_to_check = dataset.columns

    #Creat bottom to find piis based on columns names
    next_search_method = COLUMNS_NAMES_SEARCH_METHOD
    buttom_text = "Find PIIs!"

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

    global window_width
    global window_height

    #Add window title
    master.title(app_title)
    
    #Add window icon
    if hasattr(sys, "_MEIPASS"):
        icon_location = os.path.join(sys._MEIPASS, 'app.ico')
    else:
        icon_location = 'app.ico'
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
    
    intro_text_1_label = ttk.Label(frame, text=intro_text, wraplength=746, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel')
    intro_text_1_label.pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    

    intro_text_2_label = ttk.Label(frame, text=intro_text_p2, wraplength=746, justify=tk.LEFT, font=("Calibri", 11), style='my.TLabel')
    intro_text_2_label.pack(anchor='nw', padx=(30, 30), pady=(0, 12))
    
    #Labels and checkbox for settings
    settings_label = ttk.Label(frame, text="Settings:", wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel')
    settings_label.pack(anchor='nw', padx=(30, 30), pady=(0, 10))

    #Create a frame for the language selection
    language_frame = tk.Frame(master=frame, bg="white")
    language_frame.pack(anchor='nw', padx=(30, 30), pady=(0, 5))

    ttk.Label(language_frame, text='In which language are the answers in the dataset?', wraplength=546, justify=tk.LEFT, font=("Calibri", 10), style='my.TLabel').grid(row=0, column = 0, sticky = 'w', pady=(0,2))

    language_dropdown = tk.StringVar(language_frame)
    w = ttk.OptionMenu(language_frame, language_dropdown, SPANISH, ENGLISH, SPANISH, OTHER, style='my.TMenubutton').grid(row=0, column = 1, sticky = 'w', pady=(0,2))

    #Create a frame for country selection
    country_frame = tk.Frame(master=frame, bg="white")
    country_frame.pack(anchor='nw', padx=(30, 30), pady=(0, 5))

    ttk.Label(country_frame, text='In which country was this survey run?', wraplength=546, justify=tk.LEFT, font=("Calibri", 10), style='my.TLabel').grid(row=0, column = 0, sticky = 'w', pady=(0,2))

    country_dropdown = tk.StringVar(country_frame)
    w = ttk.OptionMenu(country_frame, country_dropdown, MEXICO, *ALL_COUNTRIES, OTHER, style='my.TMenubutton').grid(row=0, column = 1, sticky = 'w', pady=(0,2))


    #Labels and checkbox for options
    options_label = ttk.Label(frame, text="Options:", wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel')
    options_label.pack(anchor='nw', padx=(30, 30), pady=(0, 10))
    
    #SurveyCTO vars option
    check_survey_cto_checkbutton_var = tk.IntVar()
    check_survey_cto_checkbutton = tk.Checkbutton(frame, text="Consider surveyCTO variables for PII detection (ex: 'deviceid', 'subscriberid', 'simid', 'duration','starttime').",
            bg="white",
            activebackground="white",
            variable=check_survey_cto_checkbutton_var,
            onvalue=1, offvalue=0)
    check_survey_cto_checkbutton.pack(anchor='nw', padx=(30, 30), pady=(0, 10))

    def check_locations_pop_checkbutton_command():
        if PII_data_processor.internet_on() is False:
            messagebox.showinfo("Error", "Feature requires internet connection")
            check_locations_pop_checkbutton.deselect()
    #Check locations population option
    check_locations_pop_checkbutton_var = tk.IntVar()
    check_locations_pop_checkbutton = tk.Checkbutton(frame, text="Flag locations columns (ex: Village) as PII only if population of a location is under 20,000 [Default is to flag all locations columns].",
            bg="white",
            activebackground="white",
            variable=check_locations_pop_checkbutton_var,
            onvalue=1,
            offvalue=0,
            command = check_locations_pop_checkbutton_command)
    check_locations_pop_checkbutton.pack(anchor='nw', padx=(30, 30), pady=(0, 10))


    #Option related to unstructured text
    unstructured_text_label = ttk.Label(frame, text="What would you like to do respect to searching PIIs in open ended questions (unstructured text)?", wraplength=546, justify=tk.LEFT, font=("Calibri Italic", 10), style='my.TLabel')
    unstructured_text_label.pack(anchor='nw', padx=(30, 30), pady=(0, 10))

    def column_level_option_for_unstructured_text_checkbutton_command():
        print("As soon after the click:")
        print(f'column_level_option_for_unstructured_text_checkbutton_var {column_level_option_for_unstructured_text_checkbutton_var.get()}')
        print(f'keep_unstructured_text_option_checkbutton_var {keep_unstructured_text_option_checkbutton_var.get()}')

        #If both are now off, reselect this one
        if(column_level_option_for_unstructured_text_checkbutton_var.get()==0 and keep_unstructured_text_option_checkbutton_var.get()==0):
            messagebox.showinfo("Error", "You must have one option selected")
            column_level_option_for_unstructured_text_checkbutton_var.set(True)

        #If the other one is on, turn it off.
        if(column_level_option_for_unstructured_text_checkbutton_var.get()==1 and keep_unstructured_text_option_checkbutton_var.get()==1):
            keep_unstructured_text_option_checkbutton.deselect()

        print("At the end of the method:")
        print(f'column_level_option_for_unstructured_text_checkbutton_var {column_level_option_for_unstructured_text_checkbutton_var.get()}')
        print(f'keep_unstructured_text_option_checkbutton_var {keep_unstructured_text_option_checkbutton_var.get()}')


    def keep_unstructured_text_option_checkbutton_command():
        print("As soon after the click:")
        print(f'column_level_option_for_unstructured_text_checkbutton_var {column_level_option_for_unstructured_text_checkbutton_var.get()}')
        print(f'keep_unstructured_text_option_checkbutton_var {keep_unstructured_text_option_checkbutton_var.get()}')
        #If there is no internet connection, this feature should be disabled
        if PII_data_processor.internet_on() is False:
            messagebox.showinfo("Error", "Feature requires internet connection")
            keep_unstructured_text_option_checkbutton.deselect()
        else:
           #If both are now off, reselect this one
            if(column_level_option_for_unstructured_text_checkbutton_var.get()==0 and keep_unstructured_text_option_checkbutton_var.get()==0):
                messagebox.showinfo("Error", "You must have one option selected")
                keep_unstructured_text_option_checkbutton_var.set(True)

            else:#Disable other option
                column_level_option_for_unstructured_text_checkbutton.deselect()
        
        print("At the end of the method:")
        print(f'column_level_option_for_unstructured_text_checkbutton_var {column_level_option_for_unstructured_text_checkbutton_var.get()}')
        print(f'keep_unstructured_text_option_checkbutton_var {keep_unstructured_text_option_checkbutton_var.get()}')

    column_level_option_for_unstructured_text_checkbutton_var = tk.IntVar(value=1)
    column_level_option_for_unstructured_text_checkbutton_text = "Identify open ended questions and choose what to do with them at the column level (either drop or keep the whole column)"
    column_level_option_for_unstructured_text_checkbutton = tk.Checkbutton(frame,
        text=column_level_option_for_unstructured_text_checkbutton_text,
        bg="white",
        activebackground="white",
        variable=column_level_option_for_unstructured_text_checkbutton_var,
        onvalue=1,
        offvalue=0,
        command = column_level_option_for_unstructured_text_checkbutton_command)

    column_level_option_for_unstructured_text_checkbutton.pack(anchor='nw', padx=(30, 30), pady=(0, 10))

    keep_unstructured_text_option_checkbutton_var = tk.IntVar(value=0)
    keep_unstructured_text_option_checkbutton_text = "Keep columns with open ended questions, but replace any PIIs found on them with a 'XXXX' string [Slow process, use only if really need to keep unstructured text]"
    keep_unstructured_text_option_checkbutton = tk.Checkbutton(frame,
        text=keep_unstructured_text_option_checkbutton_text,
        bg="white",
        activebackground="white",
        variable=keep_unstructured_text_option_checkbutton_var,
        onvalue=1,
        offvalue=0,
        command=keep_unstructured_text_option_checkbutton_command)
    keep_unstructured_text_option_checkbutton.pack(anchor='nw', padx=(30, 30), pady=(0, 10))

    #Labels and buttoms to run app
    start_application_label = ttk.Label(frame, text="Run application: ", wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel')
    start_application_label.pack(anchor='nw', padx=(30, 30), pady=(0, 10))
    
    select_dataset_button = ttk.Button(frame, text="Select Dataset", command=import_file, style='my.TButton')
    select_dataset_button.pack(anchor='nw', padx=(30, 30), pady=(0, 5))

    #Add widgets to list of widgets to remove later on
    widgets_visible_ready_to_remove.extend([intro_text_1_label,
        intro_text_2_label,
        start_application_label,
        select_dataset_button,
        options_label,
        check_survey_cto_checkbutton,
        check_locations_pop_checkbutton,
        unstructured_text_label,
        column_level_option_for_unstructured_text_checkbutton,
        keep_unstructured_text_option_checkbutton,
        language_frame,
        settings_label,
        country_frame])

    # Constantly looping event listener
    root.mainloop()  