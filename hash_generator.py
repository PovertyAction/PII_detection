import hashlib
import hmac
def sha1(message):
    return hashlib.sha1(bytes(message, encoding='utf-8')).hexdigest()

def hmac_sha1(secret_key, message):

    h = hmac.new(bytes(secret_key, encoding='utf-8'), msg=bytes(message, encoding='utf-8'), digestmod=hashlib.sha1)
    return h.hexdigest()

if __name__ == '__main__':
    print(sha1(message="The Ore-Ida brand is a syllabic abbreviation of Oregon and Idaho"))
    #Should print 156a5e19b6301e43794afc5e5aff0584e25bfbe7
    print(hmac_sha1(secret_key = "Secret Key", message = "Message to be sent"))
    #Should print d5052c13e868ea7c932be9279752e9e67c8195bd
