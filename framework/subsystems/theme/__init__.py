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

import os

from google.appengine.ext import db

from django.template import TemplateDoesNotExist

from framework.subsystems import cache
from framework.subsystems import utils

CACHE_KEY = 'CUSTOM_THEMES'
DEFAULT_LOCAL_THEME_TEMPLATE = 'Google Code/Default'

class Theme(db.Model):

    namespace = db.StringProperty()
    body_template_names = db.StringListProperty()
    body_template_contents = db.ListProperty(item_type=db.Text)
    css_filenames = db.StringListProperty()
    css_contents = db.ListProperty(item_type=db.Text)
    js_filenames = db.StringListProperty()
    js_contents = db.ListProperty(item_type=db.Text)
    image_filenames = db.StringListProperty()
    image_keys = db.StringListProperty()

def get_local_theme_namespaces():
    templates = []
    for namespace in os.listdir('./themes'):
        template = []
        for filename in os.listdir('./themes/' + namespace + '/templates'):
            if filename.endswith('.body'):
                template.append([namespace + '/' + filename[:-5], namespace + ' &ndash; ' + filename[:-5]])
        templates.append([namespace, template])
    return templates

def get_custom_theme_namespaces():
    custom_themes = []
    for custom_theme in get_custom_themes():
        templates = []
        for template_name in custom_theme.body_template_names:
            templates.append([custom_theme.namespace + '/' + template_name, custom_theme.namespace + ' &ndash; ' + template_name])
        custom_themes.append([custom_theme.namespace, templates])
    return custom_themes

def is_local_theme_template(t):
    for namespace in os.listdir('./themes'):
        for filename in os.listdir('./themes/' + namespace + '/templates'):
            if namespace + '/' + filename == t + '.body':
                return True
    return False

def is_local_theme_namespace(n):
    return n in os.listdir('./themes')

def get_custom_themes():
    custom_themes = cache.get(CACHE_KEY)
    if not custom_themes:
        custom_themes = Theme.gql("")
        cache.set(CACHE_KEY, custom_themes)
    return custom_themes

def get_custom_theme(namespace):
    for t in get_custom_themes():
        if t.namespace == namespace:
            return t
    return None

def get_custom_template(theme_template):
    namespace, template_name = theme_template.split('/')
    try:
        t = Theme.gql("WHERE namespace=:1", namespace)[0]
        index = t.body_template_names.index(template_name)
        return t.body_template_contents[index]
    except:
        pass
    raise TemplateDoesNotExist