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

import random

from google.appengine.ext import db

from django.utils.html import strip_tags

from framework import content
from framework.subsystems import template
from framework.subsystems.forms import form, control, selectcontrol, textareacontrol

class Text(content.Content):

    titles = db.StringListProperty()
    bodies = db.ListProperty(item_type=db.Text)

    name = 'Text'
    author = 'Imran Somji'

    actions = [
        ['add', 'Add', False, False],
        ['edit', 'Edit', True, False],
        ['reorder', 'Reorder', False, False],
        ['delete', 'Delete', False, False],
    ]
    views = [
        ['default', 'Default - Multiple items in tabs', True],
        ['random', 'Random', True],
    ]

    def action_add(self):
        rank = int(self.section.path_params[0]) if self.section.path_params else 0
        if rank > len(self.titles) or rank < 0:
            raise Exception('BadRequest', 'Text item out of range')
        elif self.section.handler.request.get('submit'):
            self.titles.insert(rank, self.section.handler.request.get('title'))
            self.bodies.insert(rank, db.Text(self.section.handler.request.get('body')))
            self.update()
            raise Exception('Redirect', self.section.action_redirect_path)
        return '<h2>Add text</h2>' + get_form(self.section, '', '')

    def action_edit(self):
        if not self.titles: return self.action_add()
        rank = int(self.section.path_params[0]) if self.section.path_params else 0
        if rank > len(self.titles) - 1 or rank < 0:
            raise Exception('BadRequest', 'Text item out of range')
        elif self.section.handler.request.get('submit'):
            self.titles[rank] = self.section.handler.request.get('title')
            self.bodies[rank] = db.Text(self.section.handler.request.get('body'))
            self.update()
            raise Exception('Redirect', self.section.action_redirect_path)
        elif not self.section.path_params and self.titles:
            self.items = []
            for i in range(len(self.titles)):
                self.items.append([self.titles[i], self.bodies[i]])
            return template.snippet('text-edit-multiple', { 'content': self })
        return '<h2>Edit text</h2>' + get_form(self.section, self.titles[rank], self.bodies[rank])

    def action_reorder(self):
        rank = int(self.section.path_params[0]) if self.section.path_params else 0
        if rank > len(self.titles) - 1 or rank < 0:
            raise Exception('BadRequest', 'Text item out of range')
        if self.section.handler.request.get('submit'):
            new_rank = int(self.section.handler.request.get('new_rank'))
            if new_rank > len(self.titles) - 1 or rank < 0:
                raise Exception('BadRequest', 'Reorder rank out of range')
            self.titles.insert(new_rank, self.titles.pop(rank))
            self.bodies.insert(new_rank, self.bodies.pop(rank))
            self.update()
            raise Exception('Redirect', self.section.action_redirect_path)
        f = form(self.section, self.section.full_path)
        ranks = []
        for i in range(len(self.titles)):
            ranks.append([i, i])
        f.add_control(selectcontrol(self.section, 'new_rank', ranks, rank, 'Rank'))
        f.add_control(control(self.section, 'submit', 'submit', 'Submit'))
        return '<h2>Reorder text</h2>' + unicode(f)

    def action_delete(self):
        rank = int(self.section.path_params[0]) if self.section.path_params else 0
        if rank > len(self.titles) - 1 or rank < 0:
            raise Exception('BadRequest', 'Text item out of range')
        if self.section.handler.request.get('submit'):
            self.titles.pop(rank)
            self.bodies.pop(rank)
            self.update()
            raise Exception('Redirect', self.section.action_redirect_path)
        f = form(self.section, self.section.full_path)
        f.add_control(control(self.section, 'submit', 'submit', 'Confirm'))
        return '<div class="status warning">Are you sure you wish to delete item %d?</div>%s' % (rank + 1, unicode(f))

    def view_default(self, params):
        self.items = []
        for i in range(len(self.titles)):
            self.items.append([self.titles[i], self.bodies[i]])
        return template.snippet('text-default', { 'content': self }) if self.items else ''

    def view_random(self, params):
        if not self.titles: return ''
        i = random.randint(0, len(self.titles) - 1)
        ret = '<h2>%s</h2>' % self.titles[i] if self.titles[i] else ''
        ret += self.bodies[i]
        return '<div class="content text single random">%s</div>' % ret

def get_form(section, title, body):
    f = form(section, section.full_path)
    f.add_control(control(section, 'text', 'title', title, 'Title', 60))
    f.add_control(textareacontrol(section, 'body', body, 'Body', 100, 10, html=True))
    f.add_control(control(section, 'submit', 'submit'))
    return unicode(f)