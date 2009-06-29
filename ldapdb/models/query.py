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

# -*- coding: utf-8 -*-

from copy import deepcopy
import ldap

from django.db.models.query import QuerySet as BaseQuerySet
from django.db.models.query_utils import Q
from django.db.models.sql import BaseQuery
from django.db.models.sql.where import WhereNode
from granadilla.db import connection as ldap_connection

def compile(q):
    filterstr = ""
    for item in q.children:
        if isinstance(item, WhereNode):
            filterstr += compile(item)
            continue
        table, column, type, x, y, values = item
        if q.negated:
            filterstr += "(!(%s=%s))" % (column,values[0])
        else:
            filterstr += "(%s=%s)" % (column,values[0])
    return filterstr

class Query(BaseQuery):
    def results_iter(self):
        # FIXME: use all object classes
        filterstr = '(objectClass=%s)' % self.model._meta.object_classes[0]
        filterstr += compile(self.where)
        filterstr = '(&%s)' % filterstr
        attrlist = [ x.db_column for x in self.model._meta.local_fields if x.db_column ]

        try:
            vals = ldap_connection.search_s(
                self.model._meta.dn,
                ldap.SCOPE_SUBTREE,
                filterstr=filterstr,
                attrlist=attrlist,
            )
        except:
            raise self.model.DoesNotExist

        for dn, attrs in vals:
            row = [dn]
            for field in iter(self.model._meta.fields):
                row.append(attrs.get(field.db_column, None))
            yield row

class QuerySet(BaseQuerySet):
    def __init__(self, model=None, query=None):
        if not query:
            query = Query(model, None)
        super(QuerySet, self).__init__(model, query)

