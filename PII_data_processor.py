
# coding: utf-8

# # Instructions
# 
# 1. This script is meant to assist in the detection of PII (personally identifiable information) and subsequent removal from a dataset.
# 
# 2. If running it in Jupyter Notebook, press 'shift + return' or 'shift + enter' to navigate through the script and fill in the prompts when asked.
# 
# 3. If you have any errors or feedback, contact jjacobson@poverty-action.org or researchsupport@poverty-action.org
# 
# <b>This is a tool to help you identify PII, but ensuring the dataset is devoid of PII is ultimately still your responsibility.</b> Be extremely careful with potential identifiers, especially geographic, because they can sometimes be combined with other variables to become identifying.
# 
# (If this script is loaded via Jupyter Notebook, despite loading in the browser, it is running locally on your machine and will continue to run fine regardless of internet access.)

# # Import and Set-up

# In[1]:

#from __main__ import *
#from tkinter_script import tkinter_display

import nltk
import pandas as pd
import numpy as np
import os
from nltk.stem.porter import *
from tqdm import tqdm
from IPython.display import display, HTML
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"
import time

def smart_print(the_message, messages_pipe = None):
    if __name__ == "__main__":
        print(the_message)
    else:
        messages_pipe.send(the_message)

def smart_return(to_return, function_pipe = None):
    if __name__ != "__main__":
        function_pipe.send(to_return)
    else:
        if len(to_return) == 2:
            return to_return[0], to_return[1]
        else:
            return to_return

# This should be able to use variables specified in my original file
def import_dataset(dataset_path_var, messages_pipe = None):
    # returns dataset
    
    if __name__ != "__main__":
        dataset_path = dataset_path_var.recv()
    else:
        dataset_path = dataset_path_var

    dataset, label_dict, value_label_dict = False, False, False
    raise_error = False
    status_message = False

    if dataset_path.endswith(('"', "'")):
        dataset_path = dataset_path[1:-1] 

    dataset_path_l = dataset_path.lower()

    try:
        if dataset_path_l.endswith(('xlsx', 'xls')):
            dataset = pd.read_excel(dataset_path)
        elif dataset_path_l.endswith('csv'):
            dataset = pd.read_csv(dataset_path)
        elif dataset_path_l.endswith('dta'):
            try:
                dataset = pd.read_stata(dataset_path)
            except ValueError:
                dataset = pd.read_stata(dataset_path, convert_categoricals=False)
            label_dict = pd.io.stata.StataReader(dataset_path).variable_labels()
            try:
                value_label_dict = pd.io.stata.StataReader(dataset_path).value_labels()
            except AttributeError:
                status_message = "No value labels detected. " # Not printed in the app, overwritten later.
        elif dataset_path_l.endswith(('xpt', '.sas7bdat')):
            dataset = pd.read_sas(dataset_path)
        elif dataset_path_l.endswith('vc'):
            status_message = "**ERROR**: This folder appears to be encrypted using VeraCrypt."
            raise Exception
        elif dataset_path_l.endswith('bc'):
            status_message = "**ERROR**: This file appears to be encrypted using Boxcryptor. Sign in to Boxcryptor and then select the file in your X: drive."
            raise Exception
        else:
            raise Exception

    except (FileNotFoundError, Exception):
        if status_message is False:
            status_message = '**ERROR**: This path appears to be invalid. If your folders or filename contain colons or commas, try renaming them or moving the file to a different location.'
        smart_print(status_message, messages_pipe)
        raise

    status_message = '**SUCCESS**: The dataset has been read successfully.'
    smart_print(status_message, messages_pipe)

    # ADJUST FOR THIS ON THE JUPYTER SIDE
    dataset_read_return = [dataset, dataset_path, label_dict, value_label_dict]

    smart_return(dataset_read_return, dataset_path_var)

# In[3]:

