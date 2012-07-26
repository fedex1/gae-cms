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

from google.appengine.ext import db

from framework import content
from framework.subsystems.file import File
from framework.subsystems import template
from framework.subsystems.forms import form, control
from framework.subsystems import cache

CACHE_KEY_PREPEND = 'FILE_'

class Files(content.Content):

    file_keys = db.StringListProperty()
    filenames = db.StringListProperty()

    name = 'Files'
    author = 'Imran Somji'

    actions = [
        ['add', 'Add', False, False],
        ['get', 'Get', False, True],
        ['delete', 'Delete', False, False],
        ['manage', 'Manage', False, False],
    ]
    views = [
        ['menu', 'File menu', False],
    ]

    def on_delete(self):
        for i in range(len(self.filenames)):
            # This can be done more efficiently via GQL
            data = self.get_file(self.filenames[i])
            cache.delete(CACHE_KEY_PREPEND + self.file_keys[i])
            data.delete()
            del self.file_keys[i]
            del self.filenames[i]
        self.update()

    def action_add(self):
        ret = '<h2>Add file</h2>'
        if self.section.handler.request.get('submit'):
            filename = self.section.handler.request.POST['data'].filename.replace(' ', '_')
            if not self.get_file(filename):
                content_type = self.section.handler.request.POST['data'].type
                data = db.Blob(self.section.handler.request.get('data'))
                key = File(filename=filename, data=data, content_type=content_type, section_path=self.section.path).put()
                self.file_keys.append(str(key))
                self.filenames.append(filename)
                self.update()
                raise Exception('Redirect', self.section.action_redirect_path)
            ret += '<div class="status error">A file with the same name already exists for this section</div>'
        f = form(self.section, self.section.full_path)
        f.add_control(control(self.section, 'file', 'data', label='Data'))
        f.add_control(control(self.section, 'submit', 'submit', 'Submit'))
        return ret + unicode(f)

    def action_get(self):
        if not self.section.path_params or len(self.section.path_params) != 1:
            raise Exception('NotFound')
        filename = self.section.path_params[0]
        data = self.get_file(filename)
        if not data:
            raise Exception('NotFound')
        raise Exception('SendFileBlob', data)

    def action_delete(self):
        if not self.section.path_params or len(self.section.path_params) != 1:
            raise Exception('NotFound')
        filename = self.section.path_params[0]
        if self.section.handler.request.get('submit'):
            data = self.get_file(filename)
            if not data:
                raise Exception('NotFound')
            index = self.filenames.index(filename)
            cache.delete(CACHE_KEY_PREPEND + self.file_keys[index])
            data.delete()
            del self.file_keys[index]
            del self.filenames[index]
            self.update()
            raise Exception('Redirect', self.section.action_redirect_path)
        f = form(self.section, self.section.full_path)
        f.add_control(control(self.section, 'submit', 'submit', 'Confirm'))
        return '<div class="status warning">Are you sure you wish to delete file "%s" from "%s"?</div>%s' % (filename, self.section.path, unicode(f))

    def action_manage(self):
        return template.snippet('files-manage', { 'content': self })

    def view_menu(self, params=None):
        return template.snippet('files-menu', { 'content': self })

    def get_file(self, filename):
        item = None
        try:
            key = self.file_keys[self.filenames.index(filename)]
            item = cache.get(CACHE_KEY_PREPEND + key)
            if not item:
                item = File.get(key)
                cache.set(CACHE_KEY_PREPEND + key, item)
        finally:
            return item