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
import openerp.addons.decimal_precision as dp
from openerp import netsvc

 
class purchase_order(osv.osv):
    _inherit = "purchase.order"
 
    _columns = {
        'shipping_date': fields.date('Shipping Date'),
        'tracking_number': fields.char('Tracking Number', size=50, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'product_tariff_code_id': fields.many2one('product.tariff.code', 'HS Tariff Code', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'weight': fields.float('Weight', digits=(16,2), readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'packages': fields.char('Packages #', size=20, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
    }

    def action_invoice_create(self, cr, uid, ids, context=None):
        inv_id = super(purchase_order, self).action_invoice_create(cr, uid, ids, context)
        for order in self.browse(cr, uid, ids, context=context):
            self.pool.get('account.invoice').write(cr, uid, [inv_id],{
                'product_tariff_code_id':order.product_tariff_code_id.id or False,
                'tracking_number':order.tracking_number,
                'weight':order.weight,
                'packages': order.packages,
            })
        return inv_id

purchase_order()