import restricted_words as restricted_words_list
import pandas as pd
# from nltk.stem.porter import PorterStemmer
import time
import numpy as np

from constant_strings import *

import urllib.request as urllib2

import api_queries

import find_piis_in_unstructured_text as unstructured_text

import fileinput
import shutil
import os
from datetime import date

import hash_generator

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import os
from os import listdir
from os.path import isfile, isdir, join
import ntpath
import shutil

OUTPUTS_FOLDER = None
LOG_FILE_PATH = None

def get_surveycto_restricted_vars():
    return restricted_words_list.get_surveycto_restricted_vars()

def import_dataset(dataset_path):

    dataset, label_dict, value_label_dict = False, False, False
    raise_error = False
    status_message = False

    # if dataset_path.endswith(('"', "'")):
    #     dataset_path = dataset_path[1:-1]

    # dataset_path_l = dataset_path.lower()


    #Check format
    if(dataset_path.endswith(('xlsx', 'xls','csv','dta')) is False):
        return (False, 'Supported files are .csv, .dta, .xlsx, .xls')

    try:
        if dataset_path.endswith(('xlsx', 'xls')):
            dataset = pd.read_excel(dataset_path)
        elif dataset_path.endswith('csv'):
            dataset = pd.read_csv(dataset_path)
        elif dataset_path.endswith('dta'):
            try:
                dataset = pd.read_stata(dataset_path)
            except ValueError:
                dataset = pd.read_stata(dataset_path, convert_categoricals=False)
            label_dict = pd.io.stata.StataReader(dataset_path).variable_labels()
            try:
                value_label_dict = pd.io.stata.StataReader(dataset_path).value_labels()
            except AttributeError:
                status_message = "No value labels detected. " # Not printed in the app, overwritten later.
        elif dataset_path.endswith(('xpt', '.sas7bdat')):
            dataset = pd.read_sas(dataset_path)
        elif dataset_path.endswith('vc'):
            status_message = "**ERROR**: This folder appears to be encrypted using VeraCrypt."
            raise Exception
        elif dataset_path.endswith('bc'):
            status_message = "**ERROR**: This file appears to be encrypted using Boxcryptor. Sign in to Boxcryptor and then select the file in your X: drive."
            raise Exception
        else:
            raise Exception

    except (FileNotFoundError, Exception):
        if status_message is False:
            status_message = '**ERROR**: This path appears to be invalid. If your folders or filename contain colons or commas, try renaming them or moving the file to a different location.'
        raise

    if (status_message):
        log_and_print("There was an error")
        log_and_print(status_message)
        return (False, status_message)

    log_and_print('The dataset has been read successfully.\n')
    dataset_read_return = [dataset, dataset_path, label_dict, value_label_dict]
    return (True, dataset_read_return)

def word_match(column_name, restricted_word, type_of_matching=STRICT):

    if(type_of_matching == STRICT):
        return column_name.lower() == restricted_word.lower()
    else: # type_of_matching == FUZZY
        #Check if restricted word is inside column_name
        return restricted_word.lower() in column_name.lower()


def remove_other_refuse_and_dont_know(column):

    #List of values to remove. All numbers with 3 digits where all digits are the same
    values_to_remove = [str(111*i) for i in range(-9,10) if i !=0]

    filtered_column = column[~column.isin(values_to_remove)]

    return filtered_column


def clean_column(column):
    #Drop NaNs
    column_filtered = column.dropna()

    #Remove empty entries
    column_filtered = column_filtered[column_filtered!='']

    #Remove other, refuses and dont knows
    if len(column_filtered)!=0:
        column_filtered = remove_other_refuse_and_dont_know(column_filtered)

    return column_filtered

def column_is_sparse(dataset, column_name, sparse_threshold):

    column_filtered = clean_column(dataset[column_name])

    #Check sparcity
    n_entries = len(column_filtered)
    n_unique_entries = column_filtered.nunique()

    if n_entries != 0 and n_unique_entries/n_entries > sparse_threshold:
        return True
    else:
        return False

