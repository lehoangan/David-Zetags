# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
import logging

import openerp
from openerp.modules.registry import RegistryManager

_logger = logging.getLogger(__name__)

class Controller(openerp.addons.web.http.Controller):
    _cp_path = '/auth_2step'

    @openerp.addons.web.http.jsonrequest
    def get_config(self, req, dbname):
        """ retrieve the module config (which features are enabled) for the login page """
        registry = RegistryManager.get(dbname)
        with registry.cursor() as cr:
            icp = registry.get('ir.config_parameter')
            config = {
                'otp': True,
            }
        return config

    @openerp.addons.web.http.jsonrequest
    def validated_otp(self, req, dbname, token, **values):
        """ sign up a user (new or existing)"""
        try:
            self._check_otp(req, dbname, token, values)
        except:
            return {'error': 'Invalid OTP'}
        return {}

    def _check_otp(self, req, dbname, token, values):
        registry = RegistryManager.get(dbname)
        with registry.cursor() as cr:
            res_users = registry.get('res.users')
            res_users._check_otp(cr, openerp.SUPERUSER_ID, values, token)

    @openerp.addons.web.http.jsonrequest
    def show_opt(self, req, dbname, token, **values):
        """ sign up a user (new or existing)"""
        try:
            return self._check_show_otp(req, dbname, token, values)
        except:
            return {'error': 'Invalid OTP'}
        return {}

    def _check_show_otp(self, req, dbname, token, values):
        registry = RegistryManager.get(dbname)
        with registry.cursor() as cr:
            res_users = registry.get('res.users')
            return res_users._check_show_otp(cr, openerp.SUPERUSER_ID, values, token)

    @openerp.addons.web.http.jsonrequest
    def send_otp(self, req, dbname, token, **values):
        """ sign up a user (new or existing)"""
        try:
            self._send_otp(req, dbname, token, values)
        except:
            return {'error': 'Invalid OTP'}
        return {}

    def _send_otp(self, req, dbname, token, values):
        registry = RegistryManager.get(dbname)
        with registry.cursor() as cr:
            res_users = registry.get('res.users')
            res_users._send_otp(cr, openerp.SUPERUSER_ID, values, token)


# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:
