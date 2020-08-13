# Flagged strings from R script
restricted_location = ['district', 'country', 'subcountry', 'parish', 'lc', 'village', 'community', 'address', 'gps', 'lat', 'log', 'coord', 'location', 'house','compound', 'panchayat', 'name', 'fname', 'lname', 'first_name', 'last_name', 'birth', 'birthday', 'bday', ]

restricted_other = ['school','social','network','census','gender','sex','fax','email','url','child','beneficiary','mother','wife','father','husband']

# Flagged strings from Stata script
restricted_stata = ['nam','add','vill','dist','phone','parish','loc','acc','plan','email','medic','health','insur','num','resid','contact','home','comment','spec','id','enum', 'city', 'info', 'data', 'comm', 'count'] #'fo'

# Flagged strings from IPA guideline document
restricted_ipa = ['name', 'birth', 'phone', 'district', 'county', 'subcounty', 'parish', 'lc', 'village', 'community', 'address', 'gps', 'lat', 'lon', 'coord', 'location', 'house', 'compound', 'school', 'social', 'network', 'census', 'gender', 'sex', 'fax', 'email', 'ip', 'url', 'specify', 'comment']

# Additions
restricted_expansions = ['name', 'insurance', 'medical', 'number', 'enumerator', 'rand', 'random', 'child_age', 'uid', 'latitude', 'longitude', 'coordinates', 'web', 'website', 'hh', 'address', 'age', 'nickname', 'nick_name', 'firstname', 'lastname', 'sublocation', 'alternativecontact', 'division', 'gps', 'resp_name', 'resp_phone', 'head_name', 'headname', 'respname', 'subvillage', 'survey_location']
restricted_spanish = ['apellidos', 'beneficiario', 'casa', 'censo', 'ciudad', 'comentario / coment', 'comunidad', 'contacto', 'contar', 'coordenadas', 'coordenadas', 'data', 'direccion', 'direccion', 'distrito', 'distrito', 'edad', 'edad_nino', 'email', 'encuestador', 'encuestador', 'escuela', 'colegio ', 'esposa', 'esposo', 'fax', 'fecha_nacimiento', 'fecha_nacimiento', 'fecha_nacimiento', 'genero', 'gps', 'hogar', 'id', 'identificador', 'identidad', 'informacion', 'ip', 'latitud', 'latitude', 'locacion', 'longitud', 'madre', 'medical', 'medico', 'nino', 'nombre', 'nombre', 'numero', 'padre', 'pag_web', 'pais', 'parroquia', 'plan', 'primer_nombre', 'random', 'red', 'salud', 'seguro', 'sexo', 'social', 'telefono', 'fono', 'tlfno', 'ubicacion', 'url', 'villa', 'web']
restricted_swahili = ['jina', 'simu', 'mkoa', 'wilaya', 'kata', 'kijiji', 'kitongoji', 'vitongoji', 'nyumba', 'numba', 'namba', 'tarahe ya kuzaliwa', 'umri', 'jinsi', 'jinsia']


def get_restricted_words():
    all_restricted = restricted_location + restricted_other + restricted_stata + restricted_ipa + restricted_expansions + restricted_spanish + restricted_swahili
    all_restricted = list(set(all_restricted))
    return all_restricted