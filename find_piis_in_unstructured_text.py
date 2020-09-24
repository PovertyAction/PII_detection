from PII_data_processor import column_has_sufficiently_sparse_strings, clean_column, import_file, export
from constant_strings import *
import restricted_words as restricted_words_list
import query_google_answer_boxes as google
import requests
from secret_keys import get_forebears_api_key
import json
from datetime import datetime
import spacy

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


def generate_names_parameter_for_api(list_names, option):
    #According to https://forebears.io/onograph/documentation/api/location/batch

    list_of_names_json=[]
    for name in list_names:
        list_of_names_json.append('{"name":"'+name+'","type":"'+option+'","limit":2}')

    names_parameter = '['+','.join(list_of_names_json)+']'
    return names_parameter

def get_names_from_json_response(response):
    
    names_found = []

    json_response = json.loads(response)
    for result in json_response["results"]:
        #Names that exist come with the field 'jurisdictions'
        #We will also ask a minimum of 50 world incidences 
        if('jurisdictions' in result):
            world_incidences = int(result['world']['incidence'])

            if world_incidences > 50:
                names_found.append(result['name'])

    return names_found

def filter_based_type_of_word(list_strings, language):
    
    if language == SPANISH:
        nlp = spacy.load("es_core_news_sm")

    else:
        nlp = spacy.load("en_core_web_sm")
    
    #Accepted types of words
    #Reference https://spacy.io/api/annotation#pos-tagging
    accepted_types = ['PROPN', 'X','PER','LOC','ORG','MISC','']

    filtered_list = []
    import datetime

    filtered_list = []
    doc = nlp(" ".join(list_strings))
    # print("b")
    for token in doc:
        if token.pos_ in accepted_types:
            filtered_list.append(token.text)

    filtered_list = list(set(filtered_list))

    return filtered_list

def find_names_in_list_string(list_potential_names):
    '''
    Uses https://forebears.io/onograph/documentation/api/location/batch to find names in list_potential_names

    If this approach seems to be slow or inaccurate, an alternative its to use spacy:
    import spacy
    string = "my name is felipe"
    nlp = spacy.load("en_core_web_md")
    doc = nlp(string)
    for token in doc:
        if (token.ent_type_ == 'PERSON')
        print(token+" is a name")
    '''
    API_KEY = get_forebears_api_key()

    all_names_found = set()

    #Api calls must query at most 1,000 names.
    n = 1000
    list_of_list_1000_potential_names = [list_potential_names[i:i + n] for i in range(0, len(list_potential_names), n)]

    for list_1000_potential_names in list_of_list_1000_potential_names:
        #Need to 2 to API calls, one checking forenames and one checking surnames
        for forename_or_surname in ['forename', 'surname']:
            api_url = 'https://ono.4b.rs/v1/jurs?key='+API_KEY

            names_parameter = generate_names_parameter_for_api(list_1000_potential_names, forename_or_surname)

            response = requests.post(api_url, data={'names':names_parameter})

            names_found = get_names_from_json_response(response.text)
            for name in names_found:
                all_names_found.add(name)

    return list(all_names_found)
  

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
                    for word in row.split(" "):
                        #Add word to strings to check
                        set_string_in_dataset.add(word)
                #If row does not contain spaces, add whole row (its only one string)
                else:
                    set_string_in_dataset.add(row)

    return list(set_string_in_dataset)

def find_piis(dataset, label_dict, columns_to_check_not_filtered, language, country):

    #Filter columns to those that have sparse entries
    columns_to_check = []
    for column_name in columns_to_check_not_filtered:
        if column_has_sufficiently_sparse_strings(dataset, column_name):            
            columns_to_check.append(column_name)

    print("columns_to_check")
    print(columns_to_check)

    #Do not check surveyCTO columns
    #columns_to_check = [column for column in dataset.columns if column not in restricted_words_list.get_surveycto_restricted_vars()]

    #First we will make a list of all strings that need to be checked
    print("->Getting list of unique strings in dataset...")
    strings_to_check = get_list_unique_strings_in_dataset(dataset, columns_to_check)

    #Remove string with less than 3 chars - piis should be longer than that
    print("->Removing strings with less than 3 characters")
    strings_to_check = [s for s in strings_to_check if len(s)>2]

    #Find all telephone numbers
    print("-->Finding phone numbers")
    phone_numbers_found = find_phone_numbers_in_list_strings(strings_to_check)
    print("found "+str(len(phone_numbers_found)))

    #Update strings_to_check
    strings_to_check = [s for s in strings_to_check if s not in phone_numbers_found]

    #Clean list of words, now that we have already found numbers
    print("Length of list "+str(len(strings_to_check)))
    print("->Removing stopwords")
    strings_to_check = remove_stopwords(strings_to_check)
    print("->Filtering based on word type")
    strings_to_check = filter_based_type_of_word(strings_to_check, language)
    print("Length of list "+str(len(strings_to_check)))

    #Find all names
    print("->Finding names")
    names_found = find_names_in_list_string(strings_to_check)
    print("found "+str(len(names_found)))
    print(names_found)
    #Update strings_to_check
    strings_to_check = [s for s in strings_to_check if s not in names_found]

    #Find all locations with pop less than 20,000
    print("-->Finding locations with low population")
    locations_with_low_population_found = google.get_locations_with_low_population(strings_to_check, country)
    print("found "+str(len(locations_with_low_population_found)))
    print(locations_with_low_population_found)

    return list(set(phone_numbers_found + names_found + locations_with_low_population_found)), columns_to_check

if __name__ == "__main__":

    # dataset_path = 'X:\Box Sync\GRDS_Resources\Data Science\Test data\Raw\RECOVR_MEX_r1_Raw.dta'

    # reading_status, reading_content = import_file(dataset_path)

    # if(reading_status is False):
    #     print("Problem importing file")

    # dataset = reading_content[DATASET]
    # label_dict = reading_content[LABEL_DICT]
    
    # columns_to_check = [c for c in dataset.columns if c not in restricted_words_list.get_surveycto_restricted_vars()]

    # find_piis(dataset, label_dict, columns_to_check)

    print(find_names_in_list_string(['Felipe','nombrequenoexiste', 'George', 'Felipe', 'Enriqueta', 'dededede']))

