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
GNU General Public License for more detailsection.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import os

from google.appengine.api import users

from framework.subsystems import permission
from framework.subsystems.theme import DEFAULT_LOCAL_THEME_TEMPLATE, is_local_theme_template, get_custom_template
from framework.subsystems import utils

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.template.loaders.filesystem import Loader
from django.template.loader import render_to_string
from django.template import Template, Context, TemplateDoesNotExist

def html(section, main=''):
    params = {
        'VERSION': os.environ['CURRENT_VERSION_ID'],
        'user': users.get_current_user(),
        'section': section,
        'main': main,
    }

    theme_namespace_template = section.get_theme_namespace_template()

    try:
        if is_local_theme_template(theme_namespace_template):
            template_content = open('./themes/' + theme_namespace_template.replace('/', '/templates/', 1) + '.body', 'r').read()
        else:
            template_content = get_custom_template(theme_namespace_template)
    except TemplateDoesNotExist:
        theme_namespace_template = DEFAULT_LOCAL_THEME_TEMPLATE
        template_content = open('./themes/' + DEFAULT_LOCAL_THEME_TEMPLATE.replace('/', '/templates/', 1) + '.body', 'r').read()

    theme_namespace, _ = theme_namespace_template.split('/')

    body = Template('{% load filters %}' + template_content).render(Context(params)).strip()

    menubar = snippet('user-menubar', {'section': section, 'user': users.get_current_user()})

    html = render_to_string('outer.html', params).replace('<body></body>',
                                                          '<body class="%s">%s%s</body>' % (' '.join(section.classes), body, menubar),
                                                          1)

    section.yuicss, section.css, section.themecss, section.yuijs, section.js, section.localthemejs = (utils.unique_list(x) for x in [section.yuicss, section.css, section.themecss, section.yuijs, section.js, section.localthemejs])

    section.yuicss = '__'.join([x[:-4] if x.endswith('.css') else x for x in section.yuicss]).replace('/', '_')
    section.css = '_'.join([x[:-4] if x.endswith('.css') else x for x in section.css]).replace('/', '_')
    section.themecss = '_'.join([x[:-4] if x.endswith('.css') else x for x in section.themecss]).replace('/', '_')
    section.yuijs = '__'.join([x[:-3] if x.endswith('.js') else x for x in section.yuijs]).replace('/', '_')
    section.js = '_'.join([x[:-3] if x.endswith('.js') else x for x in section.js]).replace('/', '_')
    section.localthemejs = '_'.join([x[:-3] if x.endswith('.js') else x for x in section.localthemejs]).replace('/', '_')

    if section.yuicss: section.yuicss = '___yui___' + section.yuicss
    if section.css: section.css = '___local___' + section.css
    if section.themecss: section.themecss = '___theme___' + theme_namespace + '___' + section.themecss

    if section.yuijs: section.yuijs = '___yui___' + section.yuijs
    if section.js: section.js = '___local___' + section.js
    if section.localthemejs: section.localthemejs = '___theme___' + theme_namespace + '___' + section.localthemejs

    viewport = '<meta name="viewport" content="' + section.viewport_content + '">' if section.viewport_content else ''
    linkrel = '<link rel="stylesheet" type="text/css" href="/' + section.yuicss + section.css + section.themecss + '.css">' if section.yuicss or section.css or section.themecss else ''
    script = snippet('defer-js-load', {'js_file': '/' + section.yuijs + section.js + section.localthemejs + '.js'}) if section.yuijs or section.js or section.localthemejs else ''
    analytics = snippet('analytics', {'GOOGLE_ANALYTICS_UA': section.configuration['GOOGLE_ANALYTICS_UA']}) if section.configuration['GOOGLE_ANALYTICS_UA'] else ''

    header_includes = viewport + linkrel + script.replace('\t', '').replace('\n', '') + analytics.replace('\t', '').replace('\n', '')

    if header_includes:
        html = html.replace('</head>', '\t' + header_includes + '\n\t</head>', 1)

    return html.strip()

def get(content):
    '''
    Only necessary so that the DJANGO_SETTINGS_MODULE environment gets initialized
    '''
    return str(snippet('plain', {'content': content}))

def snippet(filename, params=None):
    return render_to_string(filename + '.snip', params).strip()