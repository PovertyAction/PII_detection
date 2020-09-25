from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import pandas as pd
from secret_keys import get_geonames_username, get_forebears_api_key
import requests
import json

from constant_strings import *


driver=None
def ask_google(query):
	global driver

	if driver is None:
		chrome_options = Options()
		chrome_options.add_argument("--window-size=1024x768")
		chrome_options.add_argument("--headless")
		driver = webdriver.Chrome(executable_path=r'chromedriver.exe',options=chrome_options)

	# Search for query
	query = query.replace(' ', '+')

	driver.get('http://www.google.com/search?q=' + query)

	# Get text from Google answer box
	for different_answer_box_y_location in [230,350]: #Usually 230 is fine, but for searches that come with images (La Magdalena Contreras population for ex) 350 is better
		answer = driver.execute_script("return document.elementFromPoint(arguments[0], arguments[1]);",
	        350, different_answer_box_y_location).text
		if answer != "":
			return answer

	return False

def get_country_iso_code(country_name):

	if country_name in COUNTRY_NAME_TO_ISO_CODE:
		return COUNTRY_NAME_TO_ISO_CODE[country_name]
	else:
		return None

def check_location_exists_and_population_size(location, country):
	#https://www.geonames.org/export/geonames-search.html
	
	api_url = 'http://api.geonames.org/searchJSON?name='+location+'&name_equals='+location+'&maxRows=1&orderby=population&isNameRequired=true&username='+get_geonames_username()
	country_iso = get_country_iso_code(country)
	if country_iso:
		api_url = api_url+'&country='+country_iso

	response = requests.get(api_url)
	
	response_json = json.loads(response.text)

	if 'totalResultsCount' in response_json and response_json['totalResultsCount'] > 0:

		if 'population' in response_json['geonames'][0] and response_json['geonames'][0]['population'] !=0:
			# print("Location "+location+" exists and its population is "+str(response_json['geonames'][0]['population']))
			return True, response_json['geonames'][0]['population']
		else:
			# print("Location "+location+" exists but we couldnt find population")
			return True, False
	else:
		# print(location+" is NOT a location")
		return False, False

def get_population_from_google_query_result(query_result):
	'''
	Get ready to receive populations in different formats, such as:
	 
	3,685\n2010
	91,411 (2018)
	14,810,001 // New england
	
	 
	17 million people
	1.655 million (2010) // Ecatepec de Morelos
	'''

	try:
		clean_query_result = query_result

		#14,810,001
		clean_query_result = clean_query_result.replace(',','')

		#3685\n2010
		clean_query_result = clean_query_result.split("\n")[0]

		#1.655 million (2010)
		if(" " in clean_query_result):
			clean_query_result = " ".join(clean_query_result.split(" ")[:-1])

		#1.655 million
		#Replace '.' and million
		if len(clean_query_result.split(" "))>1:
			result = float(clean_query_result.split(" ")[0])
			multiplier = clean_query_result.split(" ")[1]
			if multiplier == 'million':
				result = result * 1000000

			clean_query_result = result
		
		result =  int(clean_query_result)
	except Exception as e:
		# print("problem paring query result to int")
		# print(e)
		# print(query_result)
		return False

	return result

def google_population(location):
	#Query google
	query_result = ask_google(location+" population")

	# print("Google query result: ")
	# print(query_result)

	population = get_population_from_google_query_result(query_result)
	if population:
		# print("Googled population for "+location+" is "+str(population))
		return population
	else:
		# print("Could not google population for "+location)
		return False

def get_locations_with_low_population(locations, country, low_populations_threshold=20000, return_one=None, consider_low_population_if_unknown_population=False):
	#Check which strings of locations correspond to locations whith low_populations
	#If return_one is set to True, method returns first location with low population
	#If consider_low_population_if_unknown_population is set to True, locations with unknown population will be labelled as low population (conservative approach)
	
	locations_with_low_population = []
	locations_with_unknown_population = []

	# print("Locations to look at:")
	# print(locations)

	for index, location in enumerate(locations):
		print(str(index)+'/'+str(len(locations)))
		print(location)

		location_exists, population = check_location_exists_and_population_size(location, country)
		if location_exists:
			if not population:
				population = google_population(location)
			
			if population:
				if population < low_populations_threshold:
					# print(location+" is a location with LOW pop")
					if return_one:
						return location
					else:
						locations_with_low_population.append(location)
				else:
					#We know for sure now that we are indeed in a column with locations, given that for one of them we were able to get its population

					#We want to activate consider_low_population_if_unknown_population as long as we are sure that this column has locations (aka, we have already found at least one location and we were able to extract its population)
					#We also add all locations found so far with unkwon population to the list of locations with low population
					if consider_low_population_if_unknown_population is False:
						locations_with_low_population.extend(locations_with_unknown_population)				
						consider_low_population_if_unknown_population = True

			
			else:
				#If the population is unknown, there are 2 possibilities. 
				#The first one is a conservative approach: a location with unkown population is considered to have low population
				#The other is to discard them. This is useful for the case of columns that actually dont have locations, but some word might match a location
				#For this second scenario, we will save all locations with unknown population, and if we happen to realize we are in the scenario of a column with locations, only then we will add them all to the list of location wit low populations.
				if consider_low_population_if_unknown_population:
					if return_one:
						return location
					else:
						locations_with_low_population.append(location)
				else: #We still dont know if we are in a column with locations
					locations_with_unknown_population.append(location)

		
	if return_one:
		return False
	else:
		return locations_with_low_population



#**************FOREBEARS API TO CHECK NAMES*********

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

    if "results" in json_response:
        for result in json_response["results"]:
            #Names that exist come with the field 'jurisdictions'
            #We will also ask a minimum of 50 world incidences 
            if('jurisdictions' in result and len(result['jurisdictions'])>0):
                try:
                    world_incidences = int(result['world']['incidence'])

                    if world_incidences > 50:
                        names_found.append(result['name'])
                except Exception as e:
                    print("error in get_names_from_json_response")
                    print(e)
                    print(result)
                    print(json_response["results"])
    else:
        print("NO RESULTS IN RESPONSE")
        print(json_response)

    return names_found

def find_names_in_list_string(list_potential_names):
    '''
    Uses https://forebears.io/onograph/documentation/api/location/batch to find names in list_potential_names
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
            
            #Opportunity of improvement: If i already found a name as a forename, dont query it as a surname

    return list(all_names_found)