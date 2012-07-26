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

import webapp2, os, traceback
from datetime import datetime, timedelta

from google.appengine.api import urlfetch

from framework.subsystems import cache
from framework.subsystems import configuration
from framework.subsystems import section
from framework.subsystems import template
from framework.subsystems.theme import is_local_theme_namespace, get_custom_theme
from framework.subsystems import utils
from framework.subsystems.utils.cssmin import cssmin

NAMESPACE_REPLACER = '/*___namespace___*/'
CACHE_LAST_MODIFIED_PREPEND = 'LAST_MODIFIED_'

class Compressor(webapp2.RequestHandler):
    def get(self, path):     
        try:
            path = path.strip('/')
            path, extension = os.path.splitext(path)

            contents = cache.get(path + extension)
            last_modified = cache.get(CACHE_LAST_MODIFIED_PREPEND + path + extension)

            if not contents:
                contents = ''

                ''' YUI '''
                yui_parts = '' if path.find('___yui___') < 0 else path[path.find('___yui___'):].replace('___yui___', '', 1)
                yui_parts = yui_parts if yui_parts.find('___') < 0 else yui_parts[:yui_parts.find('___')]
                rest_parts = path.replace('___yui___', '', 1).replace(yui_parts, '', 1).replace('___local___', '', 1)
                if '___theme___' in rest_parts:
                    local_parts, theme_parts = rest_parts.split('___theme___')
                else:
                    local_parts, theme_parts = rest_parts, None
                if yui_parts:
                    yui_version = '3.5.0/build/'
                    yui_absolute = 'http://yui.yahooapis.com/combo?'
                    yui_parts = yui_parts.split('__')
                    yui_parts = [(yui_version + x.replace('_', '/') + '-min' + extension) for x in yui_parts]
                    result = urlfetch.fetch(yui_absolute + '&'.join(yui_parts))
                    if result.status_code == 200:
                        contents += result.content
                    else:
                        raise Exception('NotFound')

                ''' Local '''
                filenames = [(x + extension) for x in local_parts.split('_')]
                if len(filenames) != len(utils.unique_list(filenames)):
                    raise Exception('NotFound')
                files = utils.file_search(filenames)
                if extension == '.css':
                    contents += (''.join([parse_content(open(f, 'r').read(), True) for f in files]))
                else:
                    contents += (''.join([parse_content(open(f, 'r').read()) for f in files]))

                ''' Theme '''
                if theme_parts:
                    theme_namespace, theme_parts = theme_parts.split('___')
                    filenames = [(x + extension) for x in theme_parts.split('_')]
                    if len(filenames) != len(utils.unique_list(filenames)):
                        raise Exception('NotFound')
                    elif is_local_theme_namespace(theme_namespace):
                        if extension == '.css':
                            contents += (''.join([parse_content(open('./themes/' + theme_namespace + '/' + extension.strip('.') + '/' + f, 'r').read(), True, theme_namespace) for f in filenames]))
                        else:
                            contents += (''.join([parse_content(open('./themes/' + theme_namespace + '/' + extension.strip('.') + '/' + f, 'r').read(), False, theme_namespace) for f in filenames]))
                    else:
                        t = get_custom_theme(theme_namespace)
                        for f in filenames:
                            if extension == '.css':
                                index = t.css_filenames.index(f)
                                contents += parse_content(t.css_contents[index], True, theme_namespace)
                            elif extension == '.js':
                                index = t.js_filenames.index(f)
                                contents += parse_content(t.js_contents[index], False, theme_namespace)

                cache.set(path + extension, contents)
                last_modified = datetime.utcnow()
                cache.set(CACHE_LAST_MODIFIED_PREPEND + path + extension, last_modified)

            if not contents.strip(): raise Exception('NotFound')

            if not last_modified:
                last_modified = datetime.utcnow()
                cache.set(CACHE_LAST_MODIFIED_PREPEND + path + extension, last_modified)

            content_type = 'application/javascript' if extension == '.js' else 'text/css'
            response = webapp2.Response(template.get(contents.strip()), content_type=content_type)
            response.headers['Connection'] = 'Keep-Alive'
            response.headers['Date'] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            response.headers['Last-Modified'] = last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
            response.headers['Expires'] = (last_modified + timedelta(8)).strftime("%a, %d %b %Y %H:%M:%S GMT")
            response.cache_control.no_cache = None
            response.cache_control.public = True
            response.cache_control.max_age = 604800000 # One week
            return response
        except Exception as inst:
            message = ''
            if configuration.debug_mode():
                message = '<div class="status error">' + unicode(inst) + '<br><br>' + traceback.format_exc().replace('\n', '<br><br>') + '</div>'
            response = webapp2.Response(template.get('<html><head><title>404 Not Found</title></head><body><h1>404 Not Found</h1>Document or file requested by the client was not found.%s</body></html>' % message))
            response.set_status(404)
            return response

    def post(self, path):
        return self.get(path)

def parse_content(content, css_minify=False, namespace=None):
    default_section = section.get_section(None, '')
    if namespace: content = content.replace(NAMESPACE_REPLACER, '/%s/themes/get/%s/' % (default_section.path, namespace.replace(' ', '%20')))
    content = (content if not css_minify else cssmin(content)).strip()
    return content

app = webapp2.WSGIApplication([('(/.*)', Compressor)])