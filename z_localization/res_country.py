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

class res_region(osv.osv):
    _name = 'res.region'
    _description = 'Region'
    _columns = {
        'name': fields.char('Name', size=128, required=True),
    }
    
    def init(self, cr):
        wb = xlrd.open_workbook(base_path + '/z_localization/data/res_region.xls')
        wb.sheet_names()
        sh = wb.sheet_by_index(0)
        
        i = -1
        for rownum in range(sh.nrows):
            i += 1
            row_values = sh.row_values(rownum)
            
            if i == 0:
                continue
            
            try:
                cr.execute('''
                INSERT INTO res_region(name)
                SELECT '%s'
                WHERE not exists (select id from res_region where name='%s')
                '''%(row_values[0],
                     row_values[0]))
                cr.execute('commit;')
            except Exception, e:
                continue
        return True
res_region()

class Country(osv.osv):
    _inherit = 'res.country'
    _description = 'Country'
    _columns = {
        'flag': fields.binary("Flag"),
        'alias': fields.char('Alias', size=50),
        'region': fields.many2one('res.region', 'Region'),
        
        'currency_id': fields.many2one('res.currency', 'Sell Currency'),
        'local_currency_id': fields.many2one('res.currency', 'Local Currency'),
        'phone_code': fields.char('Phone code', size=5),
        'tax_ids': fields.many2many('account.tax', 'country_tax_rel', 'country_id', 'tax_id', 'Taxes', domain=[('parent_id','=',False)]),
        'company_id': fields.many2one('res.company', 'Controlling Office'),
    }
    
#     def _check_phone_code(self, cr, uid, ids, context=None):
#         for country in self.read(cr, uid, ids, ['phone_code']):
#             if country['phone_code']:
#                 phone_code = country['phone_code']
#                 for i in range(len(phone_code)):
#                     if not isinstance(phone_code[i], int):
#                         return False
#         return True
# 
#     _constraints = [
#         (_check_phone_code, '\nInput Error! Phone code should have numeric only.', ['phone_code'])
#     ]
    
Country()

class res_city(osv.osv):
    _name = 'res.city'
    _columns = {
        'name': fields.char('Name', size=128, required=True),
        'state_id': fields.many2one('res.country.state', 'State'),
        'country_id': fields.related('state_id', 'country_id', type='many2one', readonly=True, relation='res.country', string='Country'),
        'postcode_line': fields.one2many('postal.code', 'city_id', 'Postal Codes')
    }
    
class postal_code(osv.osv):
    _name = 'postal.code'
    _columns = {
        'name': fields.char('Postal Code', size=128, required=True),
        'city_id': fields.many2one('res.city', 'City', ondelete='cascade', required=True)
    }
    
class CountryState(osv.osv):
    _inherit = 'res.country.state'
    _columns = {
        'code': fields.char('State Code', size=10,
            help='The state code in max. three chars.', required=False),
        'city_line': fields.one2many('res.city', 'state_id', 'Cities'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
