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

AVAILABLE_STATES = [
            ('NEW', 'NEW'),
            ('GOODS_REQUIRED', 'GOODS REQUIRED'),
            ('MANUFACTURE_REQUIRED', 'MANUFACTURE REQUIRED'),
            ('ALLOCATED', 'ALLOCATED'),
            ('AWAITING_PAYMENT', 'AWAITING PAYMENT'),
            ]

class sale_order_stage(osv.osv):
    _name = "sale.order.stage"
    _description = "Stage of Sale Order"
    _rec_name = 'name'
    _order = "sequence"

    _columns = {
        'name': fields.char('Stage Name', size=64, required=True, translate=True),
        'sequence': fields.integer('Sequence', help="Used to order stages. Lower is better.", required=True),
        'case_default': fields.boolean('Default to New Sales Order',
                        help="If you check this field, this stage will be proposed by default on each sales team. It will not assign this stage to existing teams."),
        'fold': fields.boolean('Fold by Default'),
    }

    _defaults = {
        'sequence': lambda *args: 1,
        'fold': False,
        'case_default': True,
    }
sale_order_stage()
 
class sale_order(osv.osv):
    _inherit = "sale.order"
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'balance': 0.0
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
            for c in self.pool.get('account.tax').compute_all(cr, uid, order.tax_id, order.shipping_charge, 1, False, order.partner_id)['taxes']:
                val += c.get('amount', 0.0)

            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] + order.shipping_charge
            
            res[order.id]['balance'] = res[order.id]['amount_total']
            for line in order.prepayment_lines:
                res[order.id]['balance'] -= line.amount 
        return res
    
    def _get_amount_deposit(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = 0
            for line in order.prepayment_lines:
                res[order.id] += line.amount
        return res
    
    def _get_order_from_deposit(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.prepayment').browse(cr, uid, ids, context=context):
            result[line.sale_id.id] = True
        return result.keys()
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    
    _columns = {
        'country_id1':fields.related('partner_id', 'country_id', string='Country', type='many2one', relation='res.country'),
        'image': fields.related('country_id1', 'flag', string='Image', type='boolean'),
        'country_id2':fields.related('company_id', 'country_id', string='Country', type='many2one', relation='res.country'),
        'image_control': fields.related('country_id2', 'flag', string='Flag', type='boolean'),
        'color': fields.integer('Color Index'),
        'order_status': fields.selection([
            ('NEW', 'NEW'),
            ('GOODS_REQUIRED', 'GOODS REQUIRED'),
            ('MANUFACTURE_REQUIRED', 'MANUFACTURE REQUIRED'),
            ('ALLOCATED', 'ALLOCATED'),
            ('AWAITING_PAYMENT', 'AWAITING PAYMENT'),
            ], 'Order Status', readonly=False, track_visibility='onchange'),
        'stage_id': fields.many2one('sale.order.stage', 'Order Status', track_visibility='onchange', select=True),
        
        #Thanh: CHange status named Quotation to Pro fomal invoice
        'state': fields.selection([
            ('draft', 'Draft Pro Forma Invoice'),
            ('sent', 'Pro Forma Invoice Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status', readonly=True, track_visibility='onchange',
            help="Gives the status of the Pro Forma Invoice or sales order. \nThe exception status is automatically set when a cancel operation occurs in the processing of a document linked to the sales order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),
            
        'partner_contact_id': fields.many2one('res.partner', 'Contact', readonly=True, required=False, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),

        'shipping_charge': fields.float('Shipping Charge', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}),
        'tax_id': fields.many2many('account.tax', 'shipping_charge_tax', 'order_id', 'tax_id', 'Taxes', readonly=True, states={'draft': [('readonly', False)]}),
        'delivery_account_id': fields.many2one('account.account', 'Delivery Account', readonly=True, states={'draft': [('readonly', False)]}, domain="[('type','!=','view')]"),
        'shipping_date': fields.date('Shipping Date'),
        'deposit_paid': fields.function(_get_amount_deposit, digits_compute=dp.get_precision('Account'), string='Deposit Paid',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['prepayment_lines'], 10),
                'sale.order.prepayment': (_get_order_from_deposit, ['amount'], 10),
            }),
        
        'balance': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Balance',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line','prepayment_lines','shipping_charge'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                'sale.order.prepayment': (_get_order_from_deposit, ['amount'], 10),
            },
            multi='sums', track_visibility='always'),
                
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line','shipping_charge','tax_id'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
                
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line','shipping_charge','tax_id'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
        
        'tracking_number': fields.char('Tracking Number', size=50, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'product_tariff_code_id': fields.many2one('product.tariff.code', 'HS Tariff Code', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'weight': fields.float('Weight', digits=(16,2), readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'packages': fields.char('Packages #', size=20, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        
        'prepayment_lines': fields.one2many('sale.order.prepayment', 'sale_id', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        # 'alert': fields.related('partner_id', 'alert', string='Alert'),
    }
    
    def _get_default_stage_id(self, cr, uid, context=None):
        """ Gives default stage_id """
        stage_ids = self.pool.get('sale.order.stage').search(cr, uid, [('case_default','=',True)])
        return stage_ids and stage_ids[0] or False
    
    _defaults = {
        'name': '/',
        'order_policy': 'manual',
        'stage_id': _get_default_stage_id,
        'color': 0,
    }
    
    def _read_group_order_status(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        access_rights_uid = access_rights_uid or uid
        stage_obj = self.pool.get('sale.order.stage')
        order = stage_obj._order
        # lame hack to allow reverting search, should just work in the trivial case
        if read_group_order == 'stage_id desc':
            order = "%s desc" % order
        search_domain = []
        stage_ids = stage_obj._search(cr, uid, search_domain, order=order, access_rights_uid=access_rights_uid, context=context)
        result = stage_obj.name_get(cr, access_rights_uid, stage_ids, context=context)
        # restore order of the search
        result.sort(lambda x,y: cmp(stage_ids.index(x[0]), stage_ids.index(y[0])))

        fold = {}
        for stage in stage_obj.browse(cr, access_rights_uid, stage_ids, context=context):
            fold[stage.id] = stage.fold or False
        return result, fold
    
    _group_by_full = {
        'stage_id': _read_group_order_status
    }
    
    #Thanh: Get customized Template print
    def print_pf_invoice(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        data = self.browse(cr, uid, ids[0])
        datas = {
                 'model': 'sale.order',
                 'ids': ids,
                 'form': self.read(cr, uid, ids[0], context=context),
        }

        return {'type': 'ir.actions.report.xml',
                'report_name': 'report_sale_order',
                'datas': datas, 'nodestroy': True,
                'name': '%s/%s/%s'%(data.name.split(' ', 1)[0], data.partner_id.name.split(' ', 1)[0], data.partner_id.country_id.code or '')}
    
    def print_picking_slip(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        data = self.browse(cr, uid, ids[0])
        datas = {
                 'model': 'sale.order',
                 'ids': ids,
                 'form': self.read(cr, uid, ids[0], context=context),
        }
        return {'type': 'ir.actions.report.xml', 'report_name': 'report_picking_slip', 'datas': datas, 'nodestroy': True,
                'name': '%s/%s/%s'%(data.name.split(' ', 1)[0], data.partner_id.name.split(' ', 1)[0], data.partner_id.country_id.code or '')}
    
    def print_shipping_invoice(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        data = self.browse(cr, uid, ids[0])
        datas = {
                 'model': 'sale.order',
                 'ids': ids,
                 'form': self.read(cr, uid, ids[0], context=context),
        }
        return {'type': 'ir.actions.report.xml', 'report_name': 'report_shipping_invoice', 'datas': datas, 'nodestroy': True,
                'name': '%s/%s/%s'%(data.name.split(' ', 1)[0], data.partner_id.name.split(' ', 1)[0], data.partner_id.country_id.code or '')}
    
    def _check_name(self, cr, uid, ids, context=None):
        for sale in self.browse(cr, uid, ids, context=context):
            if sale.name:
                exist_ids = self.search(cr, uid, [('id','!=',sale.id),('name','=',sale.name),('company_id','=',sale.shop_id.company_id.id)])
                if len(exist_ids):
                    raise osv.except_osv(_('Error!'), _("Sale Order Reference '%s' is exist. Please select other Number."%(sale.name)))
        return True

    _constraints = [
        (_check_name, 'Order Reference must be unique per Company!', ['name']),
    ]
    
    _sql_constraints = [
        ('name_uniq', 'Check(1=1)', 'Order Reference must be unique per Company!'),
    ]
    
    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False,  'payment_term': False, 'fiscal_position': False}}

        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
        pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
        payment_term = part.property_payment_term and part.property_payment_term.id or False
        fiscal_position = part.property_account_position and part.property_account_position.id or False
        dedicated_salesman = part.user_id and part.user_id.id or uid
        val = {
            #Thanh: Add contact
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'payment_term': payment_term,
            'fiscal_position': fiscal_position,
            'user_id': dedicated_salesman,
            'carrier_id': part.default_shipping_id.id or False,
            'tax_id': [tax.id for tax in part.tax_ids] or [],
        }
        if pricelist:
            val['pricelist_id'] = pricelist

        val.update({'tax_id': [tax.id for tax in part.tax_ids] or [],})
        if part.country_id and part.country_id.company_id:
            user_company = self.pool.get('res.users').browse(cr, uid, uid).company_id
            if user_company != part.country_id.company_id:
                return {'value': {'partner_id': False}, 'warning': {
                                                                    'title': _("Access Error"),
                                                                    'message': _("You must login to %s to invoice this customer."%part.country_id.company_id.name),
                                                                    },}
        return {'value': val}
    
    def onchange_partner_contact_id(self, cr, uid, ids, partner_contact_id, context=None):
        value = {}
        if partner_contact_id:
            addr = self.pool.get('res.partner').address_get(cr, uid, [partner_contact_id], ['delivery', 'invoice', 'contact'])
            if not addr['delivery']:
                value.update({'partner_shipping_id':partner_contact_id})
        return {'value':value}
    
    def onchange_carrier_id(self, cr, uid, ids, carrier_id, context=None):
        value = {}
        if carrier_id:
            carrier = self.pool.get('delivery.carrier').browse(cr, uid, carrier_id)
            delivery_account_id = carrier.account_id.id or False
            value.update({'delivery_account_id':delivery_account_id})
        return {'value':value}
    
    def delivery_set(self, cr, uid, ids, context=None):
        order_obj = self.pool.get('sale.order')
        line_obj = self.pool.get('sale.order.line')
        grid_obj = self.pool.get('delivery.grid')
        carrier_obj = self.pool.get('delivery.carrier')
        acc_fp_obj = self.pool.get('account.fiscal.position')
        for order in self.browse(cr, uid, ids, context=context):
            grid_id = carrier_obj.grid_get(cr, uid, [order.carrier_id.id], order.partner_shipping_id.id)
            if not grid_id:
                raise osv.except_osv(_('No Grid Available!'), _('No grid matching for this carrier!'))

            if not order.state in ('draft'):
                raise osv.except_osv(_('Order not in Draft State!'), _('The order state have to be draft to add delivery lines.'))

            grid = grid_obj.browse(cr, uid, grid_id, context=context)

#             taxes = grid.carrier_id.product_id.taxes_id
#             fpos = order.fiscal_position or False
#             taxes_ids = acc_fp_obj.map_tax(cr, uid, fpos, taxes)
#             #create the sale order line
#             line_obj.create(cr, uid, {
#                 'order_id': order.id,
#                 'name': grid.carrier_id.name,
#                 'product_uom_qty': 1,
#                 'product_uom': grid.carrier_id.product_id.uom_id.id,
#                 'product_id': grid.carrier_id.product_id.id,
#                 'price_unit': grid_obj.get_price(cr, uid, grid.id, order, time.strftime('%Y-%m-%d'), context),
#                 'tax_id': [(6,0,taxes_ids)],
#                 'type': 'make_to_stock'
#             })
            shipping_charge = grid_obj.get_price(cr, uid, grid.id, order, time.strftime('%Y-%m-%d'), context)
            self.write(cr, uid, ids, {'shipping_charge': shipping_charge}, context=context)
        return True
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        if context is None:
            context = {}
        journal_ids = self.pool.get('account.journal').search(cr, uid,
            [('type', '=', 'sale'), ('company_id', '=', order.company_id.id)],
            limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        
        prepayment_lines = []
        for line in order.prepayment_lines:
            prepayment_lines.append((0,0,{'journal_id': line.journal_id.id,
                                          'date': line.date,
                                          'amount': line.amount,
                                          'company_id': line.company_id.id}))
        invoice_vals = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': order.partner_id.property_account_receivable.id,
            'partner_id': order.partner_id.id,
            'journal_id': journal_ids[0],
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': order.payment_term and order.payment_term.id or False,
            'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
            'date_invoice': order.shipping_date or context.get('date_invoice', False),
            'company_id': order.partner_id.company_id.id,
            'user_id': order.user_id and order.user_id.id or False,
            
            #Thanh: Add more fields
            'partner_contact_id': order.partner_contact_id.id or False,
            'shipping_charge': order.shipping_charge,
            'tax_id': [(4, tax.id) for tax in order.tax_id],
            'delivery_account_id': order.delivery_account_id.id or False,
            'product_tariff_code_id':order.product_tariff_code_id.id or False,
            'tracking_number':order.tracking_number,
            'weight':order.weight,
            'packages': order.packages,
            'prepayment_lines': prepayment_lines,
        }

        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals

    def write_partner_company_to_user(self, cr, uid, order, context=None):
        user_obj = self.pool.get('res.users').browse(cr, uid, uid)
        #anlee: Dont need switch company
        old_company_id = False
        if  order.partner_id.company_id and user_obj.company_id != order.partner_id.company_id and user_obj.non_switch_company:
            company_ids = [comp.id for comp in user_obj.company_ids]
            if order.partner_id.company_id.id in company_ids:
                old_company_id = user_obj.company_id.id
                user_obj.write({'company_id': order.partner_id.company_id.id})
        #anlee: END
        return old_company_id
    
    def _make_invoice(self, cr, uid, order, lines, context=None):
        inv_id = super(sale_order, self)._make_invoice(cr, uid, order, lines, context=context)
        #Thanh: Change prefix of Invoice Number
        company_ids = self.pool.get('res.company').search(cr, uid, [], context=context) + [False]
        sequence_ids = self.pool.get('ir.sequence').search(cr, uid, ['&', ('code', '=', 'sale.order'), ('company_id', 'in', company_ids)])
        number = order.name
        if sequence_ids and sequence_ids[0]:
            prefix = self.pool.get('ir.sequence').browse(cr, uid, sequence_ids[0]).prefix
            if prefix:
                number = number.replace(prefix,'IN')
        cr.execute("update account_invoice set number='%s' where id=%s"%(number,inv_id))
        return inv_id

    def action_invoice_create(self, cr, uid, ids, grouped=False, states=None, date_invoice = False, context=None):
        order = self.browse(cr, uid, ids[0])
        old_company_id = self.write_partner_company_to_user(cr, uid, order, context)
        res = super(sale_order, self). action_invoice_create(cr, uid, ids, grouped, states, date_invoice, context)
        #anlee:  revert company for user
        if old_company_id:
            self.pool.get('res.users').write(cr, uid, [uid],{'company_id': old_company_id})
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        sale_orders = self.read(cr, uid, ids, ['state','picking_ids'], context=context)
        unlink_ids = []
        for s in sale_orders:
            if s['state'] in ['draft', 'cancel']:
                unlink_ids.append(s['id'])
            if len(s['picking_ids']):
                raise osv.except_osv(_('Invalid Action!'), _('In order to delete a confirmed sales order, you must cancel it.\nTo do so, you must first cancel related picking for delivery orders.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
    def action_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        if context is None:
            context = {}
        proc_obj = self.pool.get('procurement.order')
        for sale in self.browse(cr, uid, ids, context=context):
            for pick in sale.picking_ids:
                if pick.state in ('done'):
                    raise osv.except_osv(
                        _('Cannot cancel sales order!'),
                        _('You must first cancel all delivery order(s) attached to this sales order.'))
                if pick.state == 'cancel':
                    for mov in pick.move_lines:
                        proc_ids = proc_obj.search(cr, uid, [('move_id', '=', mov.id)])
                        if proc_ids:
                            for proc in proc_ids:
                                wf_service.trg_validate(uid, 'procurement.order', proc, 'button_check', cr)
            for r in self.read(cr, uid, ids, ['picking_ids']):
                for pick in r['picking_ids']:
                    wf_service.trg_validate(uid, 'stock.picking', pick, 'button_cancel', cr)
                    sql ='''
                        DELETE FROM stock_move WHERE picking_id = %s
                    '''%(pick)
                    cr.execute(sql)
                    sql ='''
                        DELETE FROM stock_picking WHERE id =%s
                    '''%(pick)
                    cr.execute(sql)
        return super(sale_order, self).action_cancel(cr, uid, ids, context=context)
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('shipping_date',False) and vals['shipping_date']:
            vals.update({'date_order':vals['shipping_date']})
        return super(sale_order, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        this = self.browse(cr, uid, ids[0])
        date_order = this.shipping_date
        if vals.get('date_order',False) and this.shipping_date:
            vals.update({'date_order':this.shipping_date})
        if vals.get('shipping_date',False) and vals['shipping_date']:
            vals.update({'date_order':vals['shipping_date']})
        return super(sale_order, self).write(cr, uid, ids, vals, context=context)
    
#     def _auto_init(self, cr, context=None):
#         super(sale_order, self)._auto_init(cr, context)
#         cr.execute('''
#         UPDATE sale_order
#         SET partner_contact_id = partner_shipping_id
#         where partner_contact_id is null
#         ''')
        
sale_order()

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"

    # def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
    #     res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id, context)
    #     if not res:
    #         return res
    #
    #     uosqty = 1
    #     pu = round(line.price_unit * line.product_uom_qty / uosqty,
    #             self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Price'))
    #     res.update({'price_unit': pu,
    #                 'quantity': uosqty})
    #     return res
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        
        if context is None:
            context = {}
        result = super(sale_order_line,self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)

        #compute price base on rate of pricelist
        if pricelist and result['value'].get('price_unit'):
            rate = self.pool.get('product.pricelist').browse(cr, uid, pricelist, context).rate
            if rate:
                result['value']['price_unit'] = result['value']['price_unit'] * rate

        partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
        tax_obj = self.pool.get('account.tax')
        tax_ids = []
        name_tax = ''
        if partner.tax_ids:
            result['value']['tax_id'] = [tax.id for tax in partner.tax_ids]

        if result['value'].get('tax_id', []):
            for tax_id in result['value']['tax_id']:
                tax = tax_obj.browse(cr, uid, tax_id)
                if partner.company_id and partner.company_id != tax.company_id:
                    if not name_tax:
                        name_tax = tax.name
                    else:
                        name_tax = '%s - %s'%(name_tax, tax.name)
                else:
                    tax_ids += [tax.id]
            result['value']['tax_id'] = tax_ids
            warning = {}
            if name_tax:
                warning = {
                           'title': _('Configuration Error!'),
                           'message' : '%s is not the same company of customer. Please select other tax manual'%name_tax
                        }
            result['warning'] = warning

        if not product:
            return result
        
        res = self.pool.get('product.product').browse(cr, uid, product, context=context)

        result['value']['name'] = res.description or res.name
        if res.packaging_id:
            result['value']['name'] += '\n'+res.packaging_id.name

        return result
    
    def default_get(self, cr, uid, fields, context=None):
        result = super(sale_order_line, self).default_get(cr, uid, fields, context=context)
        if context.get('sale_order_partner_id',False):
            partner = self.pool.get('res.partner').browse(cr, uid, context['sale_order_partner_id'])
            result.update({'discount':partner.fixed_discount})
        return result
        
sale_order_line()

#Thanh: New object for Prepayment
class sale_order_prepayment(osv.osv):
    _name = "sale.order.prepayment"
    _columns = {
        'journal_id': fields.many2one('account.journal', 'Payment Method', required=True),
        'date': fields.date('Date Paid', required=True),
        'amount': fields.float('Deposit Paid', digits=(16,2), required=True),
        'sale_id': fields.many2one('sale.order', 'Order', required=True, ondelete='cascade', select=True),
        'company_id': fields.many2one('res.company', 'Company'),
    }
    _defaults = {
        'date': fields.date.context_today,
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'sale.order.prepayment', context=c),
    }
sale_order_prepayment()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