def column_has_sufficiently_sparse_strings(dataset, column_name, sparse_threshold=0.2):
    '''
    Checks if 'valid' column entries are sparse, defined as ratio between unique_entries/total_entries.
    Consider only valid stands, aka, exludet NaN, '', Other, Refuse to respond, Not Know
    '''

    #Check if column type is string
    if dataset[column_name].dtypes == 'object':
        return column_is_sparse(dataset, column_name, sparse_threshold)
    else:
        return False


def column_has_sparse_value_label_dicts(column_name, value_label_dict, sparse_threshold = 10):
    '''
    Check if for a given column, its values come encoded in a dictionary and are sufficiently sparse
    '''
    if column_name in value_label_dict and value_label_dict[column_name] != '' and len(value_label_dict[column_name])>sparse_threshold:
        return True
    else:
        return False

def find_piis_based_on_column_name(dataset, label_dict, value_label_dict, columns_to_check, consider_locations_cols):

    #Identifies columns whose names or labels match (strict or fuzzy) any word in the predefined list of restricted words. Also considers that data entries must be sufficiently sparse strings (Ideally, this method will capture columns with people names) or value label dictionaries (for locations)

    pii_strict_restricted_words = restricted_words_list.get_strict_restricted_words()
    pii_fuzzy_restricted_words = restricted_words_list.get_fuzzy_restricted_words()


    #If consider_locations_cols = 1, then consider locations columns in the search
    if(consider_locations_cols == 1):
        #If we are not checking locations populations, then include locations columns as part of restricted words
        locations_strict_restricted_words = restricted_words_list.get_locations_strict_restricted_words()
        locations_fuzzy_restricted_words = restricted_words_list.get_locations_fuzzy_restricted_words()

        pii_strict_restricted_words = set(pii_strict_restricted_words + locations_strict_restricted_words)
        pii_fuzzy_restricted_words = set(pii_fuzzy_restricted_words + locations_fuzzy_restricted_words)

    #We will save all restricted words in a dictionary, where the keys are the words and their values is if we are looking for a strict or fuzzy matching with that word
    restricted_words = {}
    for word in pii_strict_restricted_words:
        restricted_words[word] = STRICT
    for word in pii_fuzzy_restricted_words:
        restricted_words[word] = FUZZY

    # Looks for matches between column names (and labels) to restricted words
    possible_pii = {}

    #For every column name in our dataset
    for column_name in columns_to_check:
        #For every restricted word
        for restricted_word, type_of_matching in restricted_words.items():
            #Check if restricted word is in the column name
            column_name_match = word_match(column_name, restricted_word, type_of_matching)

            #If there is a dictionary of labels, check match with label
            if label_dict is not False: #label_dict will be False in case of no labels
                column_label = label_dict[column_name]
                column_label_match = word_match(column_label, restricted_word, type_of_matching)
            else:
                column_label_match = False

            #If there was a match between column name or label with restricted word
            if column_name_match or column_label_match:

                #If there was a strict match with restricted word
                if type_of_matching == STRICT:
                    log_and_print("Column '"+column_name+"' considered possible pii given column name had a "+type_of_matching+" match with restricted word '"+ restricted_word+"'")

                    possible_pii[column_name] = "Name had "+ type_of_matching + " match with restricted word '"+restricted_word+"'"


                #If column has strings and is sparse
                elif column_has_sufficiently_sparse_strings(dataset, column_name):

                    #Log result and save column as possible pii. Theres different log depending if match was with column or label
                    if(column_name_match):
                        log_and_print("Column '"+column_name+"' considered possible pii given column name had a "+type_of_matching+" match with restricted word '"+ restricted_word+"' and has sufficiently sparse strings")

                        possible_pii[column_name] = "Name had "+ type_of_matching + " match with restricted word '"+restricted_word+"' and has sufficiently sparse strings"

                    elif(column_label_match):
                        log_and_print("Column '"+column_name+ "' considered possible pii given column label '"+column_label+"' had a "+type_of_matching+" match with restricted word '"+ restricted_word+"' and has sufficiently sparse strings")

                        possible_pii[column_name] = "Label had "+ type_of_matching + " match with restricted word '"+restricted_word+"' and has sufficiently sparse strings"
                    #If found, I dont need to keep checking this column with other restricted words
                    break

                #Else, check if column has values labels (locations are usually stores this way)
                elif column_has_sparse_value_label_dicts(column_name, value_label_dict):

                    if(column_name_match):
                        log_and_print("Column '"+column_name+"' considered possible pii given column name had a "+type_of_matching+" match with restricted word '"+ restricted_word+"' and values labels are sparse")

                        possible_pii[column_name] = "Name had "+ type_of_matching + " match with restricted word '"+restricted_word+"' and values labels are sparse"

                    elif(column_label_match):
                        log_and_print("Column '"+column_name+ "' considered possible pii given column label '"+column_label+"' had a "+type_of_matching+" match with restricted word '"+ restricted_word+"' and values labels are sparse")

                        possible_pii[column_name] = "Label had "+ type_of_matching + " match with restricted word '"+restricted_word+"' and values labels are sparse"
                    #If found, I dont need to keep checking this column with other restricted words
                    break

    return possible_pii



