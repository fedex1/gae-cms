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

import os, importlib

from google.appengine.ext import db

from framework import content
from framework.subsystems import cache
from framework.subsystems import permission
from framework.subsystems.forms import form, control, selectcontrol

class Container(content.Content):

    content_types = db.StringListProperty()
    content_paths = db.StringListProperty()
    content_namespaces = db.StringListProperty()
    content_views = db.StringListProperty()

    name = 'Container'
    author = 'Imran Somji'

    actions = [
        ['add', 'Add content', False, False],
        ['reorder', 'Reorder', False, False],
        ['delete', 'Delete', False, False],
    ]
    views = [
        ['default', 'Default', False],
    ]

    def action_add(self):
        ret = '<h2>Add content</h2>'
        content_view = self.section.handler.request.get('content_view') if self.section.handler.request.get('content_view') else ''
        namespace = self.section.handler.request.get('namespace').replace('/', '-').replace(' ', '-').replace('.', '-').lower() if self.section.handler.request.get('namespace') else ''
        if namespace:
            existing_content = content.get_by_namespace(namespace)
            existing_content_type = existing_content.__class__.__name__ if existing_content else None
            # TODO: Ensure that the below actually exist
            rank = int(self.section.path_params[0])
            content_type, view = content_view.split('.')
        if self.section.handler.request.get('submit') and not content_view:
            ret += '<div class="status error">Content is required</div>'
        elif self.section.handler.request.get('submit') and not namespace:
            ret += '<div class="status error">Namespace is required</div>'
        elif self.section.handler.request.get('submit') and existing_content_type:
            if existing_content_type != content_type:
                ret += '<div class="status error">Selected namespace already exists for a different type of content</div>'
            else:
                if existing_content.section_path and not permission.is_admin(existing_content.section_path):
                    ret += '<div class="status error">Selected namespace already exists for content that you are not permitted to manage</div>'
                elif self.section.handler.request.get('confirm'):
                    self.content_types.insert(rank, existing_content.__class__.__name__)
                    self.content_paths.insert(rank, existing_content.section_path if existing_content.section_path else '')
                    self.content_namespaces.insert(rank, namespace)
                    self.content_views.insert(rank, view)
                    self.update()
                    ret += str(existing_content)
                    raise Exception('Redirect', self.section.action_redirect_path)
                else:
                    ret += '<div class="status progress">Selected namespace already exists, continue to add a view to this existing content</div>'
                    f = form(self.section, self.section.full_path)
                    f.add_control(control(self.section, 'hidden', 'content_view', content_view))
                    f.add_control(control(self.section, 'hidden', 'namespace', namespace))
                    f.add_control(control(self.section, 'hidden', 'confirm', '1'))
                    f.add_control(control(self.section, 'submit', 'submit', 'Confirm'))
                    ret += unicode(f)
                    return ret
        elif self.section.handler.request.get('submit'):
            content.get_else_create(self.section.path, content_type, namespace, self.namespace)
            self.content_types.insert(rank, content_type)
            self.content_paths.insert(rank, self.section_path if self.section_path else '')
            self.content_namespaces.insert(rank, namespace)
            self.content_views.insert(rank, view)
            self.update()
            raise Exception('Redirect', self.section.action_redirect_path)
        content_views = [['', '']]
        for content_type in content.get_all_content_types():
            m = importlib.import_module('framework.content.' + content_type.lower())
            views = []
            for v in getattr(m, content_type.title())().views:
                if v[2]:
                    views.append([content_type + '.' + v[0], v[1]])
            if views:
                content_views.append([content_type, views])
        f = form(self.section, self.section.full_path)
        f.add_control(selectcontrol(self.section, 'content_view', content_views, content_view, 'Content type'))
        f.add_control(control(self.section, 'text', 'namespace', namespace, 'Namespace'))
        f.add_control(control(self.section, 'submit', 'submit', 'Submit'))
        ret += unicode(f)
        return ret

    def action_delete(self):
        rank = int(self.section.path_params[0])
        item = content.get(self.content_types[rank], self.content_paths[rank] if self.content_paths[rank] else None, self.content_namespaces[rank])
        is_original_content = item and item.container_namespace == self.namespace and item.section_path == self.section_path and self.content_namespaces.count(item.namespace) == 1
        if item:
            item = item.init(self.section)
        if self.section.handler.request.get('submit'):
            if is_original_content:
                item.remove()
            self.content_types.pop(rank)
            self.content_paths.pop(rank)
            self.content_namespaces.pop(rank)
            self.content_views.pop(rank)
            self.update()
            raise Exception('Redirect', self.section.action_redirect_path)
        if is_original_content:
            message = '<div class="status warning">Are you sure you wish to delete content "%s" and all associated data?</div>' % self.content_namespaces[rank]
        else:
            message = '<div class="status warning">Are you sure you wish to delete this view for content "%s"?</div>' % self.content_namespaces[rank]
        f = form(self.section, self.section.full_path)
        f.add_control(control(self.section, 'submit', 'submit', 'Confirm'))
        return '<h2>Delete content</h2>%s%s' % (message, unicode(f))

    def action_reorder(self):
        if not len(self.content_namespaces) > 1:
            raise Exception('BadRequest', 'Cannot reorder content without multiple content contained')
        rank = int(self.section.path_params[0])
        if self.section.handler.request.get('submit'):
            new_rank = int(self.section.handler.request.get('new_rank'))
            self.content_types.insert(new_rank, self.content_types.pop(rank))
            self.content_paths.insert(new_rank, self.content_paths.pop(rank))
            self.content_namespaces.insert(new_rank, self.content_namespaces.pop(rank))
            self.content_views.insert(new_rank, self.content_views.pop(rank))
            self.update()
            raise Exception('Redirect', self.section.action_redirect_path)
        f = form(self.section, self.section.full_path)
        ranks = []
        for i in range(len(self.content_namespaces)):
            ranks.append([i, i])
        f.add_control(selectcontrol(self.section, 'new_rank', ranks, rank, 'Rank'))
        f.add_control(control(self.section, 'submit', 'submit', 'Submit'))
        return '<h2>Reorder content</h2>%s' % unicode(f)

    def view_default(self, params):
        ret = ''
        add_action = self.actions[0]
        can_add = permission.perform_action(self, self.section.path, add_action[0])
        if can_add:
            self.section.css.append('container.css')
            add_link = '<a class="container add" href="/' + self.section.path + '/' + self.namespace + '/' + add_action[0] + '/%d">' + add_action[1] + '</a>'
        for i in range(len(self.content_namespaces)):
            if can_add: ret += add_link % i
            item = content.get(self.content_types[i], self.content_paths[i] if self.content_paths[i] else None, self.content_namespaces[i])
            if not item:
                ret += self.get_manage_links(self.content_views[i], self.namespace, i) + '<div class="status error">Content for this view was deleted</div>'
            else:
                ret += item.init(self.section).view(self.content_views[i], params=None, container_namespace=self.namespace, rank=i, total_ranks=len(self.content_namespaces))
        if can_add: ret += add_link % len(self.content_namespaces)
        return ret