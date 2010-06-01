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

from django.test import TestCase

import ldap
import ldapdb
from examples.models import LdapUser, LdapGroup

class BaseTestCase(TestCase):
    def setUp(self):
        cursor = ldapdb.connection._cursor()
        for base in [LdapGroup.base_dn, LdapUser.base_dn]:
            rdn = base.split(',')[0]
            key, val = rdn.split('=')
            attrs = [('objectClass', ['top', 'organizationalUnit']), (key, [val])]
            try:
                cursor.connection.add_s(base, attrs)
            except ldap.ALREADY_EXISTS:
                pass

    def tearDown(self):
        cursor = ldapdb.connection._cursor()
        for base in [LdapGroup.base_dn, LdapUser.base_dn]:
            try:
                results = cursor.connection.search_s(base, ldap.SCOPE_SUBTREE)
                for dn, attrs in reversed(results):
                    cursor.connection.delete_s(dn)
            except ldap.NO_SUCH_OBJECT:
                pass

class GroupTestCase(BaseTestCase):
    def setUp(self):
        super(GroupTestCase, self).setUp()

        g = LdapGroup()
        g.name = "foogroup"
        g.gid = 1000
        g.usernames = ['foouser', 'baruser']
        g.save()

        g = LdapGroup()
        g.name = "bargroup"
        g.gid = 1001
        g.usernames = ['zoouser', 'baruser']
        g.save()

        g = LdapGroup()
        g.name = "wizgroup"
        g.gid = 1002
        g.usernames = ['wizuser', 'baruser']
        g.save()

    def test_count(self):
        # empty query
        qs = LdapGroup.objects.none()
        self.assertEquals(qs.count(), 0)

        qs = LdapGroup.objects.none()
        self.assertEquals(len(qs), 0)

        # all query
        qs = LdapGroup.objects.all()
        self.assertEquals(qs.count(), 3)

        qs = LdapGroup.objects.all()
        self.assertEquals(len(qs), 3)

    def test_filter(self):
        qs = LdapGroup.objects.filter(name='foogroup')
        self.assertEquals(qs.count(), 1)

        qs = LdapGroup.objects.filter(name='foogroup')
        self.assertEquals(len(qs), 1)

        g = qs[0]
        self.assertEquals(g.dn, 'cn=foogroup,%s' % LdapGroup.base_dn)
        self.assertEquals(g.name, 'foogroup')
        self.assertEquals(g.gid, 1000)
        self.assertEquals(g.usernames, ['foouser', 'baruser'])

        # try to filter non-existent entries
        qs = LdapGroup.objects.filter(name='does_not_exist')
        self.assertEquals(qs.count(), 0)

        qs = LdapGroup.objects.filter(name='does_not_exist')
        self.assertEquals(len(qs), 0)

    def test_get(self):
        g = LdapGroup.objects.get(name='foogroup')
        self.assertEquals(g.dn, 'cn=foogroup,%s' % LdapGroup.base_dn)
        self.assertEquals(g.name, 'foogroup')
        self.assertEquals(g.gid, 1000)
        self.assertEquals(g.usernames, ['foouser', 'baruser'])

        # try to get a non-existent entry
        self.assertRaises(LdapGroup.DoesNotExist, LdapGroup.objects.get, name='does_not_exist')

    def test_order_by(self):
        # ascending name 
        qs = LdapGroup.objects.order_by('name')
        self.assertEquals(len(qs), 3)
        self.assertEquals(qs[0].name, 'bargroup')
        self.assertEquals(qs[1].name, 'foogroup')
        self.assertEquals(qs[2].name, 'wizgroup')

        # descending name 
        qs = LdapGroup.objects.order_by('-name')
        self.assertEquals(len(qs), 3)
        self.assertEquals(qs[0].name, 'wizgroup')
        self.assertEquals(qs[1].name, 'foogroup')
        self.assertEquals(qs[2].name, 'bargroup')

        # ascending gid
        qs = LdapGroup.objects.order_by('gid')
        self.assertEquals(len(qs), 3)
        self.assertEquals(qs[0].gid, 1000)
        self.assertEquals(qs[1].gid, 1001)
        self.assertEquals(qs[2].gid, 1002)

        # descending gid
        qs = LdapGroup.objects.order_by('-gid')
        self.assertEquals(len(qs), 3)
        self.assertEquals(qs[0].gid, 1002)
        self.assertEquals(qs[1].gid, 1001)
        self.assertEquals(qs[2].gid, 1000)

    def test_bulk_delete(self):
        LdapGroup.objects.all().delete()

        qs = LdapGroup.objects.all()
        self.assertEquals(len(qs), 0)

    def test_slice(self):
        qs = LdapGroup.objects.all()
        objs = list(qs)
        self.assertEquals(len(objs), 3)
        self.assertEquals(objs[0].gid, 1000)
        self.assertEquals(objs[1].gid, 1001)
        self.assertEquals(objs[2].gid, 1002)

        # limit only
        qs = LdapGroup.objects.all()
        objs = qs[:2]
        self.assertEquals(objs.count(), 2)

        objs = qs[:2]
        self.assertEquals(len(objs), 2)
        self.assertEquals(objs[0].gid, 1000)
        self.assertEquals(objs[1].gid, 1001)

        # offset only
        qs = LdapGroup.objects.all()
        objs = qs[1:]
        self.assertEquals(objs.count(), 2)

        objs = qs[1:]
        self.assertEquals(len(objs), 2)
        self.assertEquals(objs[0].gid, 1001)
        self.assertEquals(objs[1].gid, 1002)

        # offset and limit
        qs = LdapGroup.objects.all()
        objs = qs[1:2]
        self.assertEquals(objs.count(), 1)

        objs = qs[1:2]
        self.assertEquals(len(objs), 1)
        self.assertEquals(objs[0].gid, 1001)

    def test_update(self):
        g = LdapGroup.objects.get(name='foogroup')

        g.gid = 1002
        g.usernames = ['foouser2', 'baruser2']
        g.save()

        # make sure DN gets updated if we change the pk
        g.name = 'foogroup2'
        g.save()
        self.assertEquals(g.dn, 'cn=foogroup2,%s' % LdapGroup.base_dn)

    def test_values(self):
        qs = LdapGroup.objects.values('name')
        self.assertEquals(len(qs), 3)
        self.assertEquals(qs[0], {'name': 'foogroup'})
        self.assertEquals(qs[1], {'name': 'bargroup'})
        self.assertEquals(qs[2], {'name': 'wizgroup'})

    def test_values_list(self):
        qs = LdapGroup.objects.values_list('name')
        self.assertEquals(len(qs), 3)
        self.assertEquals(qs[0], ('foogroup',))
        self.assertEquals(qs[1], ('bargroup',))
        self.assertEquals(qs[2], ('wizgroup',))

    def test_delete(self):
        g = LdapGroup.objects.get(name='foogroup')
        g.delete()

        qs = LdapGroup.objects.all()
        self.assertEquals(len(qs), 2)

