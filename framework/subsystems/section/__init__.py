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

import importlib, traceback, os

from google.appengine.ext import db
from google.appengine.api import users

from framework import content
from framework.subsystems import configuration
from framework.subsystems import cache
from framework.subsystems import template
from framework.subsystems.theme import DEFAULT_LOCAL_THEME_TEMPLATE
from framework.subsystems import permission
from framework.subsystems import utils

import settings

FIRST_RUN_HOME_PATH = 'home'
FORBIDDEN_EXTENSIONS = ['css', 'js']
FORBIDDEN_PATHS = ['favicon.ico', 'robots.txt', '_ah']
MAIN_CONTAINER_NAMESPACE = 'main'
CACHE_KEY_HIERARCHY = 'SECTION_HIERARCHY'

class Section(db.Model):

    path = db.StringProperty(required=True)
    parent_path = db.StringProperty()
    title = db.StringProperty()
    name = db.StringProperty()
    keywords = db.TextProperty()
    description = db.TextProperty()
    theme = db.StringProperty()
    rank = db.IntegerProperty(default = 0)
    is_private = db.BooleanProperty(default=False)
    is_default = db.BooleanProperty(default=False)
    redirect_to = db.StringProperty()
    new_window = db.BooleanProperty(default=False)

    def __unicode__(self):
        if not permission.view_section(self):
            raise Exception('AccessDenied', self.path)
        elif self.redirect_to and self.redirect_to.strip('/') != self.path and not self.path_action:
            raise Exception('Redirect', self.redirect_to)

        return template.html(self, self.get_action() if self.path_action else self.get_main_container_view())

    def get_action(self):
        item = content.get_local_else_global(self.path, self.path_namespace)
        if not item:
            raise Exception('NotFound')
        elif not permission.perform_action(item, self.path, self.path_action):
            raise Exception('Forbidden', self.path, self.path_namespace, self.path_action, self.path_params)
        return item.init(self)

    def get_main_container_view(self):
        item = content.get_else_create(self.path, 'Container', MAIN_CONTAINER_NAMESPACE)
        return item.init(self).view('default')

    def get_theme_namespace_template(self):
        TEMPLATE_OVERRIDE_THEME = self.handler.request.get('TEMPLATE_OVERRIDE_THEME') if self.handler and self.handler.request.get('TEMPLATE_OVERRIDE_THEME') else None 
        DEFAULT_THEME = configuration.default_theme()

        if TEMPLATE_OVERRIDE_THEME and configuration.theme_preview_enabled():
            theme_namespace_template = TEMPLATE_OVERRIDE_THEME
        elif not self.theme and not DEFAULT_THEME:
            theme_namespace_template = DEFAULT_LOCAL_THEME_TEMPLATE
        elif not self.theme:
            theme_namespace_template = DEFAULT_THEME
        else:
            theme_namespace_template = self.theme
        return theme_namespace_template

def get_section(handler, full_path):
    path_parts = full_path.strip('/').split('/')
    path = path_parts[0]
    path_namespace = path_parts[1] if len(path_parts) > 1 else None
    path_action = path_parts[2] if len(path_parts) > 2 else None
    path_params = path_parts[3:] if len(path_parts) > 3 else None
    try:
        if not path:
            section = Section.gql("WHERE is_default=:1 LIMIT 1", True)[0]
        else:
            section = Section.gql("WHERE ANCESTOR IS :1 LIMIT 1", section_key(path))[0]
        if section.is_default and path and not path_action:
            raise Exception('NotFound') # The default page with no action should only be accessible from root
    except:
        if not get_top_level():
            section = create_section(path=FIRST_RUN_HOME_PATH, name='Home', title='GAE-CMS', is_default=True, force=True)
        else:
            raise Exception('NotFound', path, path_action, path_params)

    section.handler = handler

    section.full_path = full_path
    section.action_redirect_path = '/' + (path if not section.is_default else '')
    section.path_namespace = path_namespace
    section.path_action = path_action
    section.path_params = path_params

    section.classes = ['yui3-skin-sam path-' + section.path]
    if path_namespace: section.classes.append('content-' + path_namespace)
    if path_action: section.classes.append('action-' + path_action)

    default_theme = configuration.default_theme()
    if not default_theme: default_theme = template.DEFAULT_LOCAL_THEME_TEMPLATE
    section.theme_namespace, section.theme_template = (section.theme if section.theme else default_theme).split('/')

    section.yuicss = []
    section.themecss = []
    section.css = ['core.css']
    section.yuijs = []
    section.localthemejs = []
    section.js = []

    section.viewport_content = None
    section.mobile_ua = utils.mobile_ua(section)

    section.logout_url = users.create_logout_url('/' + section.path if not section.is_default else '')
    section.login_url = users.create_login_url('/' + section.path if not section.is_default else '')
    section.has_siblings = len(get_siblings(section.path)) > 1
    section.has_children = len(get_children(section.path)) > 0

    section.configuration = vars(configuration.get_configuration())['_entity']

    return section

