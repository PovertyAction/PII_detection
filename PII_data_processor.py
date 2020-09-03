import restricted_words as restricted_words_list
import pandas as pd
# from nltk.stem.porter import PorterStemmer
import time 

LOG_FILE = None

from constant_strings import *


import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


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

    print('The dataset has been read successfully.\n')
    dataset_read_return = [dataset, dataset_path, label_dict, value_label_dict]
    return (True, dataset_read_return)


# def add_stem_of_words(restricted):
# # Identifies stems of restricted words and adds the stems to restricted list

#     initialized_stemmer = PorterStemmer()
#     restricted_stems = []
#     for r in restricted:
#         restricted_stems.append(initialized_stemmer.stem(r).lower())

#     restricted = restricted + restricted_stems
#     restricted = list(set(restricted))
    
#     return restricted


def word_match(column_name, restricted_word, type_of_matching=STRICT):
    if(type_of_matching == STRICT):
        return column_name.lower() == restricted_word.lower()
    else: # type_of_matching == FUZZY
        #Check if restricted word is inside column_name
        return restricted_word.lower() in column_name.lower()


def remove_other_refuse_and_dont_know(column):

    filtered_column = column.loc[(column != '777') & (column != '888') & (column != '999')]

    return filtered_column




def column_is_sparse(dataset, column_name, sparse_threshold):
    
    #Drop NaNs
    column_filtered = dataset[column_name].dropna()

    #Remove empty entries
    column_filtered = column_filtered[column_filtered!='']

    #Remove other, refuses and dont knows
    column_filtered = remove_other_refuse_and_dont_know(column_filtered)

    #Check sparcity
    n_entries = len(column_filtered)
    n_unique_entries = column_filtered.nunique()

    if n_entries != 0 and n_unique_entries/n_entries > sparse_threshold:
        # print(column_name)
        # print(n_unique_entries/n_entries)
        return True
    else:
        return False

def column_has_sufficiently_sparse_strings(dataset, column_name, sparse_threshold=0.3):
    '''
    Checks if 'valid' column entries are sparse, defined as ratio between unique_entries/total_entries.
    Consider only valid stands, aka, exludet NaN, '', Other, Refuse to respond, Not Know
    '''

    #Check if column type is string
    if dataset[column_name].dtypes == 'object':
        return column_is_sparse(dataset, column_name, sparse_threshold)
    else:
        return False


def column_name_has_restricted_word_and_sufficiently_sparse_strings(dataset, label_dict, columns_to_check, consider_locations_cols, sensitivity = 3, stemmer = None):
    
    #Identifies columns whose names or labels match (strict or fuzzy) any word in the predefined list of restricted words. Also considers that data entries must be sufficiently sparse strings
    #Ideally, this method will capture columns with names, etc.

    pii_strict_restricted_words = restricted_words_list.get_strict_restricted_words()
    pii_fuzzy_restricted_words = restricted_words_list.get_fuzzy_restricted_words()


    #If consider_locations_cols = 1, then all locations columns get flagged. else, do not check them (they will be checked later by method that will look at locations populations)
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

    #Currently not doing any stem matching
    #Get stem of the restricted words
    #pii_restricted_words = add_stem_of_words(pii_restricted_words)

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

                # print("Checking column with suspicious name")
                # print("Column: "+column_name)
                # if(column_label):
                #     print("Label: "+ column_label)
                # print("Column type: "+str(dataset[column_name].dtypes))

                #If column has strings and is sparse    
                if column_has_sufficiently_sparse_strings(dataset, column_name):

                    # print("Is sparse!!")

                    #Log result and save column as possible pii. Theres different log depending if match was with column or label
                    if(column_name_match):
                        log_and_print("Column '"+column_name+"' considered possible pii given column name had a "+type_of_matching+" match with restricted word '"+ restricted_word+"' and has sufficiently sparse strings")
                
                        possible_pii[column_name] = "Name had "+ type_of_matching + " match with restricted word '"+restricted_word+"' and has sparse sufficiently strings"
                    
                    elif(column_label_match):
                        log_and_print("Column '"+column_name+ "' considered possible pii given column label '"+column_label+"' had a "+type_of_matching+" match with restricted word '"+ restricted_word+"' and has sufficiently sparse strings")
                    
                        possible_pii[column_name] = "Label had "+ type_of_matching + " match with restricted word '"+restricted_word+"' and has sufficiently sparse strings"
                    #If found, I dont need to keep checking this column with other restricted words
                    break

    return possible_pii


def log_and_print(message)    :
    file = open(LOG_FILE, "a") 
    file.write(message+'\n') 
    file.close() 
    print(message)

def find_piis_based_on_locations_population(dataset, label_dict, columns_still_to_check):
    #PENDING!!
    return []

def find_piis_based_on_sparse_entries(dataset, label_dict, columns_to_check, sparse_values_threshold=0.85):
    #Identifies pii based on columns having sparse values

    possible_pii={}
    for column_name in columns_to_check:

        if column_is_sparse(dataset, column_name, sparse_threshold=sparse_values_threshold):
            
            log_and_print("Column '"+column_name+"' considered possible pii given entries are sparse")
            possible_pii[column_name] = "Column entries are too sparse"

    return possible_pii


def find_columns_with_phone_numbers(dataset, columns_to_check):

    columns_with_phone_numbers = {}

    phone_n_regex_expression = "(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})"

    for column in columns_to_check:

        #Check that all values in column are not NaN
        if(pd.isnull(dataset[column]).all() == False):

            #Find first 10 values that are not NaN nor empty space ''
            column_with_no_nan = dataset[column].dropna()
            column_with_no_empty_valyes = column_with_no_nan[column_with_no_nan != '']
            first_10_values = column_with_no_empty_valyes.iloc[0:10]

            match_result = first_10_values.astype(str).str.match(pat = phone_n_regex_expression)
            #If all not NaN values matched with regex, save column as PII candidate
            if(any(match_result)):
                log_and_print("Column '"+column+"' considered possible pii given column entries have phone number format")
                columns_with_phone_numbers[column]= "Column entries have phone number format"

    return columns_with_phone_numbers


def format_detection(dataset, columns_to_check):
    
    #Find columns with phone numbers formats
    possible_pii = find_columns_with_phone_numbers(dataset, columns_to_check)

    #Check other formats

    return possible_pii


def export_encoding(dataset_path, encoding_dict):
    encoding_file_path = dataset_path.split('.')[0] + '_encodingmap.csv'

    encoding_df = pd.DataFrame(columns=['variable','orginial value', 'encoded value'])

    for variable, values_dict in encoding_dict.items():
        for original_value, encoded_value in values_dict.items():
            encoding_df.loc[-1] = [variable, original_value, encoded_value]
            encoding_df.index = encoding_df.index + 1
    encoding_df.to_csv(encoding_file_path, index=False)

def create_anonymized_dataset(dataset, label_dict, dataset_path, pii_candidate_to_action):

    #Drop columns
    columns_to_drop = [column for column in pii_candidate_to_action if pii_candidate_to_action[column]=='Drop']

    dataset.drop(columns=columns_to_drop, inplace=True)
    log_and_print("Dropped columns: "+ " ".join(columns_to_drop))

    #Encode columns
    columns_to_encode = [column for column in pii_candidate_to_action if pii_candidate_to_action[column]=='Encode']

    if(len(columns_to_encode)>0):
        log_and_print("Will encode following columns: "+ " ".join(columns_to_encode))
        dataset, encoding_used = recode(dataset, columns_to_encode)
        log_and_print("Map file for encoded values created.")
        export_encoding(dataset_path, encoding_used)

    exported_file_path = export(dataset, dataset_path, label_dict)

    return exported_file_path

