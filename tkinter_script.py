# Imports and Set-up
import sys
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from PIL import ImageTk, Image
import PII_data_processor

import webbrowser
import os

intro_text = "This script is meant to assist in the detection of PII (personally identifiable information) and subsequent removal from a dataset. This is an alpha program, not fully tested yet."
intro_text_p2 = "You will first load a dataset that might contain PII variables. The system will try to identify the PII candidates. Please indicate if you would like to Drop, Encode or Keep them to then generate a new de-identified dataset."#, built without access to datasets containing PII on which to test or train it. Please help improve the program by filling out the survey on your experience using it (Help -> Provide Feedback)."
app_title = "IPA's PII Detector - v2.6"

window_width = 1086
window_height = 766

#Maps pii to action to do with them
pii_candidates_to_dropdown_element = {}

#Dataset we are working with
dataset = None
dataset_path = None
new_file_path = None
label_dict = None


widgets_visible_ready_to_remove = []

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

def tkinter_display_pii_candidates(pii_candidates, label_dict):

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
        w = ttk.OptionMenu(pii_frame, dropdown, "Drop", "Drop", "Encode", "Keep", style='my.TMenubutton').grid(row=idx, column = 2, sticky = 'w', pady=(0,2))

        pii_candidates_to_dropdown_element[pii_candidate] = dropdown

    frame.update()

    return pii_frame


def open_deidentified_file():
    os.system("start " + new_file_path)

def create_anonymized_dataset():

    creating_new_dataset_message = tkinter_display("Creating new dataset...")
    widgets_visible_ready_to_remove.append(creating_new_dataset_message)
    #Automatic scroll down
    canvas.yview_moveto( 1 )

    global new_file_path

    #We create a new dictionary that maps pii_candidate_to_action based on value of dropdown elements
    pii_candidates_to_action = {}
    for pii, dropdown_elem in pii_candidates_to_dropdown_element.items():
        pii_candidates_to_action[pii] = dropdown_elem.get()
    
    new_file_path = PII_data_processor.create_anonymized_dataset(dataset, label_dict, dataset_path, pii_candidates_to_action)
    
    clear_window_removing_all_widgets()

    if(new_file_path):
        tkinter_display_title("Congratulations! Task ready!")
        tkinter_display("The new dataset has been created and saved in the original file directory.\nYou will also find a log file describing the detection process.\nIf you encoded variables, you will find a .csv file that maps original to encoded values.")
        ttk.Button(frame, text="Open de-identified dataset", command=open_deidentified_file, style='my.TButton').pack(anchor='nw', padx=(30, 30), pady=(0, 5))        
        
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

def read_file_and_find_piis():
    global dataset
    global dataset_path
    global label_dict

    dataset_path = askopenfilename()

    #If no file was selected, do nothing
    if not dataset_path:
        return

    reading_file_label = tkinter_display("Reading file and looking for piis...")
    widgets_visible_ready_to_remove.append(reading_file_label)

    reading_status, pii_candidates_or_message, dataset, label_dict = PII_data_processor.read_file_and_find_piis(dataset_path)

    clear_window_removing_all_widgets()
    
    if(reading_status is False):
        error_message = pii_candidates_or_message
        tkinter_display(error_message)
        return
    
    pii_candidates = pii_candidates_or_message

    if(len(pii_candidates)==0):
        tkinter_display_title('No PII candidates found.')
        return

    #Create title, instructions, and display piis
    pii_candidates_title_label = tkinter_display_title('PII candidates found:')
    pii_candidates_instruction_label = tkinter_display('For each PII candidate, select an action and then press the "Create anonymized dataset" button')

    piis_frame = tkinter_display_pii_candidates(pii_candidates, label_dict)

    #Show a create anonymized dataframe buttom
    create_anonymized_df_button = ttk.Button(frame, text="Create anonymized dataset", command=create_anonymized_dataset, style='my.TButton')
    create_anonymized_df_button.pack(anchor='nw', padx=(30, 30), pady=(0, 5))
    frame.update()

    #Add all new widgets to list for future removal of canvas
    widgets_visible_ready_to_remove.extend([pii_candidates_title_label, pii_candidates_instruction_label, piis_frame, create_anonymized_df_button])

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
    # master.resizable(False, False)

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
    start_application_label = ttk.Label(frame, text="Start Application: ", wraplength=546, justify=tk.LEFT, font=("Calibri", 12, 'bold'), style='my.TLabel')
    start_application_label.pack(anchor='nw', padx=(30, 30), pady=(0, 10))
    
    select_dataset_button = ttk.Button(frame, text="Select Dataset", command=read_file_and_find_piis, style='my.TButton')
    select_dataset_button.pack(anchor='nw', padx=(30, 30), pady=(0, 5))

    #Add widgets to list of widgets to remove later on
    widgets_visible_ready_to_remove.extend([intro_text_1_label, intro_text_2_label, start_application_label, select_dataset_button])

    # Constantly looping event listener
    root.mainloop()  