def column_has_locations_with_low_populations(dataset, column_name, country):

    column_filtered = clean_column(dataset[column_name])

    #Get unique values
    unique_locations = column_filtered.unique().tolist()

    return api_queries.get_locations_with_low_population(unique_locations, country=country, return_one=True)


def log_and_print(message):
    file = open(LOG_FILE_PATH, "a")
    file.write(message+'\n')
    file.close()
    print(message)


def log_and_print(message):
    file = open(LOG_FILE_PATH, "a")
    file.write(message+'\n')
    file.close()
    print(message)

def find_piis_based_on_locations_population(dataset, label_dict, columns_to_check, country):
    #Identifies columns whose names or labels match (strict or fuzzy) words related to locations. Then, check if for those columns, any value relates to a location with population under 20,000. If it is the case, then it flags the column.

    #Lots of repeated code respect to find_piis_based_on_column_name, could refactor.

    locations_strict_restricted_words = restricted_words_list.get_locations_strict_restricted_words()
    locations_fuzzy_restricted_words = restricted_words_list.get_locations_fuzzy_restricted_words()

    #We will save all restricted words in a dictionary, where the keys are the words and their values is if we are looking for a strict or fuzzy matching with that word
    restricted_words = {}
    for word in locations_strict_restricted_words:
        restricted_words[word] = STRICT
    for word in locations_fuzzy_restricted_words:
        restricted_words[word] = FUZZY

    # Looks for matches between column names (and labels) to restricted words
    possible_pii = {}

    #For every column name in our dataset
    for column_name in columns_to_check:
        #For every restricted word
        for restricted_word, type_of_matching in restricted_words.items():
            #Check if restricted word is in the column name
            column_name_match = word_match(column_name, restricted_word, type_of_matching)

            #If there is a dictionary of labels, check match with label
            if label_dict is not False: #label_dict will be False in case of no labels
                column_label = label_dict[column_name]
                column_label_match = word_match(column_label, restricted_word, type_of_matching)
            else:
                column_label_match = False

            #If there was a match between column name or label with restricted word
            if column_name_match or column_label_match:

                location_with_low_population = column_has_locations_with_low_populations(dataset, column_name, country)

                if(location_with_low_population):
                    #Log result and save column as possible pii. Theres different log depending if match was with column or label
                    if(column_name_match):
                        log_and_print("Column '"+column_name+"' considered possible pii given column name had a "+type_of_matching+" match with restricted word '"+ restricted_word+"' and has a location with population under 20,000: "+location_with_low_population)

                        possible_pii[column_name] = "Name had "+ type_of_matching + " match with restricted word '"+restricted_word+"' and has a location with population under 20,000: "+location_with_low_population

                    elif(column_label_match):
                        log_and_print("Column '"+column_name+ "' considered possible pii given column label '"+column_label+"' had a "+type_of_matching+" match with restricted word '"+ restricted_word+"' and has a location with population under 20,000: "+location_with_low_population)

                        possible_pii[column_name] = "Label had "+ type_of_matching + " match with restricted word '"+restricted_word+"' and has a location with population under 20,000: "+location_with_low_population
                    #If found, I dont need to keep checking this column with other restricted words
                    break

    return possible_pii