def find_survey_cto_vars(dataset):
    surveycto_vars = restricted_words_list.get_surveycto_vars()

    possible_pii = {}
    log_and_print("List of identified PIIs: ")

    #For every column name in our dataset
    for column_name in dataset.columns:
        #For every restricted word
        for restricted_word in surveycto_vars:
            #Check if restricted word is in the column name
            if word_match(column_name, restricted_word):
                possible_pii[column_name] = 'SurveyCTO variable'

    return possible_pii


def find_piis_based_on_column_name(dataset, label_dict, columns_to_check, consider_locations_cols):

    all_piis_detected = {}

    #Find piis based on word matching
    piis_word_match = column_name_has_restricted_word_and_sufficiently_sparse_strings(dataset, label_dict, columns_to_check, consider_locations_cols)
    all_piis_detected.update(piis_word_match)

    log_and_print("Identified PIIs: "+" ".join(list(all_piis_detected.keys())))

    return all_piis_detected

def find_piis_based_on_column_format(dataset, label_dict, columns_to_check):

    all_piis_detected = {}

    #Find piis based on entries format
    piis_suspicious_format = format_detection(dataset, columns_to_check)
    all_piis_detected.update(piis_suspicious_format)

    return all_piis_detected


def create_log_file_path(dataset_path):

    dataset_directory_path = "/".join(dataset_path.split('/')[:-1])
    
    file_name = dataset_path.split('/')[-1].split('.')[0]

    global LOG_FILE
    LOG_FILE = dataset_directory_path+"/log_"+file_name+str(time.time()).replace('.','')+'.txt'

    print(LOG_FILE)




    

def import_file(dataset_path):

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


    create_log_file_path(dataset_path)

    return True, response_content



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

        log_and_print(var + ' has been successfully encoded.')
        econding_used[var] = old_to_new_dict

    return dataset, econding_used


# In[13]:

def export(dataset, dataset_path, variable_labels = None):

    dataset_type = dataset_path.split('.')[1]

    if(dataset_type == 'csv'):
        new_file_path = dataset_path.split('.')[0] + '_deidentified.csv'
        dataset.to_csv(new_file_path, index=False)

    elif(dataset_type == 'dta'):
        new_file_path = dataset_path.split('.')[0] + '_deidentified.dta'

        try:
            dataset.to_stata(new_file_path, variable_labels = variable_labels, write_index=False)
        except:
            dataset.to_stata(new_file_path, version = 118, variable_labels = variable_labels, write_index=False)

    elif(dataset_type == 'xlsx'):
        new_file_path = dataset_path.split('.')[0] + '_deidentified.xlsx'
        dataset.to_excel(new_file_path, index=False)

    elif(dataset_type == 'xls'):
        new_file_path = dataset_path.split('.')[0] + '_deidentified.xls'
        dataset.to_excel(new_file_path, index=False)

    else:
        log_and_print("Data type not supported")
        new_file_path = None
            
    return new_file_path


def main_when_script_run_from_console():
    dataset_path = 'X:\Box Sync\GRDS_Resources\Data Science\Test data\Raw\RECOVR_MEX_r1_Raw.dta'

    find_piis_options={}
    find_piis_options[CONSIDER_SURVEY_CTO_VARS] = 0
    reading_status, pii_candidates_or_message, dataset, label_dict = read_file_and_find_piis_based_on_column_name(dataset_path, find_piis_options)

    #Check if reading was succesful
    if(reading_status is False):    
        error_message = pii_candidates_or_message
        log_and_print(error_message)
        return
    else:
        pii_candidates = pii_candidates_or_message

    #Manually set action for piis
    pii_candidates_to_action ={}
    for pii in pii_candidates:
        pii_candidates_to_action[pii] = 'Drop'

    create_anonymized_dataset(dataset, label_dict, dataset_path, pii_candidates_to_action)


if __name__ == "__main__":
    main_when_script_run_from_console()


