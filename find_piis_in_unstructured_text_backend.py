from PII_data_processor import column_has_sufficiently_sparse_strings, clean_column, import_file, export
from constant_strings import *
import restricted_words as restricted_words_list
import query_google_answer_boxes as google

def get_stopwords(languages=None):

    from os import listdir
    from os.path import isfile, join
    
    stopwords_path = './stopwords/'

    #If no language selected, get all stopwords
    if(languages == None):
        stopwords_files = [join(stopwords_path, f) for f in listdir(stopwords_path) if isfile(join(stopwords_path, f))]
    else: #Select only stopwords files for given languages
        stopwords_files = [join(stopwords_path, language) for language in languages if isfile(join(stopwords_path, language))]

    stopwords_list = []
    for file_path in stopwords_files:
        with open(file_path, 'r', encoding="utf-8") as reader:
            stopwords = reader.read().split('\n')
            stopwords_list.extend(stopwords)
            
    return list(set(stopwords_list))

def remove_stopwords(strings_list, languages=['english','spanish']):
    import stopwords 
    stop_words = get_stopwords(languages)
    strings_list = [s for s in list(strings_list) if not s in stop_words] 
    return strings_list

def find_phone_numbers_in_list_strings(list_strings):

    phone_n_regex_str = "(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})"
    import re
    phone_n_regex = re.compile(phone_n_regex_str)
    phone_numbers_found = list(filter(phone_n_regex.match, list_strings))

    return phone_numbers_found

def generate_names_parameter_for_api(list_strings, option):
    #PENDING
    return ""

def get_names_from_json_response(response):
    #PENDING
    return []

def find_names_in_list_string(list_strings):
    import requests

    from forebears_api_key import get_api_key
    API_KEY = get_api_key()

    all_names_found = []

    for forename_or_surname in ['forename', 'surname']:
        names_parameter = generate_names_parameter_for_api(list_strings, forename_or_surname)
        
        #BULK CALL TO API NOT WORKING CORRECTLY YET, WAITING FOR REPSONSE
        api_url = 'https://ono.4b.rs/v1/jurs?key='+API_KEY+'&names='+names_parameter

        response = requests.request("GET", api_url)
        names_found = get_names_from_json_response(response)
        all_names_found.extend(names_found)

    return all_names_found

def find_piis_in_list_strings(list_strings):

    strings_to_check = list_strings

    #Find all telephone numbers
    print("-->Finding phone numbers")
    phone_numbers_found = find_phone_numbers_in_list_strings(strings_to_check)
    print("found "+str(len(phone_numbers_found)))
    #Update strings_to_check
    strings_to_check = [s for s in strings_to_check if s not in phone_numbers_found]
    
    #Find all locations with pop less than 20,000
    print("-->Finding locations")
    locations_with_low_population_found = google.get_locations_with_low_population(strings_to_check)
    print("found "+str(len(locations_with_low_population_found)))
    #Update strings_to_check
    strings_to_check = [s for s in strings_to_check if s not in locations_with_low_population_found]

    #Find all names
    print("-->Finding names")
    names_found = find_names_in_list_string(strings_to_check)
    print("found "+str(len(names_found)))

    return list(set(phone_numbers_found + locations_with_low_population_found + names_found))

def get_list_unique_strings_in_dataset(dataset, columns_to_check):
    #To make the list, we will go over all columns that have sparse strings
    set_string_in_dataset = set()

    #For every column in the dataset
    for column_name in columns_to_check:
        #If column contains strings
        if(column_has_sufficiently_sparse_strings(dataset, column_name)):
            
            #Clean column
            column = clean_column(dataset[column_name])

            for row in column:
                #If row contains more than one word, add each word
                if (' ' in row):
                    #For every word in the row
                    for word in row:
                        #Add word to strings to check
                        set_string_in_dataset.add(word)
                #If row does not contain spaces, add whole row (its only one string)
                else:
                    set_string_in_dataset.add(row)
    
    return list(set_string_in_dataset)

def find_piis_and_create_deidentified_dataset(dataset, dataset_path, label_dict):

    #Do not check surveyCTO columns
    columns_to_check = [column for column in dataset.columns if column not in restricted_words_list.get_surveycto_restricted_vars()]

    #First we will make a list of all strings that need to be checked
    print("->Getting list of unique strings in dataset...")
    strings_to_check = get_list_unique_strings_in_dataset(dataset, columns_to_check)

    
    #Remove string with less than 3 chars - piis should be longer than that
    print("->Removing strings with less than 3 characters")
    filtered_strings_to_check = [s for s in strings_to_check if len(s)>2]

    #Remove stopwords
    print("->Removing stopwords")
    filtered_strings_to_check = remove_stopwords(filtered_strings_to_check)

    #Find piis in list
    print("->Findind PIIs")
    piis_found = find_piis_in_list_strings(filtered_strings_to_check)

    print("All PIIS found:")
    print(piis_found)
    #Replace found piis found from the dataset
    print("->Replacing PIIs in new dataset")
    deidentified_dataset = dataset.replace(piis_found, 'XXXX', regex=True)

    #Save new dataframe
    print("->Exporting new dataset")
    new_file_path = export(deidentified_dataset, dataset_path)

    print("Task ready!")

    return new_file_path


if __name__ == "__main__":

    dataset_path = 'test_files/almond_etal_2008.dta'

    reading_status, reading_content = import_file(dataset_path)

    if(reading_status is False):
        print("Problem importing file")

    dataset = reading_content[DATASET]
    label_dict = reading_content[LABEL_DICT]
    
    find_piis_and_create_deidentified_dataset(dataset, dataset_path, label_dict)