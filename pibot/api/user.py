# PiBot - A site for controlling Raspberry Pi Powered robots
# Copyright (C) 2015  Mitame
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from flask import request, jsonify
from hashlib import sha256
import time
import os

from .. import app

from . import db
col_users = db["users"]
col_users.create_index("username_lower", unique=True)


class UserNotFound(Exception):
    def __init__(self, username):
        Exception.__init__(self)
        self.username = username
        self.text = "Could not find '%s' in users."


class IncorrectPassword(Exception):
    def __init__(self):
        Exception.__init__(self)
        self.text = "Password used was incorrect."


class UsernameInUse(Exception):
    def __init__(self, username):
        Exception.__init__(self)
        self.username = username
        self.text = "'%s' is in use by another user." % username


class InvalidAPIUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["success"]= False
        rv['message'] = self.message
        return rv


class MissingArgument(BaseException):
    status_code = 400
    def __init__(self, argument_name):
        InvalidUsage.__init__(self, "'%s' was not specified." % argument_name)


def login(username, password):
    cur = col_users.find({"username_lower": username.lower()}).limit(1)
    try:
        user = cur[0]
    except IndexError:
        raise UserNotFound(username)


    hasher = sha256()
    hasher.update(password.encode("utf8"))
    hasher.update(user["salt"])
    passhash = hasher.digest()
    if passhash == user["passhash"]:
        return user
    else:
        raise IncorrectPassword()


def create(username, password):
    salt = os.urandom(32)

    hasher = sha256()
    hasher.update(password.encode("utf8"))
    hasher.update(salt)
    passhash = hasher.digest()
    try:
        cur = col_users.insert({
            "username": username,
            "screen_name": username,
            "username_lower": username.lower(),
            "passhash": passhash,
            "salt": salt,
            "created": time.time(),
            "last_login": -1,
        })
    except pymongo.errors.DuplicateKeyError as e:
        raise UsernameInUse(username)

    return True


def get(username):
    cur = col_users.find({
        "username_lower": username.lower()
    }).limit(1)
    try:
        return cur[0]
    except:
        raise UserNotFound(username)


def update_password(username, password):
    salt = os.urandom(32)

    hasher = sha256()
    hasher.update(password.encode("utf8"))
    hasher.update(salt)
    passhash = hasher.digest()

    cur = col_users.update(
        {"user_lower": username.lower()},
        {
            "$set":
            {
                "passhash": passhash,
                "salt": salt,
            }
        }
    )

    return True


@app.errorhandler(InvalidAPIUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/api/script/add", methods=["POST"])
def add_script():
    try:
        user_id = request.form["user_id"]
        script_name = request.form["script_name"]
    except KeyError as e:
        raise MissingArgument(e.args)

    try:
        script = request.files["script"]
    except KeyError:
        try:
            script = request.form["script"]
        except KeyError as e:
            raise MissingArgument(e.args)
    return jsonify({
        "user_id": user_id,
        "script_name": script_name,
        "script_body": script
    })
