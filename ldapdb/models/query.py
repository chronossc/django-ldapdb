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

from copy import deepcopy
import ldap

from django.db.models.query import QuerySet as BaseQuerySet
from django.db.models.query_utils import Q
from django.db.models.sql import Query as BaseQuery
from django.db.models.sql.where import WhereNode as BaseWhereNode, Constraint as BaseConstraint, AND, OR

import ldapdb

from ldapdb.models.fields import CharField

def get_lookup_operator(lookup_type):
    if lookup_type == 'gte':
        return '>='
    elif lookup_type == 'lte':
        return '<='
    else:
        return '='

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

        try:
            if self.field:
                params = self.field.get_db_prep_lookup(lookup_type, value)
                db_type = self.field.db_type()
            else:
                params = CharField().get_db_prep_lookup(lookup_type, value)
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

    def as_sql(self, qn=None, connection=None):
        bits = []
        for item in self.children:
            if hasattr(item, 'as_sql'):
                sql, params = item.as_sql(qn=qn, connection=connection)
                bits.append(sql)
                continue

            constraint, lookup_type, y, values = item
            comp = get_lookup_operator(lookup_type)
            if hasattr(constraint, "col"):
                # django 1.2
                column = constraint.col
                if lookup_type == 'in':
                    equal_bits = [ "(%s%s%s)" % (column, comp, value) for value in values ]
                    clause = '(|%s)' % ''.join(equal_bits)
                else:
                    clause = "(%s%s%s)" % (constraint.col, comp, values)
            else:
                # django 1.1
                (table, column, db_type) = constraint
                equal_bits = [ "(%s%s%s)" % (column, comp, value) for value in values ]
                if len(equal_bits) == 1:
                    clause = equal_bits[0]
                else:
                    clause = '(|%s)' % ''.join(equal_bits)

            if self.negated:
                bits.append('(!%s)' % clause)
            else:
                bits.append(clause)
        if len(bits) == 1:
            sql_string = bits[0]
        elif self.connector == AND:
            sql_string = '(&%s)' % ''.join(bits)
        elif self.connector == OR:
            sql_string = '(|%s)' % ''.join(bits)
        else:
            raise Exception("Unhandled WHERE connector: %s" % self.connector)
        return sql_string, []

class Query(BaseQuery):
    def __init__(self, *args, **kwargs):
        super(Query, self).__init__(*args, **kwargs)
        self.connection = ldapdb.connection

    def get_count(self):
        filterstr = ''.join(['(objectClass=%s)' % cls for cls in self.model.object_classes])
        sql, params = self.where.as_sql()
        filterstr += sql
        filterstr = '(&%s)' % filterstr

        try:
            vals = ldapdb.connection.search_s(
                self.model.base_dn,
                ldap.SCOPE_SUBTREE,
                filterstr=filterstr,
                attrlist=[],
            )
        except:
            raise self.model.DoesNotExist

        return len(vals)

    def results_iter(self):
        filterstr = ''.join(['(objectClass=%s)' % cls for cls in self.model.object_classes])
        sql, params = self.where.as_sql()
        filterstr += sql
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
        def cmpvals(x, y):
            for field in ordering:
                if field.startswith('-'):
                    field = field[1:]
                    negate = True
                else:
                    negate = False
                attr = self.model._meta.get_field(field).db_column
                attr_x = x[1].get(attr, '').lower()
                attr_y = y[1].get(attr, '').lower()
                val = negate and cmp(attr_y, attr_x) or cmp(attr_x, attr_y)
                if val:
                    return val
            return 0
        vals = sorted(vals, cmp=cmpvals)

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
    def __init__(self, model=None, query=None, using=None):
        if not query:
            import inspect
            spec = inspect.getargspec(BaseQuery.__init__)
            if len(spec[0]) == 3:
                # django 1.2
                query = Query(model, WhereNode)
            else:
                # django 1.1
                query = Query(model, None, WhereNode)
        super(QuerySet, self).__init__(model=model, query=query)