def find_piis_based_on_sparse_entries(dataset, label_dict, columns_to_check, sparse_values_threshold=0.3):
    #Identifies pii based on columns having sparse values

    possible_pii={}
    for column_name in columns_to_check:

        if column_is_sparse(dataset, column_name, sparse_threshold=sparse_values_threshold):

            log_and_print("Column '"+column_name+"' considered possible pii given entries are sparse")
            possible_pii[column_name] = "Column entries are too sparse"

    return possible_pii


def find_columns_with_specific_format(dataset, format_to_search, columns_to_check):

    columns_with_phone_numbers = {}

    if format_to_search == PHONE_NUMBER:
        regex_expression = ".*(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}).*"

    elif format_to_search == DATE:

        #dd/mm/yy, (with -, / or .)
        regex_date_1 = "((0[1-9]|[12]\d|3[01])(\/|-|\.)(0[1-9]|1[0-2])(\/|-|\.)[12]\d{3})"
        #mm/dd/yyy, (with -, / or .)
        regex_date_2 = "((0[1-9]|1[0-2])(\/|-|\.)(0[1-9]|[12]\d|3[01])(\/|-|\.)[12]\d{3})"
        #yyyy/mm/dd, (with -, / or .)
        regex_date_3 = "([12]\d{3}(\/|-|\.)(0[1-9]|1[0-2])(\/|-|\.)(0[1-9]|[12]\d|3[01]))"

        regex_expression = regex_date_1+'|'+regex_date_2+'|'+regex_date_3

    for column in columns_to_check:

        #Check that all values in column are not NaN
        if(pd.isnull(dataset[column]).all() == False):

            #Find first 10 values that are not NaN nor empty space ''
            column_with_no_nan = dataset[column].dropna()
            column_with_no_empty_valyes = column_with_no_nan[column_with_no_nan != '']
            first_10_values = column_with_no_empty_valyes.iloc[0:10]

            match_result = first_10_values.astype(str).str.match(pat = regex_expression)

            #If all not NaN values matched with regex, save column as PII candidate
            if(any(match_result)):
                log_and_print("Column '"+column+"' considered possible pii given column entries have "+format_to_search+" format")
                columns_with_phone_numbers[column]= "Column entries have "+format_to_search+" format"

    return columns_with_phone_numbers

def export_encoding(dataset_path, encoding_dict):
    dataset_complete_file_name = ntpath.basename(dataset_path)
    dataset_file_name_no_extension, dataset_type = os.path.splitext(dataset_complete_file_name)

    encoding_file_path = os.path.join(OUTPUTS_FOLDER, dataset_file_name_no_extension + '_encodingmap.csv')

def save_all_piis_in_txt_file(list_variables_to_drop, list_variables_to_encode):

    all_piis_txt_file = os.path.join(OUTPUTS_FOLDER,'all_piis_identified.txt')
    delete_if_exists(all_piis_txt_file)
    file = open(all_piis_txt_file, "a")
    if len(list_variables_to_drop)>0:
        file.write(f'Columns to drop: {" ".join(list_variables_to_drop)}\n')
    if len(list_variables_to_encode)>0:
        file.write(f'Columns to encode: {" ".join(list_variables_to_encode)}')
    file.close()


