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

import ldap
import logging

import django.db.models

from granadilla.db import connection as ldap_connection
from granadilla.db.query import QuerySet

class ModelBase(django.db.models.base.ModelBase):
    """
    Metaclass for all LDAP models.
    """
    def __new__(cls, name, bases, attrs):
        attr_meta = attrs.get('Meta', None)
        if attr_meta:
            dn = attr_meta._dn
            object_classes = attr_meta._object_classes

        super_new = super(ModelBase, cls).__new__
        new_class = super_new(cls, name, bases, attrs)

        # patch manager to use our own QuerySet class
        def get_query_set():
            return QuerySet(new_class)
        new_class.objects.get_query_set = get_query_set
        new_class._default_manager.get_query_set = get_query_set

        if attr_meta:
            new_class._meta.dn = dn
            new_class._meta.object_classes = attr_meta._object_classes

        return new_class

class Model(django.db.models.base.Model):
    """
    Base class for all LDAP models.
    """
    __metaclass__ = ModelBase

    def __init__(self, dn=None, *args, **kwargs):
        self.dn = dn
        super(Model, self).__init__(*args, **kwargs)

    def build_dn(self):
        """
        Build the Distinguished Name for this entry.
        """
        for field in self._meta.local_fields:
            if field.primary_key:
                return "%s=%s,%s" % (field.db_column, getattr(self, field.name), self._meta.dn)
        raise Exception("Could not build Distinguished Name")

    def delete(self):
        """
        Delete this entry.
        """
        logging.debug("Deleting LDAP entry %s" % self.dn)
        ldap_connection.delete_s(self.dn)
        
    def save(self):
        # create a new entry
        if not self.dn:
            entry = [('objectClass', self._meta.object_classes)]
            new_dn = self.build_dn()

            for field in self._meta.local_fields:
                if not field.db_column:
                    continue
                value = getattr(self, field.name)
                if value:
                    entry.append((field.db_column, value))

            logging.debug("Creating new LDAP entry %s" % new_dn)
            ldap_connection.add_s(new_dn, entry)
            
            # update object
            self.dn = new_dn
            return

        # update an existing entry
        modlist = []
        orig = self.__class__.objects.get(pk=self.pk)
        for field in self._meta.local_fields:
            if not field.db_column:
                continue
            old_value = getattr(orig, field.name, None)
            new_value = getattr(self, field.name, None)
            if old_value != new_value:
                if new_value:
                    modlist.append((ldap.MOD_REPLACE, field.db_column, new_value))
                elif old_value:
                    modlist.append((ldap.MOD_DELETE, field.db_column, None))

        if len(modlist):
            logging.debug("Modifying existing LDAP entry %s" % self.dn)
            ldap_connection.modify_s(self.dn, modlist)
        else:
            logging.debug("No changes to be saved to LDAP entry %s" % self.dn)

