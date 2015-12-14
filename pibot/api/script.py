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

from . import db
from ..helpers import get_current_user
from ..userdata import get_user_script_dir
from .. import app
from os import path, mkdir, rename
import time
from flask import request, jsonify
import re

col_scripts = db["scripts"]


title_must_match = re.compile("^[^/\"']{4,30}?$")

class ScriptNotFound(Exception):
    def __init__(self, username, title):
        Exception.__init__(self)
        self.username = username
        self.title = title
        self.message = "Could not find a script called '%s' by '%s'." % (title, username)


class RevisionNotFound(Exception):
    def __init__(self, username, title, revision):
        Exception.__init__(self)
        self.username = username
        self.title = title
        self.revision = revision
        self.message = "Could not find revision '%i' for '%s' by '%s'." % (revision, title, username)


def add_script(username, title, body, no_revisions=False):
    try:
        script_info = get_script_info(username, title)
        if no_revisions:
            raise "Somethin!"
        revision = script_info["latest_revision"] + 1
    except ScriptNotFound:
        script_info = {
            "username": username,
            "title": title,
            "internal_path": path.join(get_user_script_dir(username), title),
            "revisions": [
                {
                    "id": 0,
                    "created_at": time.time()
                }
            ],
            "latest_revision": 0
        }
        mkdir(script_info["internal_path"])
        revision = 0

    with open(path.join(script_info["internal_path"], str(revision)), "wb") as script_file:
        script_file.write(body)

    if revision:
        script_info["revisions"].append({
            "id": revision,
            "created_at": time.time()
        })
        script_info["latest_revision"] = revision
        col_scripts.update({
            "username": username,
            "title": title
            },
            script_info
        )
    else:
        col_scripts.insert(script_info)



def get_scripts_by_user(username):
    cur = col_scripts.find({
        "username": username
    })
    return tuple(cur)


def get_script_info(username, title):
    cur = col_scripts.find({
        "username": username,
        "title": title
    }).limit(1)

    try:
        return cur[0]
    except IndexError:
        raise ScriptNotFound(username, title)


def get_script(username, title, revision=None):
    script_info = get_script_info(username, title)
    if revision is not None:
        try:
            return open(path.join(script_info["internal_path"], str(int(revision))))
        except FileNotFoundError:
            raise RevisionNotFound(username, title, revision)
    else:
        return open(path.join(script_info["internal_path"], str(int(script_info["latest_revision"]))))


def rename_script(username, title, new_title):
    script_info = get_script_info(username, title)
    new_path = path.join(get_user_script_dir(script_info["username"]), new_title)

    rename(script_info["internal_path"], new_path)

    cur = col_scripts.update(
        {"username": username, "title": title},
        {"$set": {
            "internal_path": new_path,
            "title": new_title
            }
        }
    )

    return True


def new_script(username, title):
    script_info = {
        "username": username,
        "title": title,
        "latest_revision": -1,
        "revisions": [],
        "internal_path": path.join(get_user_script_dir(username), title)
    }
    mkdir(script_info["internal_path"])

    cur = col_scripts.insert(script_info)


@app.route("/api/script/rename", methods=["POST"])
@app.route("/api/script/rename/", methods=["POST"])
def api_rename_script():
    try:
        old_title = request.form["old_title"]
        new_title = request.form["new_title"]
    except KeyError as e:
        return "'%s' was missing" % e.args, 400

    if not title_must_match.match(new_title):
        return "'%s' is not a valid title" % new_title, 400

    user = get_current_user()
    rename_script(user["username"], old_title, new_title)
    return jsonify({
        "ok": True
    })


@app.route("/api/script/upload", methods=["POST"])
@app.route("/api/script/upload/", methods=["POST"])
def api_upload():
    try:
        title = request.form["title"]
        try:
            script_body = request.files["file"]
        except KeyError:
            script_body = request.form["script_body"]
    except KeyError as e:
        return "'%s' was missing" % e.args, 400

    if not title_must_match.match(title):
        return "'%s' is not a valid title" % new_title, 400

    user = get_current_user(required=True)
    print("got new script", title)
    add_script(user["username"], title, script_body.encode("utf8"))

    return jsonify({
        "ok": True
    })
