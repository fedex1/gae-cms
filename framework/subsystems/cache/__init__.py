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

from google.appengine.api import memcache

"""
We wrap memcache to ensure new keys on each deployment
"""

def get(key):
    return memcache.Client().get(os.environ['CURRENT_VERSION_ID'] + '_' + key)

def set(key, val):
    return memcache.Client().set(os.environ['CURRENT_VERSION_ID'] + '_' + key, val)

def delete(key):
    return memcache.Client().delete(os.environ['CURRENT_VERSION_ID'] + '_' + key)

def flush_all():
    return memcache.Client().flush_all()