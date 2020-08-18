import restricted_words
import pandas as pd
from nltk.stem.porter import PorterStemmer

# import nltk
# import numpy as np
# import os


# from IPython.display import display, HTML
# from IPython.core.interactiveshell import InteractiveShell
# InteractiveShell.ast_node_interactivity = "all"
# import time

# def smart_print(the_message, messages_pipe = None):
#     if __name__ == "__main__":
#         print(the_message)
#     else:
#         messages_pipe.send(the_message)

# def smart_return(to_return, function_pipe = None):
#     if __name__ != "__main__":
#         function_pipe.send(to_return)
#     else:
#         if len(to_return) == 2:
#             return to_return[0], to_return[1]
#         else:
#             return to_return

def import_dataset(dataset_path):
    
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
        raise

    if (status_message):
        print("There was an error")
        print(status_message)
        return (False, status_message)

    print('The dataset has been read successfully.')
    dataset_read_return = [dataset, dataset_path, label_dict, value_label_dict]
    return (True, dataset_read_return)


# def initialize_lists(function_pipe = None):

#     possible_pii = []
#     global yes_strings
#     yes_strings = ['y', 'yes', 'Y', 'Yes']

#     list_restricted_words = restricted_words.get_restricted_words()
    
#     smart_return([possible_pii, list_restricted_words], function_pipe)


def add_stem_of_words(restricted):
# Identifies stems of restricted words and adds the stems to restricted list

    initialized_stemmer = PorterStemmer()
    restricted_stems = []
    for r in restricted:
        restricted_stems.append(initialized_stemmer.stem(r).lower())

    restricted = restricted + restricted_stems
    restricted = list(set(restricted))
    
    return restricted



def find_piis_word_match(dataset, restricted_words, label_dict, sensitivity = 3, stemmer = None):
    # Looks for matches between column names (and labels) to restricted words
    # In the future, we could study looking for matched betwen column names stems and restricted words
    print('The word match with stemming algorithm is now running.')
    
    possible_pii = []

    #For every column name in our dataset
    for v in dataset.columns:
        #For every restricted word
        for r in restricted_words:
            #Check if restricted word is in the column name
            if r in v.lower():
                print("Adding "+v+ " to possible piis given column name matched with restricted word "+r)
                possible_pii.append(v)

                #If found, I dont need to keep checking this column with other restricted words
                break

#---> TO BE CHECKED THIS WORKS FINE
            #If dictionary of labels is not of booleans, check labels
            if type(label_dict) is not bool:
                #Check words of label of given column
                words = label_dict[v].split(' ')
                for i in words:
                    #Check that label bigger than senstitivity
                    if len(i) > sensitivity:
                        #Check if restricted word is in label
                        if r in i.lower():
                            print("Adding "+v+ " to possible piis given column label.")
                            possible_pii.append(v)
                            break
    print("")
    return possible_pii

    
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

def unique_entries(dataset, min_entries_threshold = 0.5):
    #Identifies pii based on columns having only unique values
    #Requires that at least 50% of entries in given column are not NA 
    possible_pii=[]
    for v in dataset.columns:
        if len(dataset[v]) == len(set(dataset[v])) and len(dataset[v].dropna())/len(dataset) > min_entries_threshold:
            possible_pii.append(v)
            print("Column "+v+" considered possible pii given all entries are unique")
    
    return possible_pii


def format_detection(dataset):
    
    #Check dates format    
    possible_pii = list(dataset.select_dtypes(include=['datetime']).columns)
    
    #Check other formats

    return possible_pii




def create_anonymized_dataset(dataset, dataset_path, pii_candidate_to_action):

    #Drop columns
    columns_to_drop = [column for column in pii_candidate_to_action if pii_candidate_to_action[column]=='Drop']

    print("Will drop following columns:")
    print(columns_to_drop)

    dataset.drop(columns=columns_to_drop, inplace=True)

    #Encode columns
    # columns_to_encode = [column for column in pii_candidate_to_action if pii_candidate_to_action[column]=='Encode']

    # dataset, encoding_used = recode(dataset, columns_to_encode)


    exported_file_path = export(dataset, dataset_path)
    # # log(reviewed_pii, removed_status, recoded_fields, path, export_status)


    return exported_file_path

def find_piis(dataset, label_dict):
    
    #Get words that are usually piis
    pii_restricted_words = restricted_words.get_restricted_words()

    #Get stem of the restricted words
    #pii_restricted_words = add_stem_of_words(pii_restricted_words)

    #Find piis based on word matching
    piis_word_match = find_piis_word_match(dataset, pii_restricted_words, label_dict)

    #Another thing that might be tried
    #fuzzy_partial_stem_match()    

    #Find piis based on unique_entries detections
    piis_unique_entries = unique_entries(dataset)

    #Find piis based on entries format
    piis_suspicious_format = format_detection(dataset) 

    return set(piis_word_match + piis_unique_entries + piis_suspicious_format)

def read_file_and_find_piis(dataset_path):
    #Read file
    import_status, import_result = import_dataset(dataset_path)    
    if import_status is False:
        return import_status, import_result, _
    
    dataset, dataset_path, label_dict, value_label_dict = import_result

    #Find piis
    piis = find_piis(dataset, label_dict)

    return True, piis, dataset



def recode(dataset, columns_to_encode):

    #Keep record of encoding
    econding_used = {}

    for var in columns_to_encode:

        # dataset = dataset.sample(frac=1).reset_index(drop=False) # reorders dataframe randomly, while storing old index
        # dataset.rename(columns={'index':var + '_index'}, inplace=True)

        # Make dictionary of old and new values
        new_value = 1
        old_to_new_dict = {}   
        for unique_val in dataset[var].unique():
            old_to_new_dict[unique_val] = new_value
            new_value += 1

        # Replace old values with new in dataframe
        for k, v in old_to_new_dict.items():
            dataset[var].replace(to_replace=k, value=v, inplace=True)

        # Alternative approach, likely to be significantly quicker. Replaces the lines that employ values_dict.
        #dataset[var] = pd.factorize(dataset[var])[0] + 1

        print(var + ' has been successfully recoded.')
        econding_used[var] = old_to_new_dict

    return dataset, econding_used


# In[13]:

def export(dataset, dataset_path):

    dataset_type = dataset_path.split('.')[1]

    if(dataset_type == 'csv'):
        new_file_path = dataset_path.split('.')[0] + '_deidentified.csv'
        dataset.to_csv(new_file_path, index=False)

    elif(dataset_type == 'dta'):
        new_file_path = dataset_path.split('.')[0] + '_deidentified.dta'
        dataset.to_stata(new_file_path)
    else:
        print("Data type not supported")
        new_file_path = None
            
    return new_file_path



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

