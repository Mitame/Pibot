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

import os
import binascii
import time

from . import db
from .user import col_users
col_sessions = db["sessions"]


class SessionTokenInvalid(Exception):
    def __init__(self):
        Exception.__init__(self)
        self.message = "Session token is invalid."


class SessionInvalid(Exception):
    def __init__(self):
        Exception.__init__(self)
        self.message = "Session is invalid."


class SessionExpired(Exception):
    def __init__(self):
        Exception.__init__(self)
        self.message = "The session has expired."


def create(user, does_expire=True, timeout=60*60*24, ip_addr=None):
    session_token = binascii.b2a_hex(os.urandom(16)).decode("utf8")
    username = user["username"]

    col_sessions.insert(
        {
            "username": username,
            "session_token": session_token,
            "created": time.time(),
            "session_from": ip_addr,
            "valid_until": (time.time() + timeout) if does_expire else -1,
            "is_valid": True
        }
    )
    col_users.update(
        {"username": username},
        {
            "$set":{"last_login": time.time()}
        }
    )

    return session_token


def login(session_token):
    cur = col_sessions.find({"session_token": session_token}).limit(1)
    try:
        session = cur[0]
    except IndexError:
        raise SessionTokenInvalid()

    if not session["is_valid"]:
        raise SessionInvalid()

    if session["valid_until"] != -1 and session["valid_until"] < time.time():
        raise SessionExpired()

    username = session["username"]

    cur = col_users.find({"username": username})

    try:
        return cur[0]
    except:
        raise SessionInvalid()


def logout(session_token):
    cur = col_sessions.update(
        {"session_token": session_token},
        {
            "$set": {
                "is_valid": False
            }
        }
    )
    return True
