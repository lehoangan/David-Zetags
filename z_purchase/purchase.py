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

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
               val1 += line.price_subtotal
               for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, order.partner_id)['taxes']:
                    val += c.get('amount', 0.0)
            for c in self.pool.get('account.tax').compute_all(cr, uid, order.tax_id, order.shipping_charge, 1, False, order.partner_id)['taxes']:
                val += c.get('amount', 0.0)
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] + order.shipping_charge
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'shipping_date': fields.date('Shipping Date'),
        'tracking_number': fields.char('Tracking Number', size=50, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'product_tariff_code_id': fields.many2one('product.tariff.code', 'HS Tariff Code', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'weight': fields.float('Weight', digits=(16,2), readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'packages': fields.char('Packages #', size=20, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'shipping_charge': fields.float('Freight charges', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}),
        'tax_id': fields.many2many('account.tax', 'purchase_shipping_charge_tax', 'order_id', 'tax_id', 'Taxes', readonly=True, states={'draft': [('readonly', False)]}),

        'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line','shipping_charge','tax_id'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line','shipping_charge','tax_id'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total amount"),
    }

    def action_invoice_create(self, cr, uid, ids, context=None):
        inv_id = super(purchase_order, self).action_invoice_create(cr, uid, ids, context)
        for order in self.browse(cr, uid, ids, context=context):
            self.pool.get('account.invoice').write(cr, uid, [inv_id],{
                'product_tariff_code_id':order.product_tariff_code_id.id or False,
                'tracking_number':order.tracking_number,
                'weight':order.weight,
                'packages': order.packages,
                'tax_id': [(4, tax.id) for tax in order.tax_id],
                'shipping_charge': order.shipping_charge,
            })
        return inv_id

purchase_order()

class purchase_order_line(osv.osv):
    _inherit = "purchase.order.line"

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):

        result = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order, fiscal_position_id, date_planned, name, price_unit, context)

        res_partner = self.pool.get('res.partner')
        partner = res_partner.browse(cr, uid, partner_id)
        account_tax = self.pool.get('account.tax')
        account_fiscal_position = self.pool.get('account.fiscal.position')
        if partner.tax_ids:
            taxes = account_tax.browse(cr, uid, map(lambda x: x.id,partner.tax_ids))
            fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
            taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
            result['value']['taxes_id'] = taxes_ids
        return result