def initialize_lists(function_pipe = None):
    # returns possible_pii, restricted
    #smart_print('Initializing the variables.')
    
    possible_pii = []
    global yes_strings
    yes_strings = ['y', 'yes', 'Y', 'Yes']

    # Flagged strings from R script
    restricted_location = ["district", "country", "subcountry", "parish", "lc", "village", "community", "address", "gps", "lat", "log", "coord", "location", "house","compound", "panchayat", "name", "fname", "lname", "first_name", "last_name", "birth", "birthday", "bday", ]

    restricted_other = ["school","social","network","census","gender","sex","fax","email","url","child","beneficiary","mother","wife","father","husband"]

    # Flagged strings from Stata script
    restricted_stata = ['nam','add','vill','dist','phone','parish','loc','acc','plan','email','medic','health','insur','num','resid','contact','home','comment','spec','id','fo','enum', 'city', 'info', 'data', 'comm', 'count']

    # Flagged strings from IPA guideline document
    restricted_ipa = ['name', 'birth', 'phone', 'district', 'county', 'subcounty', 'parish', 'lc', 'village', 'community', 'address', 'gps', 'lat', 'lon', 'coord', 'location', 'house', 'compound', 'school', 'social', 'network', 'census', 'gender', 'sex', 'fax', 'email', 'ip', 'url', 'specify', 'comment']

    # Additions
    restricted_expansions = ['name', 'insurance', 'medical', 'number', 'enumerator', 'rand', 'random', 'child_age', 'uid', 'latitude', 'longitude', 'coordinates', 'web', 'website', 'hh', 'address', 'age', 'nickname', 'nick_name', 'firstname', 'lastname', 'sublocation', 'alternativecontact', 'division', 'gps', 'resp_name', 'resp_phone', 'head_name', 'headname', 'respname', 'subvillage', 'survey_location']
    restricted_spanish = ['apellidos', 'beneficiario', 'casa', 'censo', 'ciudad', 'comentario / coment', 'comunidad', 'contacto', 'contar', 'coordenadas', 'coordenadas', 'data', 'direccion', 'direccion', 'distrito', 'distrito', 'edad', 'edad_nino', 'email', 'encuestador', 'encuestador', 'escuela', 'colegio ', 'esposa', 'esposo', 'fax', 'fecha_nacimiento', 'fecha_nacimiento', 'fecha_nacimiento', 'genero', 'gps', 'hogar', 'id', 'identificador', 'identidad', 'informacion', 'ip', 'latitud', 'latitude', 'locacion', 'longitud', 'madre', 'medical', 'medico', 'nino', 'nombre', 'nombre', 'numero', 'padre', 'pag_web', 'pais', 'parroquia', 'plan', 'primer_nombre', 'random', 'red', 'salud', 'seguro', 'sexo', 'social', 'telefono', 'fono', 'tlfno', 'ubicacion', 'url', 'villa', 'web']
    restricted_swahili = ['jina', 'simu', 'mkoa', 'wilaya', 'kata', 'kijiji', 'kitongoji', 'vitongoji', 'nyumba', 'numba', 'namba', 'tarahe ya kuzaliwa', 'umri', 'jinsi', 'jinsia']

    restricted = restricted_location + restricted_other + restricted_stata + restricted_ipa + restricted_expansions + restricted_spanish + restricted_swahili
    restricted = list(set(restricted))
    
    smart_return([possible_pii, restricted], function_pipe)

# # String search with stemming

# In[4]:

def stem_restricted(restricted, function_pipe = None, messages_pipe = None):
# Identifies stems of restricted words and adds the stems to restricted list

    smart_print('Creating stems of restricted variable names.', messages_pipe)

    initialized_stemmer = PorterStemmer()
    restricted_stems = []
    for r in tqdm(restricted):
        restricted_stems.append(initialized_stemmer.stem(r).lower())

    restricted = restricted + restricted_stems
    restricted = list(set(restricted))
    
    smart_return([restricted, initialized_stemmer], function_pipe)

# In[5]:

def word_match_stemming(possible_pii, restricted, dataset, stemmer, function_pipe = None, messages_pipe = None):
# Looks for matches between variable names, variable name stems, restricted words, and restricted word stems
    smart_print('The word match with stemming algorithm is now running.', messages_pipe)
    
    for v in tqdm(dataset.columns):
        for r in restricted:
            if v.lower() in r or stemmer.stem(v).lower() in r:
                possible_pii.append(v)
    
    smart_print('**' + str(len(set(possible_pii))) + '**' + " total fields that may contain PII have now been identified.", messages_pipe)
    
    smart_return(possible_pii, function_pipe)


# # Fuzzy and Intelligent Partial Match

# In[6]:

# Function definitions

def split_by_word(search_term):
    return search_term.replace('-', ' ').replace('_', ' ').replace('  ', ' ').replace('  ', ' ').split(' ')

