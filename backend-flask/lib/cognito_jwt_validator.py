# Copyright 2017-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.

import os
import logging
import json
import time
import urllib.request
from functools import wraps
from flask import request, jsonify, redirect, url_for
from jose import jwk, jwt
from jose.utils import base64url_decode
from jose.exceptions import JWTError, JWSError

LOGGER = logging.getLogger(__name__)
region = os.getenv("AWS_REGION")
userpool_id = os.getenv("AWS_COGNITO_USER_POOL_ID")
app_client_id = os.getenv("AWS_COGNITO_APP_CLIENT_ID")
keys_url = "https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json".format(
    region, userpool_id
)
# instead of re-downloading the public keys every time
# we download them only on cold start
# https://aws.amazon.com/blogs/compute/container-reuse-in-lambda/
with urllib.request.urlopen(keys_url) as f:
    response = f.read()
keys = json.loads(response.decode("utf-8"))["keys"]


def _is_valid_cognito_token(token):
    try:
        # get the kid from the headers prior to verification
        headers = jwt.get_unverified_headers(token)
        kid = headers["kid"]
        # search for the kid in the downloaded public keys
        key_index = -1
        for i in range(len(keys)):
            if kid == keys[i]["kid"]:
                key_index = i
                break
        if key_index == -1:
            print("Public key not found in jwks.json")
            return False
        # construct the public key
        public_key = jwk.construct(keys[key_index])
        # get the last two sections of the token,
        # message and signature (encoded in base64)
        message, encoded_signature = str(token).rsplit(".", 1)
        # decode the signature
        decoded_signature = base64url_decode(encoded_signature.encode("utf-8"))
        # verify the signature
        if not public_key.verify(message.encode("utf8"), decoded_signature):
            print("Signature verification failed")
            return False
        print("Signature successfully verified")
        # since we passed the verification, we can now safely
        # use the unverified claims
        claims = jwt.get_unverified_claims(token)
        # additionally we can verify the token expiration
        if time.time() > claims["exp"]:
            print("Token is expired")
            return False
        # and the Audience  (use claims['client_id'] if verifying an access token)
        if claims["aud"] != app_client_id:
            print("Token was not issued for this audience")
            return False
        # now we can use the claims
        # print(claims)
        return True
    except (JWTError, JWSError) as e:
        print(f"Error decoding token: {e}")
        return False


def cognito_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get the token from the Authorization header
            token = None
            if "Authorization" in request.headers:
                token = request.headers["Authorization"].split(" ")[1]

            if not token:
                # return jsonify({"message": "Token is missing"}), 403
                return redirect(url_for('signin'))

            if not _is_valid_cognito_token(token):
                # return jsonify({"message": "Token is invalid"}), 403
                return redirect(url_for('signin'))

        except Exception as e:
            LOGGER.error(str(e))
            return redirect(url_for('signin'))
            # return (
            #     jsonify({"message": "An error occurred while validating the token"}),
            #     500,
            # )

        return f(*args, **kwargs)

    return decorated_function
