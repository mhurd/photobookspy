# All the code required to make correctly signed requests to Amazon for
# information by ISBN. You'll need your amazon access key, associate id
# and secret to use this.

import datetime
import hashlib
import urllib.parse

from base64 import b64encode
from collections import OrderedDict
from hmac import HMAC

api_version = '2011-08-01'
service_name = 'AWSECommerceService'
api_host = 'ecs.amazonaws.co.uk'
api_url = '/onca/xml'
utf8 = 'UTF-8'

# Creates a hashed message authentication code from the supplied
# SecretKeySpec (holds the secret) and the string to encode. Its 
# base-64 encoded to save space (both hex encoding and base64 will 
# turn a hash into a valid ASCII string. However, a hex string (where 
# bytes are each represented as two ASCII characters between 0 and F) 
# will take twice as much space as the original, while the base64 
# version will only take four thirds as much space. A hex-encoded 
# SHA-256 is 64 bytes, while a base64-encoded SHA-256 is more or less 
# 43 bytes)
def create_hmac(secret, str_to_encode):
    new_hmac = HMAC(secret.encode(encoding=utf8), 
                    str_to_encode.encode(encoding=utf8),
                    hashlib.sha256)
    return b64encode(new_hmac.digest())

# Encodes the URL additionally encoding '+' to spaces,
# See http://stackoverflow.com/questions/2678551/when-to-encode-space-to-plus-or-20"
def percent_encode_rfc_3986(str_to_encode):
    return urllib.parse.quote(str_to_encode)

def current_iso_8601_timestamp():
    # yyyy-MM-dd'T'HH:mm:ss'Z'
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def get_basic_args(amazon_access_key, amazon_associate_tag):
    return OrderedDict([("Service", service_name),
                        ("Version", api_version),
                        ("AWSAccessKeyId", amazon_access_key),
                        ("AssociateTag", amazon_associate_tag),
                        ("Condition", "All"),
                        ("Offer", "All"),
                        ("ResponseGroup", "ItemAttributes,OfferSummary,Images")])

def merge_and_encode_args_with_timestamp(amazon_access_key, amazon_associate_tag, args_dict):
    merged_args = get_basic_args(amazon_access_key, amazon_associate_tag)
    for key, value in args_dict.items():
        merged_args[key] = value
    merged_args["Timestamp"] = current_iso_8601_timestamp()  
    encoded_arg_str = ""
    for key in sorted(merged_args.keys()):
        encoded_arg_str = encoded_arg_str + percent_encode_rfc_3986(key) + "=" + percent_encode_rfc_3986(merged_args[key]) + "&"
    return encoded_arg_str[:-1]

def create_signed_url(amazon_access_key, amazon_associate_tag, args_dict, secret):
    merged_arg_str = merge_and_encode_args_with_timestamp(amazon_access_key, amazon_associate_tag, args_dict)
    to_sign = "GET\n" + api_host + "\n" + api_url + "\n" + str(merged_arg_str)
    signature = percent_encode_rfc_3986(create_hmac(secret, to_sign))
    return api_url + "?" + merged_arg_str + "&Signature=" + signature

def find_by_isbn(amazon_access_key, amazon_associate_tag, secret, isbn):
    args_dict = OrderedDict([("Operation", "ItemLookup"),
                             ("ItemId", isbn),
                             ("IdType", "ASIN")])
    url = "https://" + api_host + create_signed_url(amazon_access_key, amazon_associate_tag, args_dict, secret)
    return url

def find_offer_summary_by_isbn(amazon_access_key, amazon_associate_tag, secret, isbn):
    args_dict = OrderedDict([("ResponseGroup", "OfferSummary"),
                             ("Operation", "ItemLookup"),
                             ("ItemId", isbn),
                             ("IdType", "ASIN")])
    url = "https://" + api_host + create_signed_url(amazon_access_key, amazon_associate_tag, args_dict, secret)
    return url