class UserTestCase(BaseTestCase):
    def setUp(self):
        super(UserTestCase, self).setUp()

        u = LdapUser()
        u.first_name = u"Fôo"
        u.last_name = u"Usér"
        u.full_name = u"Fôo Usér"

        u.group = 1000
        u.home_directory = "/home/foouser"
        u.uid = 2000
        u.username = "foouser"
        u.photo = '\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xfe\x00\x1cCreated with GIMP on a Mac\xff\xdb\x00C\x00\x05\x03\x04\x04\x04\x03\x05\x04\x04\x04\x05\x05\x05\x06\x07\x0c\x08\x07\x07\x07\x07\x0f\x0b\x0b\t\x0c\x11\x0f\x12\x12\x11\x0f\x11\x11\x13\x16\x1c\x17\x13\x14\x1a\x15\x11\x11\x18!\x18\x1a\x1d\x1d\x1f\x1f\x1f\x13\x17"$"\x1e$\x1c\x1e\x1f\x1e\xff\xdb\x00C\x01\x05\x05\x05\x07\x06\x07\x0e\x08\x08\x0e\x1e\x14\x11\x14\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\xff\xc0\x00\x11\x08\x00\x08\x00\x08\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x15\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x19\x10\x00\x03\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x06\x11A\xff\xc4\x00\x14\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\x9d\xf29wU5Q\xd6\xfd\x00\x01\xff\xd9'
        u.save()

    def test_get(self):
        u = LdapUser.objects.get(username='foouser')
        self.assertEquals(u.first_name, u'Fôo')
        self.assertEquals(u.last_name, u'Usér')
        self.assertEquals(u.full_name, u'Fôo Usér')

        self.assertEquals(u.group, 1000)
        self.assertEquals(u.home_directory, '/home/foouser')
        self.assertEquals(u.uid, 2000)
        self.assertEquals(u.username, 'foouser')
        self.assertEquals(u.photo, '\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xfe\x00\x1cCreated with GIMP on a Mac\xff\xdb\x00C\x00\x05\x03\x04\x04\x04\x03\x05\x04\x04\x04\x05\x05\x05\x06\x07\x0c\x08\x07\x07\x07\x07\x0f\x0b\x0b\t\x0c\x11\x0f\x12\x12\x11\x0f\x11\x11\x13\x16\x1c\x17\x13\x14\x1a\x15\x11\x11\x18!\x18\x1a\x1d\x1d\x1f\x1f\x1f\x13\x17"$"\x1e$\x1c\x1e\x1f\x1e\xff\xdb\x00C\x01\x05\x05\x05\x07\x06\x07\x0e\x08\x08\x0e\x1e\x14\x11\x14\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\xff\xc0\x00\x11\x08\x00\x08\x00\x08\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x15\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x19\x10\x00\x03\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x06\x11A\xff\xc4\x00\x14\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\x9d\xf29wU5Q\xd6\xfd\x00\x01\xff\xd9')

        self.assertRaises(LdapUser.DoesNotExist, LdapUser.objects.get, username='does_not_exist')

    def test_update(self):
        u = LdapUser.objects.get(username='foouser')
        u.first_name = u'Fôo2'
        u.save()
        
        # make sure DN gets updated if we change the pk
        u.username = 'foouser2'
        u.save()
        self.assertEquals(u.dn, 'uid=foouser2,%s' % LdapUser.base_dn)

