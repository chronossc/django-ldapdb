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

from django.test import TestCase
from django.db.models.sql.where import Constraint, AND, OR

from ldapdb.models.query import WhereNode

class WhereTestCase(TestCase):
    def test_single(self):
        where = WhereNode()
        where.add((Constraint("cn", "cn", None), 'exact', "test"), AND)
        self.assertEquals(where.as_sql(), "(cn=test)")

    def test_and(self):
        where = WhereNode()
        where.add((Constraint("cn", "cn", None), 'exact', "foo"), AND)
        where.add((Constraint("givenName", "givenName", None), 'exact', "bar"), AND)
        self.assertEquals(where.as_sql(), "(&(cn=foo)(givenName=bar))")

    def test_or(self):
        where = WhereNode()
        where.add((Constraint("cn", "cn", None), 'exact', "foo"), AND)
        where.add((Constraint("givenName", "givenName", None), 'exact', "bar"), OR)
        self.assertEquals(where.as_sql(), "(|(cn=foo)(givenName=bar))")

