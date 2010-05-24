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
from django.db.models.sql.where import Constraint, AND, OR

from ldapdb.models.query import escape_ldap_filter
from ldapdb.models.fields import CharField, IntegerField, ListField
from ldapdb.models.query import WhereNode

class WhereTestCase(TestCase):
    def test_escape(self):
        self.assertEquals(escape_ldap_filter('foo*bar'), 'foo\\2abar')
        self.assertEquals(escape_ldap_filter('foo(bar'), 'foo\\28bar')
        self.assertEquals(escape_ldap_filter('foo)bar'), 'foo\\29bar')
        self.assertEquals(escape_ldap_filter('foo\\bar'), 'foo\\5cbar')
        self.assertEquals(escape_ldap_filter('foo\\bar*wiz'), 'foo\\5cbar\\2awiz')

    def test_char_field(self):
        where = WhereNode()
        where.add((Constraint("cn", "cn", CharField()), 'exact', "test"), AND)
        self.assertEquals(where.as_sql(), "(cn=test)")

        where = WhereNode()
        where.add((Constraint("cn", "cn", CharField()), 'exact', "(test)"), AND)
        self.assertEquals(where.as_sql(), "(cn=\\28test\\29)")

        where = WhereNode()
        where.add((Constraint("cn", "cn", CharField()), 'startswith', "test"), AND)
        self.assertEquals(where.as_sql(), "(cn=test*)")

        where = WhereNode()
        where.add((Constraint("cn", "cn", CharField()), 'endswith', "test"), AND)
        self.assertEquals(where.as_sql(), "(cn=*test)")

        where = WhereNode()
        where.add((Constraint("cn", "cn", CharField()), 'in', ["foo", "bar"]), AND)
        self.assertEquals(where.as_sql(), "(|(cn=foo)(cn=bar))")

        where = WhereNode()
        where.add((Constraint("cn", "cn", CharField()), 'contains', "test"), AND)
        self.assertEquals(where.as_sql(), "(cn=*test*)")

    def test_integer_field(self):
        where = WhereNode()
        where.add((Constraint("uid", "uid", CharField()), 'exact', 1), AND)
        self.assertEquals(where.as_sql(), "(uid=1)")

    def test_and(self):
        where = WhereNode()
        where.add((Constraint("cn", "cn", CharField()), 'exact', "foo"), AND)
        where.add((Constraint("givenName", "givenName", CharField()), 'exact', "bar"), AND)
        self.assertEquals(where.as_sql(), "(&(cn=foo)(givenName=bar))")

    def test_or(self):
        where = WhereNode()
        where.add((Constraint("cn", "cn", CharField()), 'exact', "foo"), AND)
        where.add((Constraint("givenName", "givenName", CharField()), 'exact', "bar"), OR)
        self.assertEquals(where.as_sql(), "(|(cn=foo)(givenName=bar))")