def create_deidentifying_do_file(dataset_path, pii_candidates_to_action):
    '''
    Using anonymize_script_tempalte.txt as a starting point, we create a .do file that deidentifies dataset according to pii_candidates_to_action
    '''
    #Make a copy of the template file
    template_file = 'anonymize_script_template_v2.do'
    script_filename= os.path.join(OUTPUTS_FOLDER, 'anonymize_script.do')

    delete_if_exists(script_filename)
    shutil.copyfile(template_file, script_filename)

    deidentified_dataset_path = dataset_path.split('.')[0] + '_deidentified.dta'

    #Create list of vars to drop and encode
    list_variables_to_drop = []
    list_variables_to_encode = []
    for pii_candidate, action in pii_candidates_to_action.items():
        if action == 'Drop':
            list_variables_to_drop.append(pii_candidate)
        elif action == 'Encode':
            list_variables_to_encode.append(pii_candidate)


    #Read all lines and replace whenever we find one of the keywords
    with fileinput.FileInput(script_filename, inplace=True) as file: #, backup='.bak'
        today_string = date.today().strftime("%m/%d/%y")
        for line in file:
            #Create modified_line
            modified_line = line
            modified_line = modified_line.replace('[date]', today_string)
            modified_line = modified_line.replace('[input_file_path]', dataset_path)
            modified_line = modified_line.replace('[output_file_path]', deidentified_dataset_path)

            modified_line = modified_line.replace('[list_variables_to_drop_space_delimited]', " ".join(list_variables_to_drop))
            modified_line = modified_line.replace('[list_variables_to_hash_space_delimited]', " ".join(list_variables_to_encode))

            #The template .do file has an option to only remove value labels, we are not using that option so we will by default select no variables for that.
            modified_line = modified_line.replace('[list_variables_to_remove_value_labelling_space_delimited]', "")

            #Save modified line in file
            #print here will print in the file, not actually printing in console
            print(modified_line, end='')

    #Write down list of variables in a document
    save_all_piis_in_txt_file(list_variables_to_drop, list_variables_to_encode)

