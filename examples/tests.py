# -*- coding: utf-8 -*-
# 
# django-ldapdb
# Copyright (C) 2009-2010 Bolloré telecom
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

from django.test import TestCase

from ldapdb import connection
from examples.models import LdapUser, LdapGroup

class BaseTestCase(TestCase):
    def setUp(self):
        cursor = connection._cursor()
        for base in [LdapGroup.base_dn, LdapUser.base_dn]:
            ou = base.split(',')[0].split('=')[1]
            attrs = [('objectClass', ['top', 'organizationalUnit']), ('ou', [ou])]
            try:
                cursor.connection.add_s(base, attrs)
            except ldap.ALREADY_EXISTS:
                pass

    def tearDown(self):
        cursor = connection._cursor()
        for base in [LdapGroup.base_dn, LdapUser.base_dn]:
            results = cursor.connection.search_s(base, ldap.SCOPE_SUBTREE)
            for dn, attrs in reversed(results):
                cursor.connection.delete_s(dn)

class GroupTestCase(BaseTestCase):
    def test_create(self):
        g = LdapGroup()
        g.name = "foogroup"
        g.gid = 1000
        g.usernames = ['foouser', 'baruser']
        g.save()

    def test_get(self):
        self.test_create()

        g = LdapGroup.objects.get(name='foogroup')
        self.assertEquals(g.name, 'foogroup')
        self.assertEquals(g.gid, 1000)
        self.assertEquals(g.usernames, ['foouser', 'baruser'])
 
class UserTestCase(BaseTestCase):
    def test_create(self):
        u = LdapUser()
        u.first_name = "Foo"
        u.last_name = "User"
        u.full_name = "Foo User"

        u.group = 1000
        u.home_directory = "/home/foouser"
        u.uid = 1000
        u.username = "foouser"
        u.save()

    def test_get(self):
        self.test_create()

        u = LdapUser.objects.get(username='foouser')
        self.assertEquals(u.first_name, 'Foo') 
        self.assertEquals(u.last_name, 'User') 
        self.assertEquals(u.full_name, 'Foo User')
 
        self.assertEquals(u.group, 1000)
        self.assertEquals(u.home_directory, '/home/foouser')
        self.assertEquals(u.uid, 1000)
        self.assertEquals(u.username, 'foouser')