def get_helper(path, hierarchy):
    for item, children in hierarchy:
        if path == item['path']: return item
        val = get_helper(path, children)
        if val: return val
    return None

def get(path):
    return get_helper(path, get_top_level())

def get_primary_ancestor_helper(path, hierarchy):
    for item, children in hierarchy:
        if path == item['path'] or get_primary_ancestor_helper(path, children):
            return [item, children]
    return None

def get_primary_ancestor(path):
    return get_primary_ancestor_helper(path, get_top_level())

def get_second_level(path):
    return get_primary_ancestor(path)[1]

def get_children_helper(path, hierarchy):
    for item, children in hierarchy:
        if path == item['path']: return children
        val = get_children_helper(path, children)
        if val: return val
    return []

def get_children(path):
    if not path: return get_top_level()
    return get_children_helper(path, get_top_level())

def get_siblings(path):
    section = get(path)
    return get_children(section['parent_path']) if section else []

def get_top_level():
    hierarchy = cache.get(CACHE_KEY_HIERARCHY)
    if hierarchy: return hierarchy
    hierarchy = db_get_hierarchy()
    cache.set(CACHE_KEY_HIERARCHY, hierarchy)
    return hierarchy

def db_get_hierarchy(path=None):
    ret = []
    for s in Section.gql("WHERE parent_path=:1 ORDER BY rank", path):
        ret.append([{'path': s.path, 'parent_path': s.parent_path, 'rank': s.rank, 'is_private': s.is_private, 'name': s.name, 'title': s.title, 'keywords': s.keywords, 'description': s.description, 'is_private': s.is_private, 'is_default': s.is_default, 'redirect_to': s.redirect_to, 'new_window': s.new_window}, db_get_hierarchy(s.path)])
    return ret

def is_ancestor(path, another_path):
    while path != another_path:
        section = get(path)
        try:
            path = section['parent_path']
        except:
            return False
    return True

def get_depth(path):
    section = get(path)
    if not section['parent_path']:
        return 0
    else:
        return get_depth(section['parent_path']) + 1

def can_path_exist(path, parent_path, old_path=None):
    if not path:
        raise Exception('Path is required')
    elif any(path.endswith('.' + ext) for ext in FORBIDDEN_EXTENSIONS):
        raise Exception('This extension is not allowed')
    elif any(path == ext for ext in FORBIDDEN_PATHS):
        raise Exception('This path is reserved')
    elif is_ancestor(parent_path, path):
        raise Exception('Path recursion detected: path is an ancestor')
    elif old_path != path and get(path):
        raise Exception('Path already exists')
    elif parent_path and not get(parent_path):
        raise Exception('Parent path does not exist')
    return True