def delete_if_exists(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

def export_encoding(dataset_path, encoding_dict):
    encoding_file_path = dataset_path.split('.')[0] + '_encodingmap.csv'

    #Delete if file exists
    delete_if_exists(encoding_file_path)

    encoding_df = pd.DataFrame(columns=['variable','orginial value', 'encoded value'])

    for variable, values_dict in encoding_dict.items():
        for original_value, encoded_value in values_dict.items():
            encoding_df.loc[-1] = [variable, original_value, encoded_value]
            encoding_df.index = encoding_df.index + 1
    encoding_df.to_csv(encoding_file_path, index=False)

def create_anonymized_dataset(dataset, label_dict, dataset_path, pii_candidate_to_action, columns_where_to_replace_piis = None, piis_found_in_ustructured_text = None):

    #Drop columns
    columns_to_drop = [column for column in pii_candidate_to_action if pii_candidate_to_action[column]=='Drop']

    dataset = dataset.drop(columns=columns_to_drop)
    log_and_print("Dropped columns: "+ " ".join(columns_to_drop))

    #Encode columns
    columns_to_encode = [column for column in pii_candidate_to_action if pii_candidate_to_action[column]=='Encode']

    if(len(columns_to_encode)>0):
        log_and_print("Hashed columns: "+ " ".join(columns_to_encode))
        dataset, encoding_used = recode(dataset, columns_to_encode)
        log_and_print("Map file for encoded values created.")
        export_encoding(dataset_path, encoding_used)

    #Replace piis in unstructured text
    if(columns_where_to_replace_piis and piis_found_in_ustructured_text):
        for c in columns_where_to_replace_piis:
            dataset[c].replace(piis_found_in_ustructured_text, 'XXXX', regex=True, inplace=True)

    exported_file_path = export(dataset, dataset_path, label_dict)

    return exported_file_path

def find_survey_cto_vars(dataset):
    surveycto_vars = restricted_words_list.get_surveycto_vars()

    possible_pii = {}
    #For every column name in our dataset
    for column_name in dataset.columns:
        #For every restricted word
        for restricted_word in surveycto_vars:
            #Check if restricted word is in the column name
            if word_match(column_name, restricted_word):
                possible_pii[column_name] = 'SurveyCTO variable'

    return possible_pii


def find_piis_based_on_column_format(dataset, label_dict, columns_to_check):

    all_piis_detected = {}

    #Find columns with phone numbers formats
    columns_with_phone_numbers = find_columns_with_specific_format(dataset, PHONE_NUMBER, columns_to_check)
    all_piis_detected.update(columns_with_phone_numbers)

    columns_with_dates = find_columns_with_specific_format(dataset, DATE, columns_to_check)
    all_piis_detected.update(columns_with_dates)

    return all_piis_detected

def create_outputs_folder(dataset_path):
    directory_path = os.path.dirname(dataset_path)

    global OUTPUTS_FOLDER
    OUTPUTS_FOLDER = directory_path+'/pii_detection_outputs'

    if os.path.exists(OUTPUTS_FOLDER):
        shutil.rmtree(OUTPUTS_FOLDER)
    os.mkdir(OUTPUTS_FOLDER)


def create_log_file_path(dataset_path):

    global LOG_FILE_PATH
    LOG_FILE_PATH = OUTPUTS_FOLDER+"/log.txt"
    delete_if_exists(LOG_FILE_PATH)

def import_file(dataset_path):

    #Create outputs folder and log file
    create_outputs_folder(dataset_path)

    #Create log file
    create_log_file_path(dataset_path)

    #Read file
    import_status, import_result = import_dataset(dataset_path)

    #Check if error ocurr
    if import_status is False:
        return import_status, import_result

    #If no error, decouple import result
    dataset, dataset_path, label_dict, value_label_dict = import_result

    #Save results in dictionary for return
    response_content = {}
    response_content[DATASET] = dataset
    response_content[LABEL_DICT] = label_dict
    response_content[VALUE_LABEL_DICT] = value_label_dict

    return True, response_content



def recode(dataset, columns_to_encode):

    #Keep record of encoding
    econding_used = {}

    for var in columns_to_encode:

        #For hashing, we will use hmac-sha1, then sort the hashed values and assign values 1-n.
        # Make dictionary of old and new values.
        #First there is a step between
        unique_val_to_hmacsha1 = {}
        hmacsha1_to_final_hash = {}

        for unique_val in dataset[var].dropna().unique():
            unique_val_to_hmacsha1[unique_val] = hash_generator.hmac_sha1('[SECRET KEY]', unique_val)

        #Get list of all hmac-sha1 hashes and sort them
        sorted_hash = [v for k, v in sorted(unique_val_to_hmacsha1.items(), key=lambda item: item[1])]

        #Create dict that points from hmac-sha1 hashes to a 1-n value
        hmacsha1_to_final_hash = {}
        for index, hash in enumerate(sorted_hash):
            hmacsha1_to_final_hash[hash]=index+1

        #Join two dictionaries
        unique_val_to_final_hash = {}
        for k, v in unique_val_to_hmacsha1.items():
            unique_val_to_final_hash[k] = hmacsha1_to_final_hash[v]

        #Replace column with its hashes. First create list of all hashed values
        hashed_column = []
        for value in dataset[var].tolist():
            if value is np.nan:
                hashed_column.append(np.nan)
            else:
                hashed_column.append(unique_val_to_final_hash[value])
        dataset[var] = hashed_column

        print(var + ' has been successfully encoded.')
        econding_used[var] = unique_val_to_final_hash

    return dataset, econding_used

def find_piis_unstructured_text(dataset, label_dict, columns_still_to_check, language, country):

    #Filter columns to those that have sparse entries
    columns_to_check = []
    for column_name in columns_still_to_check:
        if column_has_sufficiently_sparse_strings(dataset, column_name):
            columns_to_check.append(column_name)

    pii_candidates_unstructured_text = unstructured_text.find_piis(dataset, label_dict, columns_to_check, language, country)

    log_and_print(f'Piis found in columns {columns_to_check} with unstructured text: {pii_candidates_unstructured_text}')

    return pii_candidates_unstructured_text, columns_to_check



def input_file_is_dta(dataset_path):
    dataset_file_name_no_extension, dataset_type = os.path.splitext(dataset_path)

    if dataset_type == '.dta':
        return True
    else:
        return False

def export(dataset, dataset_path, variable_labels = None):

    dataset_complete_file_name = ntpath.basename(dataset_path)
    dataset_file_name_no_extension, dataset_type = os.path.splitext(dataset_complete_file_name)

    if(dataset_type == '.csv'):
        new_file_path = os.path.join(OUTPUTS_FOLDER, dataset_file_name_no_extension + '_deidentified.csv')
        delete_if_exists(new_file_path)
        dataset.to_csv(new_file_path, index=False)

    elif(dataset_type == '.dta'):
        new_file_path = os.path.join(OUTPUTS_FOLDER, dataset_file_name_no_extension + '_deidentified.dta')
        delete_if_exists(new_file_path)
        try:
            dataset.to_stata(new_file_path, variable_labels = variable_labels, write_index=False)
        except:
            dataset.to_stata(new_file_path, version = 118, variable_labels = variable_labels, write_index=False)

    elif(dataset_type == '.xlsx'):
        new_file_path = os.path.join(OUTPUTS_FOLDER, dataset_file_name_no_extension + '_deidentified.xlsx')
        delete_if_exists(new_file_path)
        dataset.to_excel(new_file_path, index=False)

    elif(dataset_type == '.xls'):
        new_file_path = os.path.join(OUTPUTS_FOLDER, dataset_file_name_no_extension + '_deidentified.xls')
        delete_if_exists(new_file_path)
        dataset.to_excel(new_file_path, index=False)

    else:
        log_and_print("Data type not supported")
        new_file_path = None

    return new_file_path


def internet_on():
    try:
        urllib2.urlopen('http://google.com', timeout=2)
        return True
    except Exception as e:
        log_and_print(e)
        return False

def get_directories_path_in_folder(folder_path):
    only_directories = [join(folder_path, f) for f in listdir(folder_path) if isdir(join(folder_path, f))]
    return only_directories

def get_files_path_in_folder(folder_path):
    only_files = [join(folder_path, f) for f in listdir(folder_path) if isfile(join(folder_path, f))]
    return only_files

def get_testing_tuple(folder_path):
    only_files = get_files_path_in_folder(folder_path)

    data_source = None
    excel_with_ground_truth_pii = None
    country_file = None

    for file in only_files:
        if file.split('.')[-1]=='dta':
            data_source = file
            continue
        if file.split('-')[-1]=='true_piis.xlsx':
            excel_with_ground_truth_pii = file
            continue
        if file.split('.')[-1]=='txt':
            country_file = file
            continue
    if data_source and excel_with_ground_truth_pii and country_file:
        return True, (data_source, excel_with_ground_truth_pii, country_file)
    else:
        return False, False


def get_test_files_tuples():

    all_test_files_tuples = []

    #Look for files in X:\Box Sync\GRDS_Resources\Data Science\Test data\Raw\
    #For every folder inside, if folder has .dta and .xlsx ending with -piis.xlsx, add it to list

    folder_with_raw_data = 'X:\Box Sync\GRDS_Resources\Data Science\Test data\Raw'
    only_directories = get_directories_path_in_folder(folder_with_raw_data)

    for dir in only_directories:
        #Check that dir has .dta and .xls
        dir_has_testing_tuple, testing_tuple = get_testing_tuple(dir)
        if dir_has_testing_tuple:
             all_test_files_tuples.append((testing_tuple[0], testing_tuple[1], testing_tuple[2]))

    return all_test_files_tuples

def get_country(country_file_path):
    with open(country_file_path) as f:
        lines = f.readlines()
    return lines[0]

def run_tests():

    test_files_tuples = get_test_files_tuples()

    for test_files_tuple in test_files_tuples:
        dataset_path, true_piis_path, country_file_path = test_files_tuple
        country = get_country(country_file_path)

        print(f'RUNNING TEST FOR {dataset_path}.\nCountry {country}')

        #Import dataset
        reading_status, reading_content = import_file(dataset_path)

        #Check if reading was succesful
        if(reading_status is False):
            return

        dataset = reading_content[DATASET]
        label_dict = reading_content[LABEL_DICT]
        value_label_dict = reading_content[VALUE_LABEL_DICT]
        columns_still_to_check = [c for c in dataset.columns if c not in restricted_words_list.get_surveycto_restricted_vars()]

        #Search piis using all methods
        all_piis_found = {}

        #Options
        consider_locations_cols = 1
        search_pii_in_unstructured_text = 0

        pii_candidates = find_piis_based_on_column_name(dataset, label_dict, value_label_dict, columns_still_to_check, consider_locations_cols)
        all_piis_found.update(pii_candidates)
        columns_still_to_check = [c for c in columns_still_to_check if c not in pii_candidates]
        log_and_print("Piis found using column names: "+",".join(pii_candidates.keys()))

        if(consider_locations_cols==0):
            pii_candidates = find_piis_based_on_locations_population(dataset, label_dict, columns_still_to_check, country)
            all_piis_found.update(pii_candidates)
            columns_still_to_check = [c for c in columns_still_to_check if c not in pii_candidates]
            log_and_print("Piis found basen on locations with low population: "+",".join(pii_candidates.keys()))


        pii_candidates = find_piis_based_on_column_format(dataset, label_dict, columns_still_to_check)
        all_piis_found.update(pii_candidates)
        columns_still_to_check = [c for c in columns_still_to_check if c not in pii_candidates]
        log_and_print("Piis found using column formats: "+",".join(pii_candidates.keys()))

        if search_pii_in_unstructured_text == 0:
            pii_candidates_unstructured_text = None
            column_with_unstructured_text = None

            pii_candidates = find_piis_based_on_sparse_entries(dataset, label_dict, columns_still_to_check)
            all_piis_found.update(pii_candidates)
            log_and_print("Piis based on sparse entries: "+",".join(pii_candidates.keys()))

        else:
            pii_candidates_unstructured_text, column_with_unstructured_text = find_piis_unstructured_text(dataset, label_dict, columns_still_to_check, SPANISH, MEXICO)

            log_and_print("Piis found in unstructured text: "+",".join(pii_candidates_unstructured_text))
            log_and_print(len(pii_candidates_unstructured_text))


        #Create fake pii_candidate_to_action
        pii_candidate_to_action = {}
        for pii in pii_candidates:
            pii_candidate_to_action[pii] = 'Drop'

        #Create deidentified dataset
        create_anonymized_dataset(dataset, label_dict, dataset_path, pii_candidate_to_action, pii_candidates_unstructured_text, column_with_unstructured_text)

        #Now we check identified PIIs are the correct ones based on ground truth
        reading_status, reading_content = import_file(true_piis_path)
        if(reading_status is False):
            return
        true_piis_dataset = reading_content[DATASET]
        true_piis = true_piis_dataset.iloc[:,0].to_list()

        #Announce wrongly detected ppis
        print("THE FOLLOWING PIIS WERE WRONGLY DETECTED:")
        wrongly_detected = [pii for pii in all_piis_found.keys() if pii not in true_piis]
        print(wrongly_detected)

        #Announce missing piis
        print("THE FOLLOWING PIIS WERE NOT DETECTED:")
        not_detected = [pii for pii in true_piis if pii not in all_piis_found.keys()]
        print(not_detected)



if __name__ == "__main__":
    run_tests()
