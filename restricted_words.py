#Fuzzy = variables that if contained inside a column name/label, there will be a match
#Strict = variables that if are strictly equal to column name/label, there will be a match

locations_strict = ['vill', 'lc']

#For location matching
locations_fuzzy = ['district', 'country', 'subcountry', 'parish', 'village', 'community', 'location', 'panchayat', 'compound', 'survey_location', 'county', 'subcounty', 'ciudad','distrito','villa','city', 'town', 'neighbourhood', 'barangay', 'brgy']

# Flagged strings from Stata script
stata_strict = ['nam','add','addr','addr1','addr2','dist','parish','loc','acc','plan','medic','health','insur','num','resid','home','spec','id','enum', 'info', 'data', 'comm', 'count', 'fo']

# Flagged strings from IPA guideline document
ipa_strict = ['gps', 'lat', 'lon', 'coord', 'house', 'social', 'census', 'fax', 'ip', 'url', 'specify', 'enumerator', 'random']

other_strict = ['rand','uid','hh', 'age', 'gps','id', 'ip','red','fono','url', 'web', 'number', 'encuestador', 'escuela', 'colegio','edad', 'insurance', 'school', 'birth']

survey_cto_strict = ['deviceid', 'subscriberid', 'simid', 'formdef_version']

fuzzy = [' name', '_name','fname', 'lname', 'first_name', 'last_name', 'birthday', 'bday','address', 'network','email','beneficiary','mother','wife','father','husband', 'medical', 'enumerator ','enumerator_', 'child_age', 'latitude', 'longitude', 'coordinates', 'website', 'nickname', 'nick_name', 'firstname', 'lastname', 'sublocation', 'alternativecontact', 'division', 'resp_name', 'head_name', 'headname', 'respname', 'subvillage', 'comment', 'notes', 'contact']
#adding an empty space in front of name to avoid match with ${name}


#'phone' removing phone given that we already have the phone format detector
#telefono', 'telefonico', 'teléfono', 'telefónico'
#'telefono', 'tlfno'

spanish_fuzzy = ['apellido', 'apellidos', 'beneficiario', 'censo',  'comentario', 'comunidad', 'contar', 'coordenadas', 'direccion', 'edad_nino', 'email', 'esposa', 'esposo', 'fecha_nacimiento', 'genero', 'identificador', 'identidad', 'informacion', 'latitud', 'latitude', 'locacion', 'longitud', 'madre', 'medical', 'medico', 'nino', 'nombre', 'numero', 'padre', 'pag_web', 'pais', 'parroquia', 'primer_nombre', 'random', 'salud', 'seguro', 'ubicacion']

swahili_strict = ['jina', 'simu', 'mkoa', 'wilaya', 'kata', 'kijiji', 'kitongoji', 'vitongoji', 'nyumba', 'numba', 'namba', 'tarahe ya kuzaliwa', 'umri', 'jinsi', 'jinsia']

def get_locations_strict_restricted_words():
	return locations_strict

def get_locations_fuzzy_restricted_words():
	return locations_fuzzy

def get_strict_restricted_words():
    strict_restricted = stata_strict + ipa_strict + other_strict  + swahili_strict + survey_cto_strict + locations_strict
    return list(set(strict_restricted))

def get_fuzzy_restricted_words():
    fuzzy_restricted = fuzzy + spanish_fuzzy + locations_fuzzy
    return list(set(fuzzy_restricted))

#Check for repeated words in lists of strict and fuzzy
#strict = get_strict_restricted_words()
#fuzzy = get_fuzzy_restricted_words()
#print([word for word in strict if word in fuzzy])