# def is_acronym(acronym, text):
#     text = text.lower()
#     acronym = acronym.lower()
#     text = split_by_word(text)
#     count = 0
    
#     for c in range(len(acronym)):
#         try:
#             if acronym[c] == text[c][0]:
#                 count += 1
#         except IndexError:
#             return False
#     if count == len(acronym):
#         return True
#     else:
#         return False
    
def levenshtein_distance(first, second):
    # Find the Levenshtein distance between two strings.
    insertion_cost = .5
#     if not is_acronym(first, second):
#         insertion_cost = .2
#         first = first.lower()
#         if first[-1] == 's':
#             if is_acronym(first.rstrip('s'), second):
#                 insertion_cost = 0
    
    first = first.lower()
    second = second.lower()
    if len(first) > len(second):
        first, second = second, first
    if len(second) == 0:
        return len(first)
    first_length = len(first) + 1
    second_length = len(second) + 1
    distance_matrix = [[0] * second_length for x in range(first_length)]
    for i in range(first_length):
        distance_matrix[i][0] = i
        for j in range(second_length):
            distance_matrix[0][j]=j
    for i in range(1, first_length):
        for j in range(1, second_length):
            deletion = distance_matrix[i-1][j] + 1
            insertion = distance_matrix[i][j-1] + insertion_cost
            substitution = distance_matrix[i-1][j-1]
            if first[i-1] != second[j-1]:
                substitution += 1
            distance_matrix[i][j] = min(insertion, deletion, substitution)
    return distance_matrix[first_length-1][second_length-1]

def compute_fuzzy_scores(search_term, restricted):
    match_list = []
    match_score_list = []
    for r in restricted:
        match_list.append(r)
        match_score_list.append(levenshtein_distance(search_term,r))   
    #print(match_list, match_score_list)
    return [match_list, match_score_list]

def best_fuzzy_match(word_list, score_list): #would eliminate this by implementing a priority queue
    lowest_score_index = score_list.index(min(score_list)) #index of lowest (best) score
    best_word_match = word_list[lowest_score_index] #use index to locate the best word
    del score_list[lowest_score_index] #remove the score from the list
    word_list.remove(best_word_match) #remove the word from the list
    return [best_word_match, word_list, score_list] #return the best word

def ordered_fuzzy_results(word_list, score_list):
    ordered_fuzzy_list = []
    ordered_score_list = []
    best_fuzzy_results = ['', word_list, score_list] #initial set_up for while loop call        
    while len(word_list) > 0:
        best_fuzzy_results = best_fuzzy_match(best_fuzzy_results[1], best_fuzzy_results[2])
        ordered_fuzzy_list.append(best_fuzzy_results[0])
        #ordered_score_list.append(best_fuzzy_results[2][word_list.index(best_fuzzy_results[0])])
    return ordered_fuzzy_list[:5]

def run_fuzzy_query(term, fuzzy_threshold, restricted):
    fuzzy_result = []
    words = split_by_word(term)
    for w in words:
        if len(w) <= 2:
            continue
        scored_list = compute_fuzzy_scores(w, restricted)
        if min(scored_list[1]) < fuzzy_threshold:
            final_result = ordered_fuzzy_results(scored_list[0], scored_list[1])
            fuzzy_result.append(final_result[0])
            
#     scored_list = compute_fuzzy_scores(term)
#     if min(scored_list[1]) < fuzzy_threshold:
#         final_result = ordered_fuzzy_results(scored_list[0], scored_list[1])
#         fuzzy_result.append(final_result[0])
        
    if len(fuzzy_result) == 0:
        return False
    else:
        return fuzzy_result
    #return final_result


# In[7]:

def fuzzy_partial_stem_match(possible_pii, restricted, dataset, stemmer, threshold = 0.75, function_pipe = None, messages_pipe = None):
# Looks for fuzzy and intelligent partial matches
# Recommended value is 0.75. Higher numbers (i.e. 4) will identify more possible PII, while lower numbers (i.e. 0.5) will identify less potential PII.

    smart_print('The fuzzy and intelligent partial matches with stemming algorithm is now running.', messages_pipe)

    for v in tqdm(dataset.columns):
        if run_fuzzy_query(v.lower(), threshold, restricted) != False:
            possible_pii.append(v)
        if run_fuzzy_query(stemmer.stem(v).lower(), threshold, restricted) != False:
            possible_pii.append(v)
            
    smart_print('**' + str(len(set(possible_pii))) + '**' + " total fields that may contain PII have now been identified.", messages_pipe)

    smart_return(possible_pii, function_pipe)


