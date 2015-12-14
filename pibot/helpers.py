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

from . import app
from .api import session, user

from flask import request, redirect, make_response, render_template
from urllib.parse import urlparse, quote
from datetime import datetime

def get_redirect_target():
    host = urlparse(request.host_url)
    try:
        target = urlparse(request.args["r"])
        print(target)
        if target.scheme in ("http", "https", "") and target.netloc in (host.netloc, ""):
            return target.path
    except KeyError:
        return None


class ForceRedirect(Exception):
    status_code = 301

    def __init__(self, address):
        Exception.__init__(self)
        self.address = address


class LoginRequired(Exception):
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


@app.errorhandler(LoginRequired)
def redirect_to_login():
    target = urlparse(request.host_url)
    return redirect("/login?r=%s" % quote(target.path), 302)


@app.errorhandler(ForceRedirect)
def handle_forced_redirect(error):
    return redirect(error.address, 302)


@app.errorhandler(user.UserNotFound)
def handle_user_not_found(error):
    # print(error.message)
    print(error.username)
    res = make_response(render_template("user/missing.jinja", username=error.username))
    res.status_code = 404
    return res


@app.template_global()
def get_user(username):
    return user.get(username)


@app.template_global()
def get_current_user(required=False, redirect_on_logged_in=None):
    try:
        session_token = request.cookies.get("session_token")
        if session_token is not None:
            user = session.login(session_token)
            if redirect_on_logged_in:
                raise ForceRedirect(redirect_on_logged_in)
            else:
                return user
        else:
            return None
    except (session.SessionExpired, session.SessionInvalid, session.SessionTokenInvalid) as e:
        print(e.message)
        if required:
            raise LoginRequired()
        else:
            return None


@app.template_filter()
def nicetime(timestamp):
    d = datetime.fromtimestamp(timestamp)
    return d.strftime("%Y-%m-%d %H:%M:%S")
