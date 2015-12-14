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

from pibot import app, api
from flask import render_template, request, redirect
from .helpers import get_redirect_target, get_current_user, get_user

import re

@app.route("/")
def home():
    return render_template("index.jinja")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.jinja")

    elif request.method == "POST":
        try:
            username = request.form["username"]
            password = request.form["password"]
        except KeyError as e:
            return render_template("login.jinja", error_message="'%s' was not specifed." % e.args)

        if username == "":
            return render_template("login.jinja", error_message="Username was not specifed.")
        elif password == "":
            return render_template("login.jinja", error_message="Password was not specifed.")

        try:
            user = api.user.login(username, password)
        except (api.user.UserNotFound, api.user.IncorrectPassword):
            return render_template("login.jinja", error_message="Username and password did not match.")

        session = api.session.create(user)

        target = get_redirect_target()
        if target is not None:
            res = redirect(target, 302)
        else:
            res = redirect("/", 302)
        res.set_cookie("session_token", session)

        return res

permitted_username = re.compile("^[a-zA-Z0-9_\-.@]{4,30}$")

@app.route("/signup", methods=["GET", "POST"])
def newuser():
    if request.method == "GET":
        user = get_current_user(required=False)
        if user:
            return redirect("/", 302)
        else:
            return render_template("signup.jinja")
    elif request.method == "POST":
        try:
            username = request.form["username"]
            password = request.form["password"]
            password_confirmation = request.form["password_confirmation"]
        except KeyError as e:
            return render_template("signup.jinja", error_message="'%s' was not specifed." % e.args)

        if username == "":
            return render_template("signup.jinja", error_message="Username was not specifed.")
        elif password == "":
            return render_template("signup.jinja", error_message="Password was not specifed.", username=username)
        elif password != password_confirmation:
            return render_template("signup.jinja", error_message="Passwords did not match.", username=username)


        if not permitted_username.match(username):
            print(username, permitted_username)
            return render_template("signup.jinja", error_message="Username must be between 4 and 30 characters long and contain only a-z, A-Z, 0-9, underscores, hyphens, periods and @ symbols.", username=username)

        try:
            created = api.user.create(username, password)
        except api.user.UsernameInUse:
            return render_template("signup.jinja", error_message="Username is already in use.")

        if created:
            return render_template("user/created.jinja", username=username)
        else:
            return render_template("signup.jinja", error_message="An unknown error occurred", username=username)


@app.route("/logout")
def logout():
    try:
        api.session.logout(request.cookies.get("session_token"))
    except (api.session.SessionExpired, api.session.SessionInvalid, api.session.SessionTokenInvalid) as e:
        print(e.message)
    res = redirect("/")
    res.delete_cookie("session_token")
    return res


@app.route("/<username>/")
def user_profile(username):
    user = get_user(username)

    # redirect to their capitalised user name
    if user["username"] != username:
        return redirect("/%s/scripts/" % user["username"], 301)

    return username


@app.route("/<username>/scripts/")
def user_scripts(username):
    user = get_user(username)

    # redirect to their capitalised user name
    if user["username"] != username:
        return redirect("/%s/scripts/" % user["username"], 301)

    scripts = api.script.get_scripts_by_user(username)

    return render_template("user/scripts.jinja", target_user=user, scripts=scripts)

@app.route("/<username>/script/<title>/")
def view_edit_script(username, title):
    target_user = get_user(username)

    # redirect to their capitalised user name
    if target_user["username"] != username:
        return redirect("/%s/scripts/%s/%s" % (user["username"], title, mode), 301)

    current_user = get_current_user(required=False)
    can_edit = current_user and current_user["username"] == target_user["username"]

    script_info = api.script.get_script_info(username, title)

    if script_info["latest_revision"] == -1:
        script_body = ""
    else:
        script = api.script.get_script(username, title)
        script_body = script.read()
    if can_edit:
        return render_template("edit_script.jinja", script_info=script_info, script_body=script_body)
    else:
        return render_template("view_script.jinja", script_info=script_info, script_body=script_body)


@app.route("/<username>/script/<title>/<int:revision>")
def view_edit_script_with_revision(username, title, revision):
    target_user = get_user(username)

    # redirect to their capitalised user name
    if target_user["username"] != username:
        return redirect("/%s/script/%s/%i" % (target_user["username"], title, revision), 301)

    # set the mode
    current_user = get_current_user(required=False)
    if current_user and current_user["username"] == target_user["username"]:
        mode = "edit"
    else:
        mode = "view"

    # get the script info and data
    script_info = api.script.get_script_info(username, title)
    try:
        script = api.script.get_script(username, title, revision)
    except api.script.RevisionNotFound:
        return redirect("/%s/script/%s" % (target_user["username"], title), 301)
    script_body = script.read()

    return render_template("view_script.jinja", script_info=script_info, revision=revision, script_body=script_body)


@app.route("/scripts")
def scripts():
    return render_template("scripts.jinja")


@app.route("/script/upload/", methods=["POST"])
def script_upload():
    try:
        title = request.form["title"]
        try:
            script_body = request.files["file"].read()
        except KeyError:
            script_body = request.form["script_body"]
    except KeyError as e:
        return "'%s' is missing." % e.args, 400

    user = get_current_user(required=True)
    api.script.add_script(user["username"], title, script_body)
    return redirect("/%s/scripts/" % user["username"])


@app.route("/script/new/", methods=["POST"])
def editor_test():
    try:
        title = request.form["title"]
    except KeyError as e:
        return "'%s' is missing." % e.args, 400

    if not api.script.title_must_match.match(title):
        return "'%s' is not a valid title" % new_title, 400

    user = get_current_user(required=True)
    api.script.new_script(user["username"], title)
    return redirect("/%s/script/%s/" % (user["username"], title), 302)
