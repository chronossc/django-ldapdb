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

from copy import deepcopy
import ldap

from django.db.models.query import QuerySet as BaseQuerySet
from django.db.models.query_utils import Q
from django.db.models.sql import Query as BaseQuery
from django.db.models.sql.where import WhereNode as BaseWhereNode, Constraint as BaseConstraint, AND, OR

import ldapdb

def escape_ldap_filter(value):
    value = str(value)
    return value.replace('\\', '\\5c') \
                .replace('*', '\\2a') \
                .replace('(', '\\28') \
                .replace(')', '\\29') \
                .replace('\0', '\\00')

class Constraint(BaseConstraint):
    """
    An object that can be passed to WhereNode.add() and knows how to
    pre-process itself prior to including in the WhereNode.
    """
    def process(self, lookup_type, value):
        """
        Returns a tuple of data suitable for inclusion in a WhereNode
        instance.
        """
        # Because of circular imports, we need to import this here.
        from django.db.models.base import ObjectDoesNotExist

        if lookup_type == 'endswith':
            params = ["*%s" % escape_ldap_filter(value)]
        elif lookup_type == 'startswith':
            params = ["%s*" % escape_ldap_filter(value)]
        elif lookup_type == 'contains':
            params = ["*%s*" % escape_ldap_filter(value)]
        elif lookup_type == 'exact':
            params = [escape_ldap_filter(value)]
        elif lookup_type == 'in':
            params = [escape_ldap_filter(v) for v in value]
        else:
            raise TypeError("Field has invalid lookup: %s" % lookup_type)

        try:
            if self.field:
                db_type = self.field.db_type()
            else:
                db_type = None
        except ObjectDoesNotExist:
            raise EmptyShortCircuit

        return (self.alias, self.col, db_type), params

class WhereNode(BaseWhereNode):
    def add(self, data, connector):
        if not isinstance(data, (list, tuple)):
            super(WhereNode, self).add(data, connector)
            return

        # we replace the native Constraint by our own
        obj, lookup_type, value = data
        if hasattr(obj, "process"):
            obj = Constraint(obj.alias, obj.col, obj.field)
        super(WhereNode, self).add((obj, lookup_type, value), connector)

    def as_sql(self):
        bits = []
        for item in self.children:
            if isinstance(item, WhereNode):
                bits.append(item.as_sql())
                continue
            (table, column, type), x, y, values = item
            equal_bits = [ "(%s=%s)" % (column, value) for value in values ]
            if len(equal_bits) == 1:
                clause = equal_bits[0]
            else:
                clause = '(|%s)' % ''.join(equal_bits)
            if self.negated:
                bits.append('(!%s)' % clause)
            else:
                bits.append(clause)
        if len(bits) == 1:
            return bits[0]
        elif self.connector == AND:
            return '(&%s)' % ''.join(bits)
        elif self.connector == OR:
            return '(|%s)' % ''.join(bits)
        else:
            raise Exception("Unhandled WHERE connector: %s" % self.connector)

class Query(BaseQuery):
    def results_iter(self):
        # FIXME: use all object classes
        filterstr = '(objectClass=%s)' % self.model.object_classes[0]
        filterstr += self.where.as_sql()
        filterstr = '(&%s)' % filterstr
        attrlist = [ x.db_column for x in self.model._meta.local_fields if x.db_column ]

        try:
            vals = ldapdb.connection.search_s(
                self.model.base_dn,
                ldap.SCOPE_SUBTREE,
                filterstr=filterstr,
                attrlist=attrlist,
            )
        except:
            raise self.model.DoesNotExist

        # perform sorting
        if self.extra_order_by:
            ordering = self.extra_order_by
        elif not self.default_ordering:
            ordering = self.order_by
        else:
            ordering = self.order_by or self.model._meta.ordering
        def getkey(x):
            keys = []
            for k in ordering:
                attr = self.model._meta.get_field(k).db_column
                keys.append(x[1].get(attr, '').lower())
            return keys
        vals = sorted(vals, key=lambda x: getkey(x))

        # process results
        for dn, attrs in vals:
            row = []
            for field in iter(self.model._meta.fields):
                if field.attname == 'dn':
                    row.append(dn)
                else:
                    row.append(attrs.get(field.db_column, None))
            yield row

class QuerySet(BaseQuerySet):
    def __init__(self, model=None, query=None):
        if not query:
            query = Query(model, None, WhereNode)
        super(QuerySet, self).__init__(model, query)

