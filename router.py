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

import traceback
import webapp2
from datetime import datetime, timedelta

from framework.subsystems import section
from framework.subsystems import template
from framework.subsystems import configuration

class Router(webapp2.RequestHandler):
    def get(self, path):
        try:
            if path == '/robots.txt':
                return webapp2.Response(template.get(configuration.get_robots_txt()))
            elif path == '/favicon.ico':
                return webapp2.Response(configuration.get_favicon_ico())
            else:
                response = webapp2.Response(unicode(section.get_section(self, path)))
                response.headers['Connection'] = 'Keep-Alive'
                return response
        except Exception as inst:
            if inst[0] == 'Redirect':
                return self.redirect(str(inst[1]))
            elif inst[0] == 'SendFileBlob':
                response = webapp2.Response(inst[1].data)
                if inst[1].content_type: response.content_type = str(inst[1].content_type)
                response.headers['Connection'] = 'Keep-Alive'
                response.headers['Date'] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
                last_modified = datetime.utcnow() # TODO: Store when this actually happened
                response.headers['Last-Modified'] = last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
                response.headers['Expires'] = (last_modified + timedelta(8)).strftime("%a, %d %b %Y %H:%M:%S GMT")
                response.cache_control.no_cache = None
                response.cache_control.public = True
                response.cache_control.max_age = 604800000 # One week
                return response
            elif inst[0] == 'NotFound':
                err = 404
                main = 'Page not found'
            elif inst[0] == 'BadRequest':
                err = 400
                main = 'Bad Request'
            elif inst[0] == 'Forbidden':
                err = 403
                main = 'Forbidden'
            elif inst[0] == 'AccessDenied':
                err = 403
                main = 'Access Denied'
            elif configuration.debug_mode():
                err = 400
                main = 'RouterError: ' + unicode(inst) + '<div class="traceback">' + traceback.format_exc().replace('\n', '<br><br>') + '</div>'
            else:
                err = 400
                main = 'An error has occurred.'
            default_section = section.get_section(None, '')
            response = webapp2.Response(unicode(template.html(default_section, '<div class="status error">' + main + '</div>')))
            response.set_status(err)
            return response

    def post(self, path):
        return self.get(path)

app = webapp2.WSGIApplication([('(/.*)', Router)], debug=configuration.debug_mode())