# # All Uniques

# In[8]:

def unique_entries(possible_pii, dataset, min_entries_threshold = 0.5, function_pipe = None, messages_pipe = None):
    # .5 (50%) is the minimum percent of values that must exist for a field to be considered as potential PII 
    # based on having unique values for each entry, you may customize this as desired (0.0-1.0)
    
    smart_print('The unique entries algorithm is now running.', messages_pipe)
    
    for v in tqdm(dataset.columns):
        if len(dataset[v]) == len(set(dataset[v])) and len(dataset[v].dropna())/len(dataset) > min_entries_threshold:
            possible_pii.append(v)
    
    smart_print('**' + str(len(set(possible_pii))) + '**' + " total fields that may contain PII have now been identified.", messages_pipe)
    
    smart_return(possible_pii, function_pipe)


# # Corpus Search & Categorization

# In[9]:

#names = pd.read_csv("Corpus & Categorizations/combined.csv", header=None, encoding='utf-8')

#p1 = pd.read_csv(r"D:\Dropbox\Work-Personal Sync\PII Detection\Corpus & Categorizations\0717182\nam_dict.txt", encoding='latin-1')

# pd.read_csv("D:\Dropbox\Work-Personal Sync\PII Detection\Corpus & Categorizations\allCountries.txt")

# path = 'D:\\Dropbox\\Work-Personal Sync\\PII Detection\\Corpus & Categorizations\\IPA Countries\\'
# filenames = os.listdir(path)
# #filenames# = filenames[2:4]

# for f in tqdm(filenames):
#      print(f)
#      temp = pd.read_table(path+f, header=None, encoding='latin-1', low_memory=False, delim_whitespace=True)#, usecols=[1])
#      #temp.to_csv(path+'narrow'+f, header=None, index=None, encoding='latin-1')

#pd.read_csv("D:\Dropbox\Work-Personal Sync\PII Detection\Corpus & Categorizations\IPA Countries\AF.csv", header=None)


# # Date Detection

# In[10]:

def date_detection(possible_pii, dataset, function_pipe = None, messages_pipe = None):
    
    smart_print('The date detection algorithm is now running.', messages_pipe)
    
    possible_pii = possible_pii + list(dataset.select_dtypes(include=['datetime']).columns)
    
    smart_print('**' + str(len(set(possible_pii))) + '**' + " total fields that may contain PII have now been identified.", messages_pipe)
    
    smart_return(possible_pii, function_pipe)


# # Review PII, Confirm & Clean, Recode, and Export

# In[11]:

#Reviewing and confirming PII
def review_potential_pii(possible_pii, dataset):
    #first does the GUI approach, and then does the command line / notebook approach
    confirmed_pii = []
    removed = False
    
    try:
        Label(frame, text="Your Expression:").pack()
    
    except NameError:
        if input('There are ' + str(len(set(possible_pii))) + ' variables that may contain PII. Would you like to review them and decide which to delete?') in yes_strings:
            count = 0
            for v in set(possible_pii):
                count += 1
                display(dataset[v].dropna()[:8])
                if input('Does this look like PII? (' + str(len(set(possible_pii))-count) + ' variables left to review.)  ') in yes_strings:
                    confirmed_pii.append(v)

        # Option to remove PII
        if input('Would you like to remove the columns identified as PII?   ') in yes_strings:
            for pii in confirmed_pii:
                del dataset[pii]
            removed = True
    
    return confirmed_pii, removed


# In[12]:

