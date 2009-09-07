# -*- coding: utf-8 -*-
# 
# django-ldapdb
# Copyright (C) 2009 Bolloré telecom
# See AUTHORS file for a full list of contributors.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import ldap

from django.conf import settings

def convert(field, value, func):
    if not value or field == 'jpegPhoto':
        return value
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, list):
        return [ func(x) for x in value ]
    else:
        return func(value)
        
class LdapConnection(object):
    def __init__(self, server, bind_dn, bind_password):
        self.connection = ldap.initialize(server)
        self.connection.simple_bind_s(bind_dn, bind_password)
        self.charset = "utf-8"

    def add_s(self, dn, modlist):
        mods = []
        for field, value in modlist:
            converted = convert(field, value, lambda x: x.encode(self.charset))
            if isinstance(converted, list):
                mods.append((field, converted))
            else:
                mods.append((field, [converted]))
        return self.connection.add_s(dn.encode(self.charset), mods)

    def delete_s(self, dn):
        return self.connection.delete_s(dn.encode(self.charset))

    def modify_s(self, dn, modlist):
        mods = []
        for op, field, value in modlist:
            mods.append((op, field, convert(field, value, lambda x: x.encode(self.charset))))
        return self.connection.modify_s(dn.encode(self.charset), mods)

    def rename_s(self, dn, newrdn):
        return self.connection.rename_s(dn.encode(self.charset), newrdn.encode(self.charset))

    def search_s(self, base, scope, filterstr, attrlist):
        results = self.connection.search_s(base, scope, filterstr.encode(self.charset), attrlist)
        output = []
        for dn, attrs in results:
            for field in attrs:
                if field == "member" or field == "memberUid":
                    attrs[field] = convert(field, attrs[field], lambda x: x.decode(self.charset))
                else:
                    attrs[field] = convert(field, attrs[field][0], lambda x: x.decode(self.charset))
            output.append((dn.decode(self.charset), attrs))
        return output

# FIXME: is this the right place to initialize the LDAP connection?
connection = LdapConnection(settings.LDAPDB_SERVER_URI,
    settings.LDAPDB_BIND_DN,
    settings.LDAPDB_BIND_PASSWORD)

