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
import datetime

from google.appengine.ext import db

from framework.subsystems import permission
from framework.subsystems import template
from framework.subsystems import cache

CACHE_KEY_PREPEND = 'CONTENT_'

SCOPE_GLOBAL = 'GLOBAL'
SCOPE_LOCAL = 'LOCAL'

class Content(db.Model):

    section_path = db.StringProperty(default=None) # None means GLOBAL
    namespace = db.StringProperty()
    container_namespace = db.StringProperty(default=None)

    name = 'Base Content'
    author = 'Imran Somji'

    actions = [] # Format: [[action_id, action_string, display_in_outer, permit_by_default], ...]
    views = [] # Format: [[view_id, view_string, display_in_outer], ...]

    def __unicode__(self):
        return getattr(self, 'action_%s' % self.section.path_action)()

    def init(self, section):
        self.section = section
        return self

    def get_manage_links(self, view, container_namespace=None, rank=None, total_ranks=None):
        allowed = []
        for action in self.actions:
            if action[2] and permission.perform_action(self, self.section.path, action[0]):
                allowed.append(action)
        if permission.is_admin(self.section.path) and container_namespace:
            pass
        elif len(allowed) == 0:
            return ''
        for v in self.views:
            if v[0] == view:
                view = v[1]
                break
        params = {
                  'content': self,
                  'view': view,
                  'can_manage': permission.is_admin(self.section.path),
                  'container_namespace': container_namespace,
                  'rank': rank,
                  'total_ranks': total_ranks,
                  'allowed_actions': allowed,
                  }
        return template.snippet('content-permissions', params)

    def update(self):
        cache.delete(CACHE_KEY_PREPEND + str(content_key(self.__class__.__name__, self.section_path, self.namespace)))
        return self.put()

    def on_remove(self):
        '''
        Subclasses should overwrite this to perform any cleanup required before removing
        '''
        pass

    def remove(self):
        '''
        Calling this method makes sure cache is cleaned up as well as any subclass level cleanup before deleting
        '''
        cache.delete(CACHE_KEY_PREPEND + str(content_key(self.__class__.__name__, self.section_path, self.namespace)))
        self.on_remove()
        self.delete()

    def clone(self, **extra_args):
        '''
        Adapted from: http://stackoverflow.com/a/2712401
        '''
        klass = self.__class__
        props = dict((k, v.__get__(self, klass)) for k, v in klass.properties().iteritems())
        props.update(extra_args)
        return klass(**props)

    def unique_identifier(self):
        return 'gae-cms-' + self.section.path + '-' + self.__class__.__name__.lower() + (('-' + self.container_namespace if self.container_namespace else '')) + '-' + self.namespace + '-' + str(datetime.datetime.now().microsecond)

    def view(self, view, params=None, container_namespace=None, rank=None, total_ranks=None):
        if not permission.view_content(self, self.section, view):
            raise Exception('You do not have permission to view this content')
        view_str = getattr(self, 'view_' + view)(params).strip()
        return self.get_manage_links(view, container_namespace, rank, total_ranks) + view_str

def get_else_create(section_path, content_type, namespace, container_namespace=None):
    item = get(content_type, section_path, namespace)
    if not item:
        m = __import__('framework.content.' + content_type.lower(), globals(), locals(), [str(content_type.lower())])
        concrete = getattr(m, content_type)
        item = concrete(parent=content_key(content_type, section_path, namespace),
                        section_path=section_path,
                        namespace=namespace,
                        container_namespace=container_namespace,
                        )
        item.put()
    return item

def get(content_type, section_path, namespace):
    item = cache.get(CACHE_KEY_PREPEND + str(content_key(content_type, section_path, namespace)))
    if item: return item
    m = __import__('framework.content.' + content_type.lower(), globals(), locals(), [str(content_type.lower())])
    concrete = getattr(m, content_type)
    try:
        item = concrete.gql("WHERE ANCESTOR IS :1 LIMIT 1", content_key(content_type, section_path, namespace))[0]
        cache.set(CACHE_KEY_PREPEND + str(content_key(content_type, section_path, namespace)), item)
        return item
    except:
        return None

def get_local_else_global(section_path, namespace):
    for content_type in get_all_content_types():
        item = cache.get(CACHE_KEY_PREPEND + str(content_key(content_type, section_path, namespace)))
        if item: return item
        item = cache.get(CACHE_KEY_PREPEND + str(content_key(content_type, None, namespace)))
        if item: return item
    for content_type in get_all_content_types():
        m = __import__('framework.content.' + content_type.lower(), globals(), locals(), [str(content_type.lower())])
        concrete = getattr(m, content_type)
        try:
            item = concrete.gql("WHERE section_path IN :1 AND namespace=:2 LIMIT 1", [section_path, None], namespace)[0]
            cache.set(CACHE_KEY_PREPEND + str(content_key(content_type, item.section_path, namespace)), item)
            return item
        except:
            pass
    return None

def get_by_namespace(namespace):
    for content_type in get_all_content_types():
        m = __import__('framework.content.' + content_type.lower(), globals(), locals(), [str(content_type.lower())])
        concrete = getattr(m, content_type)
        try:
            return concrete.gql("WHERE namespace=:1 LIMIT 1", namespace)[0]
        except:
            pass
    return None

def get_all_content_types():
    content_types = []
    for name in os.listdir('framework/content'):
        if os.path.isdir('framework/content/' + name) and os.path.isfile('framework/content/' + name + '/__init__.py'):
            # Convert something_like_this into SomethingLikeThis
            CapWordsName = ''.join(j.title() for j in name.split('_'))
            content_types.append(CapWordsName)
    return content_types

def rename_section_paths(old, new):
    for content_type in get_all_content_types():
        m = __import__('framework.content.' + content_type.lower(), globals(), locals(), [str(content_type.lower())])
        concrete = getattr(m, content_type)
        items = concrete.gql("WHERE section_path=:1", old)
        for i in items:
            # Have to remove and reenter content since the key will change
            n = i.clone(parent=content_key(content_type, new, i.namespace), section_path=new)
            i.delete()
            n.put()

        if content_type == 'Container':
            # The following line is pretty inefficient but then so is doing "WHERE old path IN content_paths" and I believe we avoid subquery limitations
            items = concrete.gql("")
            for i in items:
                if old in i.content_paths:
                    i.content_paths = [new if x == old else x for x in i.content_paths]
                    i.update()

def delete_section_path_content(path):
    for content_type in get_all_content_types():
        m = __import__('framework.content.' + content_type.lower(), globals(), locals(), [str(content_type.lower())])
        concrete = getattr(m, content_type)
        items = concrete.gql("WHERE section_path=:1", path)
        for i in items: i.remove()

def content_key(content_type, section_path, namespace):
    return db.Key.from_path(content_type, ((section_path + '.') if section_path else '') + namespace)