# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime

import xlrd
from openerp import SUPERUSER_ID

import os
from openerp import modules
base_path = os.path.dirname(modules.get_module_path('z_localization'))

class Country(osv.osv):
    _inherit = 'res.country'
    _columns = {
        'default_shipping_id': fields.many2one('delivery.carrier', 'Default Shipping'),
    }
    
Country()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
