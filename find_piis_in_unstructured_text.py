from constant_strings import *
import restricted_words as restricted_words_list
import api_queries
import requests

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




def filter_based_type_of_word(list_strings, language):
    
    # CHECK .ENT_TYPE_
    #     if (token.ent_type_ == 'PERSON')
    #     print(token+" is a name")

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


  

#REPEATED FUNCTION FROM PII_DATA_PROCESSOR
def remove_other_refuse_and_dont_know(column):

    filtered_column = column.loc[(column != '777') & (column != '888') & (column != '999') & (column != '-888')]

    return filtered_column

#REPEATED FUNCTION FROM PII_DATA_PROCESSOR
def clean_column(column):
    #Drop NaNs
    column_filtered = column.dropna()

    #Remove empty entries
    column_filtered = column_filtered[column_filtered!='']

    #Remove other, refuses and dont knows
    column_filtered = remove_other_refuse_and_dont_know(column_filtered)

    return column_filtered

def get_list_unique_strings_in_dataset(dataset, columns_to_check):
    #To make the list, we will go over all columns that have sparse strings
    set_string_in_dataset = set()

    #For every column in the dataset
    for column_name in columns_to_check:
        
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

def find_piis(dataset, label_dict, columns_to_check, language, country):

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
    print(f'Found {len(phone_numbers_found)} phone numbers in open ended questions')
    if len(phone_numbers_found)>0:
        print(phone_numbers_found)

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
    names_found = api_queries.find_names_in_list_string(strings_to_check)
    print(f'Found {len(names_found)} names in open ended questions')
    if len(names_found)>0:
        print(names_found)


    #Update strings_to_check
    strings_to_check = [s for s in strings_to_check if s not in names_found]

    #Find all locations with pop less than 20,000
    print("-->Finding locations with low population")
    locations_with_low_population_found = api_queries.get_locations_with_low_population(strings_to_check, country)
    print(f'Found {len(locations_with_low_population_found)} locations with low populations')
    if len(locations_with_low_population_found)>0:
        print(locations_with_low_population_found)

    return list(set(phone_numbers_found + names_found + locations_with_low_population_found))

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



