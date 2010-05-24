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

from django.db.models import fields, SubfieldBase

from ldapdb import escape_ldap_filter

class CharField(fields.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 200
        super(CharField, self).__init__(*args, **kwargs)

    def get_db_prep_lookup(self, lookup_type, value):
        "Returns field's value prepared for database lookup."
        if lookup_type == 'endswith':
            return ["*%s" % escape_ldap_filter(value)]
        elif lookup_type == 'startswith':
            return ["%s*" % escape_ldap_filter(value)]
        elif lookup_type == 'contains':
            return ["*%s*" % escape_ldap_filter(value)]
        elif lookup_type == 'exact':
            return [escape_ldap_filter(value)]
        elif lookup_type == 'in':
            return [escape_ldap_filter(v) for v in value]

        raise TypeError("CharField has invalid lookup: %s" % lookup_type)

    def get_prep_lookup(self, lookup_type, value):
        "Perform preliminary non-db specific lookup checks and conversions"
        if lookup_type == 'endswith':
            return "*%s" % escape_ldap_filter(value)
        elif lookup_type == 'startswith':
            return "%s*" % escape_ldap_filter(value)
        elif lookup_type == 'contains':
            return "*%s*" % escape_ldap_filter(value)
        elif lookup_type == 'exact':
            return escape_ldap_filter(value)
        elif lookup_type == 'in':
            return [escape_ldap_filter(v) for v in value]

        raise TypeError("CharField has invalid lookup: %s" % lookup_type)

class ImageField(fields.Field):
    def get_db_prep_lookup(self, lookup_type, value):
        "Returns field's value prepared for database lookup."
        return [self.get_prep_lookup(lookup_type, value)]

    def get_prep_lookup(self, lookup_type, value):
        "Perform preliminary non-db specific lookup checks and conversions"
        raise TypeError("ImageField has invalid lookup: %s" % lookup_type)

class IntegerField(fields.IntegerField):
    def get_db_prep_lookup(self, lookup_type, value):
        "Returns field's value prepared for database lookup."
        return [self.get_prep_lookup(lookup_type, value)]

    def get_prep_lookup(self, lookup_type, value):
        "Perform preliminary non-db specific lookup checks and conversions"
        if lookup_type in ('exact', 'gte', 'lte'):
            return value
        raise TypeError("IntegerField has invalid lookup: %s" % lookup_type)

class ListField(fields.Field):
    __metaclass__ = SubfieldBase

    def get_db_prep_lookup(self, lookup_type, value):
        "Returns field's value prepared for database lookup."
        return [self.get_prep_lookup(lookup_type, value)]

    def get_prep_lookup(self, lookup_type, value):
        "Perform preliminary non-db specific lookup checks and conversions"
        if lookup_type == 'contains':
            return escape_ldap_filter(value)
        raise TypeError("ListField has invalid lookup: %s" % lookup_type)

    def to_python(self, value):
        if not value:
            return []
        return value

