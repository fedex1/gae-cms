"""
@org: GAE-CMS.COM
@description: Python-based CMS designed for Google App Engine
@(c): gae-cms.com 2012
@author: Imran Somji
@license: GNU GPL v2

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

from google.appengine.api import users

def is_admin(path):
    return users.is_current_user_admin() # TODO: currently only super admins can do page management

def view_section(section):
    if not section.is_private:
        return True # TODO: if a parent is private then the child should inherit that
    elif section.is_private and users.is_current_user_admin():
        return True # TODO: currently only super admins can view private page
    return False

def perform_action(content, path, path_action):
    for action in content.actions:
        if path_action == action[0]: return action[3] or is_admin(path) # TODO: Check if actually has permission
    raise Exception('NotFound')

def view_content(content, section, view_id):
    for view in content.views:
        if view_id == view[0]: return view_section(section)
    raise Exception('NotFound')