class AdminTestCase(BaseTestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        super(AdminTestCase, self).setUp()

        g = LdapGroup()
        g.name = "foogroup"
        g.gid = 1000
        g.usernames = ['foouser', 'baruser']
        g.save()

        g = LdapGroup()
        g.name = "bargroup"
        g.gid = 1001
        g.usernames = ['zoouser', 'baruser']
        g.save()

        u = LdapUser()
        u.first_name = "Foo"
        u.last_name = "User"
        u.full_name = "Foo User"
        u.group = 1000
        u.home_directory = "/home/foouser"
        u.uid = 2000
        u.username = "foouser"
        u.save()

        u = LdapUser()
        u.first_name = "Bar"
        u.last_name = "User"
        u.full_name = "Bar User"
        u.group = 1001
        u.home_directory = "/home/baruser"
        u.uid = 2001
        u.username = "baruser"
        u.save()

        self.client.login(username="test_user", password="password")

    def test_index(self):
        response = self.client.get('/admin/examples/')
        self.assertContains(response, "Ldap groups")
        self.assertContains(response, "Ldap users")

    def test_group_list(self):
        response = self.client.get('/admin/examples/ldapgroup/')
        self.assertContains(response, "Ldap groups")
        self.assertContains(response, "foogroup")
        self.assertContains(response, "1000")

        # order by name
        response = self.client.get('/admin/examples/ldapgroup/?o=1')
        self.assertContains(response, "Ldap groups")
        self.assertContains(response, "foogroup")
        self.assertContains(response, "1000")

        # order by gid
        response = self.client.get('/admin/examples/ldapgroup/?o=2')
        self.assertContains(response, "Ldap groups")
        self.assertContains(response, "foogroup")
        self.assertContains(response, "1000")

    def test_group_detail(self):
        response = self.client.get('/admin/examples/ldapgroup/foogroup/')
        self.assertContains(response, "foogroup")
        self.assertContains(response, "1000")

    def test_group_delete(self):
        response = self.client.post('/admin/examples/ldapgroup/foogroup/delete/', {'yes': 'post'})
        self.assertRedirects(response, '/admin/examples/ldapgroup/')

    def test_group_search(self):
        response = self.client.get('/admin/examples/ldapgroup/?q=foo')
        self.assertContains(response, "Ldap groups")
        self.assertContains(response, "foogroup")
        self.assertContains(response, "1000")

    def test_user_list(self):
        response = self.client.get('/admin/examples/ldapuser/')
        self.assertContains(response, "Ldap users")
        self.assertContains(response, "foouser")
        self.assertContains(response, "2000")

        # order by username
        response = self.client.get('/admin/examples/ldapuser/?o=1')
        self.assertContains(response, "Ldap users")
        self.assertContains(response, "foouser")
        self.assertContains(response, "2000")

        # order by uid
        response = self.client.get('/admin/examples/ldapuser/?o=2')
        self.assertContains(response, "Ldap users")
        self.assertContains(response, "foouser")
        self.assertContains(response, "2000")

    def test_user_detail(self):
        response = self.client.get('/admin/examples/ldapuser/foouser/')
        self.assertContains(response, "foouser")
        self.assertContains(response, "2000")

    def test_user_delete(self):
        response = self.client.post('/admin/examples/ldapuser/foouser/delete/', {'yes': 'post'})
        self.assertRedirects(response, '/admin/examples/ldapuser/')

