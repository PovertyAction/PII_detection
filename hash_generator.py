import hashlib
import hmac
import hmac_secret_key

def sha1(message):
    return hashlib.sha1(bytes(message, encoding='utf-8')).hexdigest()

def hmac_sha1(secret_key, message):

    h = hmac.new(bytes(secret_key, encoding='utf-8'), msg=bytes(message, encoding='utf-8'), digestmod=hashlib.sha1)
    return h.hexdigest()

if __name__ == '__main__':
    print(sha1(message="The Ore-Ida brand is a syllabic abbreviation of Oregon and Idaho"))


    example = {}
    for name in ['felipe', 'michael', 'lindsey']:
        # example[name] = hmac_sha1(secret_key = 'a', message = name)

        secret_key = hmac_secret_key.get_secret_key()
        example[name] = hmac_sha1(secret_key = secret_key, message = name)