def create_section(path, parent_path=None, name='', title='', keywords='', description='', theme='', is_private=False, is_default=False, redirect_to='', new_window=False, force=False):
    path = path.replace('/', '-').replace(' ', '-').strip() if path else None
    parent_path = parent_path.replace('/', '-').replace(' ', '-').strip() if parent_path else None
    if not force and not can_path_exist(path, parent_path): return None

    if is_default:
        try:
            old_default = Section.gql("WHERE is_default=:1 LIMIT 1", True)[0]
            old_default.is_default=False
            old_default.put()
        except:
            pass # Probably no sections yet

    max_rank = 0
    for item, _ in get_children(parent_path):
        if item['rank'] <= max_rank: max_rank = item['rank'] + 1

    default_theme = configuration.default_theme()
    if not default_theme: default_theme = template.DEFAULT_LOCAL_THEME_TEMPLATE
    if theme == default_theme: theme = ''

    section = Section(parent=section_key(path), path=path, parent_path=parent_path, rank=max_rank, name=name, title=title, keywords=keywords, description=description, theme=(theme if theme != template.DEFAULT_LOCAL_THEME_TEMPLATE else ''), is_private=is_private, redirect_to=redirect_to, new_window=new_window, is_default=is_default)
    section.put()
    cache.delete(CACHE_KEY_HIERARCHY)
    return section

def update_section(old, path, parent_path, name, title, keywords, description, theme, is_private, is_default, redirect_to, new_window):
    path = path.replace('/', '-').replace(' ', '-').strip() if path else None
    parent_path = parent_path.replace('/', '-').replace(' ', '-').strip() if parent_path else None

    default_theme = configuration.default_theme()
    if not default_theme: default_theme = template.DEFAULT_LOCAL_THEME_TEMPLATE
    if theme == default_theme: theme = ''

    if old.is_default:
        # Cannot change the default page except if another page is promoted
        is_default = True
    elif not old.is_default and is_default:
        old_default = Section.gql("WHERE is_default=:1 LIMIT 1", True)[0]
        if old_default.path != old.path:
            old_default.is_default = False
            old_default.put()

    can_path_exist(path, parent_path, old.path)

    if old.path != path:
        for child in Section.gql("WHERE parent_path=:1", old.path):
            child.parent_path = path
            child.put()

        content.rename_section_paths(old.path, path)

        new = Section(parent=section_key(path), path=path, parent_path=parent_path, rank=old.rank, name=name, title=title, keywords=keywords, description=description, theme=theme, is_private=is_private, is_default=is_default, redirect_to=redirect_to, new_window=new_window)
        old.delete()
        new.put()
        cache.delete(CACHE_KEY_HIERARCHY)
        return new
    elif old.parent_path != parent_path:

        # Rerank old's siblings to account for its removal by pushing it to the end of the old sibling list
        update_section_rank(old, len(get_siblings(old.path)))

        # Make it the last of its new siblings
        max_rank = 0
        for item, _ in get_children(parent_path):
            if item['rank'] <= max_rank: max_rank = item['rank'] + 1
        old.rank = max_rank

    old.parent_path = parent_path
    old.name = name
    old.title = title
    old.keywords = keywords
    old.description = description
    old.theme = theme
    old.is_private = is_private
    old.is_default = is_default
    old.redirect_to = redirect_to
    old.new_window = new_window
    old.put()
    cache.delete(CACHE_KEY_HIERARCHY)
    return old

def update_section_rank(section, new_rank):
    larger, smaller = max(section.rank, new_rank), min(section.rank, new_rank)
    for sibling in Section.gql("WHERE parent_path=:1 AND rank>=:2 AND rank<=:3 ORDER BY rank", section.parent_path, smaller, larger):
        if sibling.rank < section.rank:
            sibling.rank += 1
        elif sibling.rank > section.rank:
            sibling.rank -= 1
        else:
            sibling.rank = new_rank
        sibling.put()
    cache.delete(CACHE_KEY_HIERARCHY)

def delete_section(section):
    if section.is_default:
        raise Exception('Cannot delete default page without appointing another page first')
    elif get_children(section.path):
        raise Exception('Cannot delete a page with children without reparenting them first')
    content.delete_section_path_content(section.path)
    cache.delete(CACHE_KEY_HIERARCHY)
    section.delete()

def rename_theme_namespace_template(old, new):
    for s in Section.gql("WHERE theme=:1", old):
        s.theme = new
        s.put()
    cache.delete(CACHE_KEY_HIERARCHY)

def section_key(path):
    return db.Key.from_path('Section', path)