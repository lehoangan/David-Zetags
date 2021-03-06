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

import openerp
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
        'include_tax': fields.boolean('Include Tax'),
    }

    def onchange_include_tax(self, cr, uid, ids, include_tax, order_line, context):
        if not include_tax or not order_line:
            return {'value': {}}
        ait_obj = self.pool.get('account.tax')
        ail_obi = self.pool.get('purchase.order.line')

        for line in order_line:
            if line[0] != 0:
                ivl = ail_obi.browse(cr, uid, line[1], context)
                new_tax_ids = []
                old_tax_ids = []
                for tax in ivl.taxes_id:
                    if not tax.price_include and tax.amount:
                        tax_ids = ait_obj.search(cr, uid, [('type_tax_use', 'in', (tax.type_tax_use, 'all')),
                                                 ('type', '=', tax.type),
                                                ('price_include', '=', True),
                                                 ('amount', '=', tax.amount),
                                                 ('company_id', '=', tax.company_id and tax.company_id.id or False)])
                        if not tax_ids:
                            raise openerp.exceptions.Warning(_('You must define tax include %s first.'%(tax.amount*100)))
                        new_tax_ids.append(tax_ids[0])
                        old_tax_ids.append(tax.id)
                if new_tax_ids:
                    amount_tax = ivl.price_unit
                    for tax in self.pool.get('account.tax').compute_all(cr, uid, ait_obj.browse(cr, uid, old_tax_ids), \
                                                                        ivl.price_unit, 1, False, ivl.order_id.partner_id)['taxes']:
                        amount_tax += tax['amount']
                    ivl.write({'taxes_id': [(6, 0, new_tax_ids)], 'price_unit': amount_tax})
            else:
                origin_tax_ids = line[2].get('taxes_id', [])
                new_tax_ids = []
                old_tax_ids = []
                if origin_tax_ids:
                    for taxs in origin_tax_ids:
                        for tax_id in taxs[2]:
                            tax = ait_obj.browse(cr, uid, tax_id)
                            if not tax.price_include and tax.amount:
                                tax_ids = ait_obj.search(cr, uid, [('type_tax_use', 'in', (tax.type_tax_use, 'all')),
                                                         ('type', '=', tax.type),
                                                         ('price_include', '=', True),
                                                         ('amount', '=', tax.amount),
                                                         ('company_id', '=', tax.company_id and tax.company_id.id or False)])
                                if not tax_ids:
                                    raise openerp.exceptions.Warning(_('You must define tax include %s first.'%(tax.amount*100)))
                                new_tax_ids.append(tax_ids[0])
                                old_tax_ids.append(tax_id)
                    if new_tax_ids:
                        line[2]['taxes_id'] = [[6, False, new_tax_ids]]

                    amount_tax = line[2].get('price_unit', 0)
                    for tax in self.pool.get('account.tax').compute_all(cr, uid, ait_obj.browse(cr, uid, old_tax_ids), \
                                                                        line[2].get('price_unit', 0), 1, False, False)['taxes']:
                        amount_tax += tax['amount']
                    line[2]['price_unit'] = amount_tax

        return {'value': {'order_line': order_line}}

    def onchange_partner_id(self, cr, uid, ids, partner_id):
        result = super(purchase_order, self).onchange_partner_id(cr, uid, ids, partner_id)
        if partner_id:
            part = self.pool.get('res.partner').browse(cr, uid, partner_id)
            result['value'].update({'tax_id': [tax.id for tax in part.tax_ids] or [],})
        return result

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
            taxes_id = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
            result['value']['taxes_id'] = taxes_id
        return result

    def _amount_line_tax(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            if line.order_id.include_tax:
                res[line.id] = cur_obj.round(cr, uid, cur, taxes['total_included'])
            else:
                res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    _columns = {
        'price_subtotaltax': fields.function(_amount_line_tax, string='Amount', type="float",
            digits_compute= dp.get_precision('Account')),
    }