def recode(dataset):
    recoded_vars = []
    
    try:
        Label(frame, text='Recoding').pack()
    
    except NameError:
        # Option to recode columns
        if input('Would you like any variables to have their values recoded / anonymized?   ') in yes_strings:
            var_names = input('Which variable names? Enter each now, separated by a comma, or respond with "list" to see all variable names.  ').lower()
            if var_names.lower() in ['list', "'list'", '"list"']:
                smart_print(list(dataset.columns))
                time.sleep(5) #puts the next prompt in proper order
                var_names = input('Which variables would you like to recode? Enter them now, or write "none" to cancel.  ').lower()

            var_names = var_names.split(',')
            for var in var_names:
                var = var.replace("'","")
                var = var.strip()
                if var in dataset.columns:
                    dataset = dataset.sample(frac=1).reset_index(drop=False) # reorders dataframe randomly, while storing old index
                    dataset.rename(columns={'index':var + '_index'}, inplace=True)

                    # The method currently employed is used in order to more easily export the original/recoded value pairs. 
                    # It is likely slower than the other recoding option, commented out below.
                    # If speed is important and the user is ok not exporting value pairs, feel free to disable this approach,
                    # and enable the alternative below.

                    # Make dictionary of old and new values
                    value_replacer = 1
                    values_dict = {}   
                    for unique_val in dataset[var].unique():
                        values_dict[unique_val] = value_replacer
                        value_replacer += 1

                    # Replace old values with new
                    for k, v in values_dict.items():
                        dataset[var].replace(to_replace=k, value=v, inplace=True)

                    # Alternative approach, likely to be significantly quicker. Replaces the lines that employ values_dict.
                    #dataset[var] = pd.factorize(dataset[var])[0] + 1

                    smart_print(var + ' has been successfully recoded.')
                    recoded_vars.append(var)

                else:
                    smart_print(var + ' is not a valid variable. It will not be recoded.')
    return dataset, recoded_vars


# In[13]:

def export(dataset):
    csv_path = None
    exported = False
    
    try:
        Label(frame, text='Recoding').pack()
    
    except NameError:# Option for exporting deidentified dataset
        exported = False
        if input('Would you like to export the deidentified dataset to csv? (Your original dataset will be preserved.)  ') in yes_strings:
            csv_path = dataset_path.split('.')[0] + '_deidentified.csv'
            #stata_path = dataset_path.split('.')[0] + '_deidentified.dta'
            dataset.to_csv(csv_path)
            #dataset.to_stata(stata_path)
            exported = True
            
    return csv_path, exported


# In[14]:

def log(confirmed_pii, removed, recoded_vars, csv_path, exported):
    # log creation
    line1 = "The following actions were performed on this dataset:  "
    line2 = "These fields were confirmed as containing PII:  " + str(confirmed_pii)
    line3 = "The PII WAS "
    if not removed:
        line3 = line3 + "NOT "
    line3 = line3 + "removed from the dataset."
    line4 = "These fields were recoded / anonymized: " + str(recoded_vars)
    line5 = "And the new dataset WAS "
    if not exported:
        line5 = line5 + "NOT output."
    else:
        line5 = line5 + "output at " + csv_path

    log_lines = [line1, '', line2, line3, line4, line5]
    
    try:
        Label(frame, text='Recoding').pack()
    except NameError:
        if input('Would you like to see the log of this script session?  ') in yes_strings:
            for l in log_lines:
                smart_print(l)

        if input('Would you like to export this log as a .txt file?  ') in yes_strings:
            log_path = dataset_path.split('.')[0] + '_log.txt'

            with open(log_path, 'w') as f:
                f.write('\n'.join(log_lines))

            smart_print("The log has been exported at: " + log_path)


# In[15]:

#queue to pipe?

def driver(queue=None):
    import_results = import_dataset(queue.get()) #dataset, label_dict, value_label_dict
    dataset = import_results[0]
    dataset_path = import_results[1]

    identified_pii, restricted_vars = initialize_lists() 
    restricted_vars, stemmer = stem_restricted(restricted_vars)

    identified_pii = word_match_stemming(identified_pii, restricted_vars) 
    identified_pii = fuzzy_partial_stem_match(identified_pii, restricted_vars, threshold = 0.75) 
    identified_pii = unique_entries(identified_pii, min_entries_threshold = 0.5) 
    identified_pii = date_detection(identified_pii) 

    reviewed_pii, removed_status = review_potential_pii(identified_pii)
    dataset, recoded_fields = recode(dataset)
    path, export_status = export(dataset)
    log(reviewed_pii, removed_status, recoded_fields, path, export_status)

if __name__ == "__main__":
    dataset_path = input('What is the path to your dataset? (example: C:\Datasets\\file.xlsx)   ')
    driver(dataset_path)

# clean this up with consistent variable naming, better commenting, better documentation

