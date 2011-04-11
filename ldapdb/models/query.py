# -*- coding: utf-8 -*-
# 
# django-ldapdb
# Copyright (c) 2009-2010, Bolloré telecom
# All rights reserved.
# 
# See AUTHORS file for a full list of contributors.
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
#     1. Redistributions of source code must retain the above copyright notice, 
#        this list of conditions and the following disclaimer.
#     
#     2. Redistributions in binary form must reproduce the above copyright 
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
# 
#     3. Neither the name of Bolloré telecom nor the names of its contributors
#        may be used to endorse or promote products derived from this software
#        without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from copy import deepcopy
import ldap

from django.db.models.query import QuerySet as BaseQuerySet
from django.db.models.query_utils import Q
from django.db.models.sql import Query as BaseQuery
from django.db.models.sql.where import WhereNode as BaseWhereNode, Constraint as BaseConstraint, AND, OR

import ldapdb
from ldapdb.backends.ldap import compiler
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

    NOTES: 
    - we redefine this class, because when self.field is None calls
    Field().get_db_prep_lookup(), which short-circuits our LDAP-specific code.
    """
    def process(self, lookup_type, value, connection):
        """
        Returns a tuple of data suitable for inclusion in a WhereNode
        instance.
        """
        # Because of circular imports, we need to import this here.
        from django.db.models.base import ObjectDoesNotExist

        try:
            if self.field:
                params = self.field.get_db_prep_lookup(lookup_type, value,
                    connection=connection, prepared=True)
                db_type = self.field.db_type()
            else:
                params = CharField().get_db_prep_lookup(lookup_type, value,
                    connection=connection, prepared=True)
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
            if lookup_type == 'in':
                equal_bits = [ "(%s%s%s)" % (constraint.col, comp, value) for value in values ]
                clause = '(|%s)' % ''.join(equal_bits)
            else:
                clause = "(%s%s%s)" % (constraint.col, comp, values)

            bits.append(clause)

        if not len(bits):
            return '', []

        if len(bits) == 1:
            sql_string = bits[0]
        elif self.connector == AND:
            sql_string = '(&%s)' % ''.join(bits)
        elif self.connector == OR:
            sql_string = '(|%s)' % ''.join(bits)
        else:
            raise Exception("Unhandled WHERE connector: %s" % self.connector)

        if self.negated:
            sql_string = ('(!%s)' % sql_string)

        return sql_string, []

class Query(BaseQuery):
    def __init__(self, *args, **kwargs):
        super(Query, self).__init__(*args, **kwargs)
        self.connection = ldapdb.connection

    def _ldap_filter(self):
        filterstr = ''.join(['(objectClass=%s)' % cls for cls in self.model.object_classes])
        sql, params = self.where.as_sql()
        filterstr += sql
        return '(&%s)' % filterstr

    def get_count(self, using):
        try:
            vals = ldapdb.connection.search_s(
                self.model.base_dn,
                self.model.search_scope,
                filterstr=self._ldap_filter(),
                attrlist=[],
            )
        except ldap.NO_SUCH_OBJECT:
            return 0

        number = len(vals)

        # apply limit and offset
        number = max(0, number - self.low_mark)
        if self.high_mark is not None:
            number = min(number, self.high_mark - self.low_mark)

        return number

    def get_compiler(self, using=None, connection=None):
        return compiler.SQLCompiler(self, ldapdb.connection, using)

    def has_results(self, using):
        return self.get_count(using) != 0

class QuerySet(BaseQuerySet):
    def __init__(self, model=None, query=None, using=None):
        if not query:
            query = Query(model, WhereNode)
        super(QuerySet, self).__init__(model=model, query=query, using=using)

    def delete(self):
        "Bulk deletion."
        try:
            vals = ldapdb.connection.search_s(
                self.model.base_dn,
                self.model.search_scope,
                filterstr=self.query._ldap_filter(),
                attrlist=[],
            )
        except ldap.NO_SUCH_OBJECT:
            return

        # FIXME : there is probably a more efficient way to do this 
        for dn, attrs in vals:
            ldapdb.connection.delete_s(dn)

