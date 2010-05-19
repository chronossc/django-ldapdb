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

from django.db.models import fields, SubfieldBase

class CharField(fields.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 200
        super(CharField, self).__init__(*args, **kwargs)

    def get_db_prep_value(self, value):
        """Returns field's value prepared for interacting with the database
        backend.

        Used by the default implementations of ``get_db_prep_save``and
        `get_db_prep_lookup```
        """
        return value.replace('\\', '\\5c') \
                    .replace('*', '\\2a') \
                    .replace('(', '\\28') \
                    .replace(')', '\\29') \
                    .replace('\0', '\\00')

class ImageField(fields.Field):
    pass

class IntegerField(fields.IntegerField):
    pass

class ListField(fields.Field):
    __metaclass__ = SubfieldBase

    def to_python(self, value):
        if not value:
            return []
        return value

