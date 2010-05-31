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
        u.photo = '\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xfe\x00\x1cCreated with GIMP on a Mac\xff\xdb\x00C\x00\x05\x03\x04\x04\x04\x03\x05\x04\x04\x04\x05\x05\x05\x06\x07\x0c\x08\x07\x07\x07\x07\x0f\x0b\x0b\t\x0c\x11\x0f\x12\x12\x11\x0f\x11\x11\x13\x16\x1c\x17\x13\x14\x1a\x15\x11\x11\x18!\x18\x1a\x1d\x1d\x1f\x1f\x1f\x13\x17"$"\x1e$\x1c\x1e\x1f\x1e\xff\xdb\x00C\x01\x05\x05\x05\x07\x06\x07\x0e\x08\x08\x0e\x1e\x14\x11\x14\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\xff\xc0\x00\x11\x08\x00\x08\x00\x08\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x15\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x19\x10\x00\x03\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x06\x11A\xff\xc4\x00\x14\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\x9d\xf29wU5Q\xd6\xfd\x00\x01\xff\xd9'
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
        self.assertEquals(u.photo, '\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xfe\x00\x1cCreated with GIMP on a Mac\xff\xdb\x00C\x00\x05\x03\x04\x04\x04\x03\x05\x04\x04\x04\x05\x05\x05\x06\x07\x0c\x08\x07\x07\x07\x07\x0f\x0b\x0b\t\x0c\x11\x0f\x12\x12\x11\x0f\x11\x11\x13\x16\x1c\x17\x13\x14\x1a\x15\x11\x11\x18!\x18\x1a\x1d\x1d\x1f\x1f\x1f\x13\x17"$"\x1e$\x1c\x1e\x1f\x1e\xff\xdb\x00C\x01\x05\x05\x05\x07\x06\x07\x0e\x08\x08\x0e\x1e\x14\x11\x14\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\xff\xc0\x00\x11\x08\x00\x08\x00\x08\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x15\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x19\x10\x00\x03\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x06\x11A\xff\xc4\x00\x14\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\x9d\xf29wU5Q\xd6\xfd\x00\x01\xff\xd9')

class AdminTestCase(BaseTestCase):
    fixtures = ['test_users.json']

    def test_index(self):
        self.client.login(username="test_user", password="password")
        response = self.client.get('/admin/examples/')
        self.assertContains(response, "Ldap groups")
        self.assertContains(response, "Ldap users")

    def test_list_groups(self):
        self.client.login(username="test_user", password="password")
        response = self.client.get('/admin/examples/ldapgroup/')
        self.assertContains(response, "Ldap groups")

    def test_list_users(self):
        self.client.login(username="test_user", password="password")
        response = self.client.get('/admin/examples/ldapuser/')
        self.assertContains(response, "Ldap users")
