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

def unique_list(seq, idfun=None):
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

'''
Adapted from: http://mobiforge.com/developing/story/build-a-mobile-and-desktop-friendly-application-django-15-minutes
'''

mobile_uas = [
    'w3c ','acs-','alav','alca','amoi','audi','avan','benq','bird','blac',
    'blaz','brew','cell','cldc','cmd-','dang','doco','eric','hipt','inno',
    'ipaq','java','jigs','kddi','keji','leno','lg-c','lg-d','lg-g','lge-',
    'maui','maxo','midp','mits','mmef','mobi','mot-','moto','mwbp','nec-',
    'newt','noki','palm','pana','pant','phil','play','port','prox',
    'qwap','sage','sams','sany','sch-','sec-','send','seri','sgh-','shar',
    'sie-','siem','smal','smar','sony','sph-','symb','t-mo','teli','tim-',
    'tosh','tsm-','upg1','upsi','vk-v','voda','wap-','wapa','wapi','wapp',
    'wapr','webc','winw','winw','xda','xda-'
    ]

mobile_ua_hints = [ 'SymbianOS', 'Opera Mobi', 'iPhone', 'Mobile' ]

def mobile_ua(section):
    try:
        ua = section.handler.request.user_agent.lower()[0:4]
    except:
        return None

    if (ua in mobile_uas):
        return ua
    else:
        for hint in mobile_ua_hints:
            if section.handler.request.user_agent.find(hint) > 0:
                return hint
    return None

def file_search(search, root='.'):
    files = []
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename in search:
                files.append(os.path.join(dirpath, filename))
    ret = []
    for s in search: # Reorder
        for f in files:
            if f.endswith(os.path.sep + s): ret.append(f)
    return ret

def dir_search(search, root='.'):
    directories = []
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')] # Remove hidden directories
        for dirname in dirnames:
            if dirname in search:
                directories.append(os.path.join(dirpath, dirname))
    ret = []
    for s in search: # Reorder
        for d in directories:
            if d.endswith(os.path.sep + s): ret.append(d)
    return ret