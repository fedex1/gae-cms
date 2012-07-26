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

from django.template import Library
from django import template

from framework import content
from framework.subsystems import configuration
from framework.subsystems.section import MAIN_CONTAINER_NAMESPACE

register = Library()

@register.filter
def view(section, param_string):
    params = [x.strip() for x in param_string.split(',')]
    try:
        try:
            scope, namespace, content_type, view = params[0:4]
        except:
            raise Exception('A minimum of four parameters required')
        else:
            params = params[4:] if len(params) > 4 else None

        if scope not in [content.SCOPE_GLOBAL, content.SCOPE_LOCAL]:
            raise Exception('Scope must be one of: ' + str([content.SCOPE_GLOBAL, content.SCOPE_LOCAL]))
        elif ' ' in namespace:
            raise Exception('Invalid character " " for namespace')
        elif namespace == MAIN_CONTAINER_NAMESPACE:
            raise Exception('"%s" is a reserved namespace' % MAIN_CONTAINER_NAMESPACE)
        item = content.get_local_else_global(section.path, namespace)
        if item and item.__class__.__name__ != content_type:
            raise Exception('Selected namespace already exists for a different type of content')
        elif not item:
            item = content.get_else_create(section.path if scope == content.SCOPE_LOCAL else None, content_type, namespace)
        return item.init(section).view(view, params)
    except Exception as inst:
        error = unicode(inst) + ('<div class="traceback">' + traceback.format_exc().replace('\n', '<br><br>') + '</div>') if configuration.debug_mode() else ''
        return '<div class="status error">Error: View "%s" does not exist: %s</div>' % (view, error)

@register.filter
def joinby(value, arg):
    return arg.join(value)

@register.filter
def bodyclass(section, args):
    [section.classes.append(x.strip('/ ')) for x in args.split(',')]
    return ''

@register.filter
def yuicss(section, args):
    [section.yuicss.append(x.strip('/ ')) for x in args.split(',')]
    return ''

@register.filter
def css(section, args):
    [section.css.append(x.strip('/ ')) for x in args.split(',')]
    return ''

@register.filter
def themecss(section, args):
    [section.themecss.append(x.strip('/ ')) for x in args.split(',')]
    return ''

@register.filter
def yuijs(section, args):
    [section.yuijs.append(x.strip('/ ')) for x in args.split(',')]
    return ''

@register.filter
def js(section, args):
    [section.js.append(x.strip('/ ')) for x in args.split(',')]
    return ''

@register.filter
def localthemejs(section, args):
    [section.js.append(x.strip('/ ')) for x in args.split(',')]
    return ''

@register.filter
def viewport_content(section, args):
    section.viewport_content = args.strip()
    return ''

@register.tag(name='captureas')
def do_captureas(parser, token):
    try:
        _, args = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("'captureas' node requires a variable name.")
    nodelist = parser.parse(('endcaptureas',))
    parser.delete_first_token()
    return CaptureasNode(nodelist, args)

class CaptureasNode(template.Node):
    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        output = self.nodelist.render(context)
        context[self.varname] = output
        return ''