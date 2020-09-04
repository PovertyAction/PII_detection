from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import pandas as pd

chrome_options = Options()
chrome_options.add_argument("--window-size=1024x768")
chrome_options.add_argument("--headless")

driver = webdriver.Chrome(executable_path=r'chromedriver.exe',options=chrome_options)

def ask_google(query):

	# Search for query
	query = query.replace(' ', '+')

	driver.get('http://www.google.com/search?q=' + query)

	# Get text from Google answer box

	answer = driver.execute_script(
	        "return document.elementFromPoint(arguments[0], arguments[1]);",
	        350, 230).text

	return answer





def is_location(location):
	#PENDING
    #Check result using https://forebears.io/place-search?q=new+england
    return True

def get_clean_query_result(query_result):
	'''
	Get ready to receive populations in different formats, such as:
	 91,411 (2018)
	 3,685\n2010
	 17 million people
	'''

	clean_query_result = query_result
	clean_query_result = clean_query_result.replace(" million","000,000")
	clean_query_result = clean_query_result.split(" ")[0]
	clean_query_result = clean_query_result.split("\n")[0]
	clean_query_result = clean_query_result.replace(',','')

	return clean_query_result
def get_population(location):
	#Query google
	query_result = ask_google(location+" population")

	try:
		clean_query_result = get_clean_query_result(query_result)
		population = int(clean_query_result)

		return population
	except:
		# print("EXCEPTION")
		# print("Couldnt parse query result to int")
		# print(location)
		# print(query_result)
		return False

def get_locations_with_low_population(locations, low_populations_threshold=20000):

	locations_with_low_population = []

	'''
	Instead of using locations.csv, I could use some of the following resources
	https://geonames.nga.mil/gns/html/namefiles.html
	http://www.geonames.org/
	'''
	all_existing_locations = pd.read_csv('locations.csv')['name'].to_list()

	for index, location in enumerate(locations):
		if(index%50==0):
			print(str(index)+'/'+str(len(locations))+':'+location)
		#Check if location string is indeed a location
		if location in all_existing_locations:
			
			population = get_population(location)
			
			if population:# and population < low_populations_threshold:
				locations_with_low_population.append(location)
	return locations_with_low_population

def check_if_any_row_is_location_has_low_population(locations, low_populations_threshold=20000):

	#Check that for elements in locations array, at least one is a location and has pop under threshold
	for location in locations:
		if is_location(location):
			population = get_population(location)
			
			if population and population < low_populations_threshold:
				return True
	return False


if __name__ == "__main__":
	print(get_locations_with_low_population(["Cabildo","New England", "Santa Monica", "Yolanda"]))