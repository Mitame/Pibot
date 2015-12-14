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
import sys

data_dir = os.path.join(
                os.path.abspath(
                    os.path.split(
                        sys.argv[0]
                    )[0]
                ), "userdata"
            )

if not os.path.exists(data_dir):
    os.makedirs(data_dir)


def get_user_dir(username):
    user_dir = os.path.join(data_dir, username)  # This should probably be done differently
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    return user_dir


def get_user_script_dir(username):
    user_scripts_dir = os.path.join(get_user_dir(username), "scripts")
    if not os.path.exists(user_scripts_dir):
        os.makedirs(user_scripts_dir)
    return user_scripts_dir
