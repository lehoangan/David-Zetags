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

# class res_partner(osv.osv):
#     _inherit = "res.partner"
#     _columns = {
#     }
#     
#     def search(self, cr, uid, args, offset=0, limit=None, order=None,
#             context=None, count=False):
#         if context is None:
#             context = {}
#         return super(res_partner, self).search(cr, uid, args, offset, limit,
#                 order, context=context, count=count)
#         
# res_partner()

class account_voucher(osv.osv):
    _inherit = "account.voucher"
    _columns = {
        'number': fields.char('Number', size=32, readonly=False),
    }
account_voucher()

class account_invoice(osv.osv):
    _inherit = "account.invoice"

    def invoice_print(self, cr, uid, ids, context=None):
        '''
        This function prints the invoice and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        self.write(cr, uid, ids, {'sent': True}, context=context)
        datas = {
             'ids': ids,
             'model': 'account.invoice',
             'form': self.read(cr, uid, ids[0], context=context)
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.invoice.zetags',
            'datas': datas,
            'nodestroy' : True
        }
    
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0
            }
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed'] + invoice.shipping_charge
        return res
    
    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()
    
    def _amount_residual(self, cr, uid, ids, name, args, context=None):
        result = super(account_invoice, self)._amount_residual(cr, uid, ids, name, args, context)
        for invoice in self.browse(cr, uid, ids, context=context):
            result[invoice.id] = 0.0
            if invoice.move_id:
                for m in invoice.move_id.line_id:
                    if m.account_id.type in ('receivable','payable'):
                        if invoice.type in ['in_invoice','out_refund'] and m.date_maturity:
                            result[invoice.id] += m.amount_residual_currency or 0.0
                        if invoice.type in ['out_invoice','in_refund'] and m.date_maturity:
                            result[invoice.id] += m.amount_residual_currency or 0.0
        return result
    
    def _get_invoice_from_line(self, cr, uid, ids, context=None):
        move = {}
        for line in self.pool.get('account.move.line').browse(cr, uid, ids, context=context):
            if line.reconcile_partial_id:
                for line2 in line.reconcile_partial_id.line_partial_ids:
                    move[line2.move_id.id] = True
            if line.reconcile_id:
                for line2 in line.reconcile_id.line_id:
                    move[line2.move_id.id] = True
        invoice_ids = []
        if move:
            invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move.keys())], context=context)
        return invoice_ids

    def _get_invoice_from_reconcile(self, cr, uid, ids, context=None):
        move = {}
        for r in self.pool.get('account.move.reconcile').browse(cr, uid, ids, context=context):
            for line in r.line_partial_ids:
                move[line.move_id.id] = True
            for line in r.line_id:
                move[line.move_id.id] = True

        invoice_ids = []
        if move:
            invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move.keys())], context=context)
        return invoice_ids
    
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
        for line in self.pool.get('account.invoice.prepayment').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()
    
    _columns = {
        'number': fields.char('Number', size=64, readonly=True),#, states={'draft':[('readonly',False)]}),
        'partner_contact_id': fields.many2one('res.partner', 'Contact', readonly=True, required=False, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]},
                                      domain="[('type', 'in', {'out_invoice': ['sale'], 'out_refund': ['sale_refund'], 'in_refund': ['purchase_refund'], 'in_invoice': ['purchase']}.get(type, [])), ('company_id', '=', company_id)]"),
        'shipping_charge': fields.float('Shipping Charge', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft':[('readonly',False)]}),
        'delivery_account_id': fields.many2one('account.account', 'Delivery Account', readonly=True, states={'draft': [('readonly', False)]}, domain="[('type','!=','view')]"),
        
        'deposit_paid': fields.function(_get_amount_deposit, digits_compute=dp.get_precision('Account'), string='Deposit Paid',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['prepayment_lines'], 10),
                'account.invoice.prepayment': (_get_order_from_deposit, ['amount'], 10),
            }),
                
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
                
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line','shipping_charge'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        
        #Thanh: Change the way computing Balance
        'residual': fields.function(_amount_residual, digits_compute=dp.get_precision('Account'), string='Balance',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line','move_id'], 50),
                'account.invoice.tax': (_get_invoice_tax, None, 50),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 50),
                'account.move.line': (_get_invoice_from_line, None, 50),
                'account.move.reconcile': (_get_invoice_from_reconcile, None, 50),
            },
            help="Remaining amount due."),
                
        'product_tariff_code_id': fields.many2one('product.tariff.code', 'HS Tariff Code'),
        'tracking_number': fields.char('Tracking Number', size=50),
        'weight': fields.float('Weight', digits=(16,2)),
        'packages': fields.char('Packages #', size=20),
        
        'prepayment_lines': fields.one2many('account.invoice.prepayment', 'invoice_id', readonly=True, states={'draft': [('readonly', False)]}),
    }
    
#     def _check_name(self, cr, uid, ids, context=None):
#         for inv in self.browse(cr, uid, ids, context=context):
#             if inv.number:
#                 exist_ids = self.search(cr, uid, [('id','!=',inv.id),
#                                                   ('number','=',inv.number),
#                                                   ('type','=',inv.type),
#                                                   ('company_id','=',inv.company_id.id),
#                                                   ])
#                 if len(exist_ids):
#                     raise osv.except_osv(_('Error!'), _("Invoice Number '%s' is exist. Please select other Number."%(inv.number)))
#         return True
# 
#     _constraints = [
#         (_check_name, 'Invoice Number must be unique per Company!', ['number']),
#     ]
    
    _sql_constraints = [
        ('number_uniq', 'Check(1=1)', 'Invoice Number must be unique per Company!'),
    ]

    def button_reset_taxes(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ait_obj = self.pool.get('account.invoice.tax')
        for id in ids:
            cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is False", (id,))
            inv = self.browse(cr, uid, id, context=ctx)
            old_company_id = self.pool.get('sale.order').write_partner_company_to_user(cr, uid, inv, context)
            partner = inv.partner_id
            if partner.lang:
                ctx.update({'lang': partner.lang})
            for taxe in ait_obj.compute(cr, uid, id, context=ctx).values():
                ait_obj.create(cr, uid, taxe)
            #anlee:  revert company for user
            if old_company_id:
                self.pool.get('res.users').write(cr, uid, [uid],{'company_id': old_company_id})
        # Update the stored value (fields.function), so we write to trigger recompute
        self.pool.get('account.invoice').write(cr, uid, ids, {'invoice_line':[]}, context=ctx)
        return True

    #Thanh: Dont get currency from Journal
    def onchange_journal_id(self, cr, uid, ids, journal_id=False, context=None):
        result = {}
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
            currency_id = journal.currency and journal.currency.id or journal.company_id.currency_id.id
            company_id = journal.company_id.id
            result = {'value': {
#                     'currency_id': currency_id,
                    'company_id': company_id,
                    }
                }
        return result
    #Thanh: Dont get currency from Journal
    
    #Thanh: Get currency from Partner's sale pricelist
    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        result = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice=date_invoice, payment_term=payment_term, partner_bank_id=partner_bank_id, company_id=company_id)
        result['value'].update({'partner_contact_id':partner_id or False})
        if type in ('out_refund') and partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if partner.property_product_pricelist:
                result['value'].update({'currency_id':partner.property_product_pricelist.currency_id.id or False})
        return result
    #Thanh: Get currency from Partner's sale pricelist
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoices = self.read(cr, uid, ids, ['state','number'], context=context)
        unlink_ids = []

        for t in invoices:
            if t['state'] not in ('draft', 'cancel'):
                raise openerp.exceptions.Warning(_('You cannot delete an invoice which is not draft or cancelled. You should refund it instead.'))
            #Thanh: Check number instead of internal_number of original module
            # elif t['number']:#t['internal_number']
            #     raise openerp.exceptions.Warning(_('You cannot delete an invoice after it has been validated (and received a number).  You can set it back to "Draft" state and modify its content, then re-confirm it.'))
            else:
                unlink_ids.append(t['id'])

        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        account_move_obj = self.pool.get('account.move')
        voucher_obj = self.pool.get('account.voucher')
        invoices = self.read(cr, uid, ids, ['move_id', 'payment_ids'])
        move_ids = [] # ones that we will need to remove
        for i in invoices:
            if i['move_id']:
                move_ids.append(i['move_id'][0])
            if i['payment_ids']:
                #Thanh: Remove Payment Firstly
                #Thanh: Get all related payment and then unlink them first
                cr.execute("select id from account_voucher where move_id in (%s)"%(','.join(map(str, i['payment_ids']))))
                voucher_ids = [x[0] for x in cr.fetchall()]
                if voucher_ids:
                    voucher_obj.cancel_voucher(cr, uid, voucher_ids, context=context)
                # account_move_line_obj = self.pool.get('account.move.line')
                # pay_ids = account_move_line_obj.browse(cr, uid, i['payment_ids'])
                # for move_line in pay_ids:
                #     if move_line.reconcile_partial_id and move_line.reconcile_partial_id.line_partial_ids:
                #         raise osv.except_osv(_('Error!'), _('You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))

        # First, set the invoices as cancelled and detach the move ids
        self.write(cr, uid, ids, {'state':'cancel', 'move_id':False})
        if move_ids:
            # second, invalidate the move(s)
            account_move_obj.button_cancel(cr, uid, move_ids, context=context)
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            account_move_obj.unlink(cr, uid, move_ids, context=context)
        self._log_event(cr, uid, ids, -1.0, 'Cancel Invoice')
        return True
    
    def action_move_create(self, cr, uid, ids, context=None):
        """Creates invoice related analytics and financial move lines"""
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        payment_term_obj = self.pool.get('account.payment.term')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        if context is None:
            context = {}
        for inv in self.browse(cr, uid, ids, context=context):
            old_company_id = self.pool.get('sale.order').write_partner_company_to_user(cr, uid, inv, context)
            if not inv.journal_id.sequence_id:
                raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line:
                raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = context.copy()
            ctx.update({'lang': inv.partner_id.lang})
            if not inv.date_invoice:
                self.write(cr, uid, [inv.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
            company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
            # create the analytical lines
            # one move line per invoice line
            iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)
            # check if taxes are all computed
            compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
            self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)

            # I disabled the check_total feature
            group_check_total_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
            group_check_total = self.pool.get('res.groups').browse(cr, uid, group_check_total_id, context=context)
            if group_check_total and uid in [x.id for x in group_check_total.users]:
                if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0)):
                    raise osv.except_osv(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise osv.except_osv(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

            # one move line per tax line
            iml += ait_obj.move_line_get(cr, uid, inv.id)

            entry_type = ''
            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
                entry_type = 'journal_pur_voucher'
                if inv.type == 'in_refund':
                    entry_type = 'cont_voucher'
            else:
                ref = self._convert_ref(cr, uid, inv.number)
                entry_type = 'journal_sale_vou'
                if inv.type == 'out_refund':
                    entry_type = 'cont_voucher'

            diff_currency_p = inv.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml, context=ctx)
            acc_id = inv.account_id.id

            name = inv['name'] or inv['supplier_invoice_number'] or '/'
            totlines = False
            if inv.payment_term:
                totlines = payment_term_obj.compute(cr,
                        uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
            if totlines:
                res_amount_currency = total_currency
                i = 0
                ctx.update({'date': inv.date_invoice})
                for t in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                                and amount_currency or False,
                        'currency_id': diff_currency_p \
                                and inv.currency_id.id or False,
                        'ref': ref,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity': inv.date_due or False,
                    'amount_currency': diff_currency_p \
                            and total_currency or False,
                    'currency_id': diff_currency_p \
                            and inv.currency_id.id or False,
                    'ref': ref
            })

            date = inv.date_invoice or time.strftime('%Y-%m-%d')

            part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)

            line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part.id, date, context=ctx)),iml)

            line = self.group_lines(cr, uid, iml, line, inv)

            journal_id = inv.journal_id.id
            journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.centralisation:
                raise osv.except_osv(_('User Error!'),
                        _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = self.finalize_invoice_move_lines(cr, uid, inv, line)
            
            #Thanh: create Move for Shipping Charge Entry
            shipping_moves = []
            shipping_amount = 0.0
            if inv.shipping_charge and inv.type in ['out_invoice','out_refund']:
                if not inv.delivery_account_id:
                    raise osv.except_osv(_('Delivery Account Missing!'),
                        _('Please select Delivery Account!'))
                
                ctx.update({'date': inv.date_invoice})
                company_amount_currency = inv.shipping_charge
                shipping_charge_currency = inv.shipping_charge
                if inv.currency_id.id != company_currency:
                    company_amount_currency = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, inv.shipping_charge, context=ctx)
                    
                if inv.type in ['out_invoice']:
                    shipping_charge_currency = -1 * shipping_charge_currency
                if inv.type in ['out_refund']:
                    shipping_charge_currency = shipping_charge_currency
                    
                shipping_moves += [(0,0, {
                        'name': inv.delivery_account_id.name,
                        'product_id': False,
                        'quantity': False,
                        'ref': name,
                        'date': inv.date_invoice,
                        'debit': inv.type in ['out_refund'] and company_amount_currency or 0.0,
                        'credit': inv.type in ['out_invoice'] and company_amount_currency or 0.0,
                        'account_id': inv.delivery_account_id.id,
                        'amount_currency': diff_currency_p \
                                and shipping_charge_currency or False,
                        'currency_id': diff_currency_p \
                                and inv.currency_id.id or False,
                        })]
            line += shipping_moves
            #Thanh: create Move for Shipping Charge Entry
            
            #Thanh: update Invoice Entry
            if len(shipping_moves):
                for move_line in line:
                    if inv.account_id.id == move_line[2]['account_id']:
                        if move_line[2]['debit']:
                            for shipping_move in shipping_moves:
                                move_line[2]['debit'] += shipping_move[2]['credit']
                                move_line[2]['debit'] -= shipping_move[2]['debit']
                        else:
                            for shipping_move in shipping_moves:
                                move_line[2]['credit'] += shipping_move[2]['debit']
                                move_line[2]['credit'] -= shipping_move[2]['credit']
                        
                        if inv.currency_id.id != company_currency:
                            amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, move_line[2]['debit'] or move_line[2]['credit'], context=ctx)
                            
                            if move_line[2]['debit'] > 0:
                                amount_currency = abs(amount_currency)
                            if move_line[2]['credit'] > 0:
                                amount_currency = -1 * amount_currency
                            
                            move_line[2]['amount_currency'] = amount_currency
            #Thanh: update Invoice Entry
            
            move = {
                #Thanh: Pass invoice number to Journal
                'name': inv.number or '/',
                #Thanh: Pass invoice number to Journal
                
                'ref': inv.reference and inv.reference or inv.name,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'narration': inv.comment,
                'company_id': inv.company_id.id,
            }
            period_id = inv.period_id and inv.period_id.id or False
            ctx.update(company_id=inv.company_id.id,
                       account_period_prefer_normal=True)
            if not period_id:
                period_ids = period_obj.find(cr, uid, inv.date_invoice, context=ctx)
                period_id = period_ids and period_ids[0] or False
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id

            ctx.update(invoice=inv)
            move_id = move_obj.create(cr, uid, move, context=ctx)
            
            #Thanh: Reconciliation Extend Move Line
            cr.execute("SELECT id FROM account_move_line WHERE move_id=%s AND account_id=%s"%(move_id, inv.account_id.id))
            rec_ids = [x[0] for x in cr.fetchall()]
            if rec_ids:
                move_line_pool.reconcile_partial(cr, uid, rec_ids)
            #Thanh: Reconciliation Extend Move Line
            
            new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
            # make the invoice point to that move
            self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name, 'supplier_invoice_number':inv.number}, context=ctx)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move_obj.post(cr, uid, [move_id], context=ctx)
            
            #Thanh: Update Journal number for Invoice number except Customer Invoice
            if inv.type not in ('out_invoice') or inv.number in (False, '/'):
                cr.execute('''
                    UPDATE account_invoice
                    SET number='%s'
                    WHERE id = %s
                    '''%(new_move_name,inv.id))
            #Thanh: Update Journal number for Invoice number except Customer Invoice
            
            #Thanh: Update Move name to Sale Order
            cr.execute('''
            SELECT name FROM sale_order
            WHERE id in (select order_id from sale_order_invoice_rel where invoice_id=%s)
            '''%(inv.id))
            sale = cr.fetchone()
            if sale and sale[0]:
                company_ids = self.pool.get('res.company').search(cr, uid, [], context=context) + [False]
                sequence_ids = self.pool.get('ir.sequence').search(cr, uid, ['&', ('code', '=', 'sale.order'), ('company_id', 'in', company_ids)])
                number = sale[0]
                if sequence_ids and sequence_ids[0]:
                    prefix = self.pool.get('ir.sequence').browse(cr, uid, sequence_ids[0]).prefix
                    if prefix:
                        number = number.replace(prefix,'SO')
                        cr.execute('''
                        UPDATE sale_order
                        SET name='%s'
                        WHERE id in (select order_id from sale_order_invoice_rel where invoice_id=%s)
                        '''%(number,inv.id))
            #Thanh: Update Move name to Sale Order
            if old_company_id:
                self.pool.get('res.users').write(cr, uid, [uid],{'company_id': old_company_id})
            
        self._log_event(cr, uid, ids)
        self.pay_invoice(cr, uid, ids, context)
        return True
    
    def pay_invoice(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        voucher = self.pool.get('account.voucher')
            
        fields_list = ['comment', 'line_cr_ids', 'is_multi_currency', 'reference', 'line_dr_ids', 'company_id', 'currency_id', 
                         'shop_id', 'narration', 'partner_id', 'payment_rate_currency_id', 'paid_amount_in_company_currency', 
                         'writeoff_acc_id', 'state', 'pre_line', 'type', 'payment_option', 'account_id', 'period_id', 'date', 
                         'reference_number', 'payment_rate', 'name', 'writeoff_amount', 'analytic_id', 'journal_id', 'amount']
        for inv in self.browse(cr, uid, ids):
            for prepaid in inv.prepayment_lines:
                voucher_context = {
                    'payment_expected_currency': inv.currency_id.id,
                    'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                    'default_amount': inv.type in ('out_refund', 'in_refund') and -prepaid.amount or prepaid.amount,
                    'default_reference': inv.name,
                    'close_after_process': True,
                    'invoice_type': inv.type,
                    'invoice_id': inv.id,
                    'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                    'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                }
                vals = voucher.default_get(cr, uid, fields_list, context=voucher_context)
                res = voucher.onchange_journal(cr, uid, [], prepaid.journal_id.id, 
                                               False, False, inv.partner_id.id, 
                                               prepaid.date, 
                                               prepaid.amount, 
                                               vals['type'], vals['company_id'], context=voucher_context)
                vals = dict(vals.items() + res['value'].items())
                line_cr_ids = []
                line_dr_ids = []
                for line in vals['line_cr_ids']:
                    line_cr_ids.append((0,0,line))
                for line in vals['line_dr_ids']:
                    line_dr_ids.append((0,0,line))
                vals['line_cr_ids'] = line_cr_ids
                vals['line_dr_ids'] = line_dr_ids
                vals.update({'journal_id': prepaid.journal_id.id, 'date':prepaid.date})
                if len(line_cr_ids) or len(line_dr_ids):
                    voucher_id = voucher.create(cr, uid, vals)
                    if voucher_id:
                        wf_service.trg_validate(uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)
                    else:
                        raise osv.except_osv(_('Error!'), _('Cannot create Payment!'))
        return True
    
    #Thanh: New Function to create refund paymentlines
    def _refund_cleanup_prepayment_lines(self, cr, uid, lines, context=None):
        clean_lines = []
        for line in lines:
            clean_line = {}
            for field in line._all_columns.keys():
                if line._all_columns[field].column._type == 'many2one':
                    clean_line[field] = line[field].id
                elif line._all_columns[field].column._type not in ['many2many','one2many']:
                    clean_line[field] = line[field]
            clean_lines.append(clean_line)
        return map(lambda x: (0,0,x), clean_lines)
    #Thanh: New Function to create refund paymentlines
    
    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, context=None):
        invoice_data = super(account_invoice, self)._prepare_refund(cr, uid, invoice, date=date, period_id=period_id, description=description, journal_id=journal_id, context=context)
        
        #Thanh: Update for more custom Fields
        prepayment_lines = self._refund_cleanup_prepayment_lines(cr, uid, invoice.prepayment_lines, context=context)
        
        invoice_data.update({
            'shipping_charge': invoice.shipping_charge,
            'delivery_account_id': invoice.delivery_account_id.id or False,
            'product_tariff_code_id': invoice.product_tariff_code_id.id or False,
            'tracking_number': invoice.tracking_number,
            'weight': invoice.weight,
            'packages': invoice.packages,
            'prepayment_lines': prepayment_lines,
        })
        #Thanh: Update for more custom Fields

        return invoice_data
    
    def _auto_init(self, cr, context=None):
        super(account_invoice, self)._auto_init(cr, context)
        cr.execute('''
        UPDATE ir_act_report_xml
        SET attachment_use = False
        where model='account.invoice'
        ''')
        
        cr.execute('''
        UPDATE account_invoice
        SET partner_contact_id = partner_id
        where partner_contact_id is null
        ''')
account_invoice()

#Thanh: New object for Prepayment
class account_invoice_prepayment(osv.osv):
    _name = "account.invoice.prepayment"
    _columns = {
        'journal_id': fields.many2one('account.journal', 'Payment Method', required=True),
        'date': fields.date('Date Paid', required=True),
        'amount': fields.float('Deposit Paid', digits=(16,2), required=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', required=True, ondelete='cascade', select=True),
        'company_id': fields.many2one('res.company', 'Company'),
    }
    _defaults = {
        'date': fields.date.context_today,
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice.prepayment', context=c),
    }
account_invoice_prepayment()

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"

    def product_id_change(self, cr, uid, ids, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None):
        if context is None:
            context = {}
        result = super(account_invoice_line,self).product_id_change(cr, uid, ids, product, uom_id, qty=qty, name=name, type=type, partner_id=partner_id, fposition_id=fposition_id, price_unit=price_unit, currency_id=currency_id, context=context, company_id=company_id)
        
        if not product:
            return result
        res = self.pool.get('product.product').browse(cr, uid, product, context=context)

        result['value']['name'] = res.description or res.name
        if res.packaging_id:
            result['value']['name'] += '\n'+res.packaging_id.name
        if partner_id and type == 'out_invoice':
            tax_ids = self.pool.get('res.partner').browse(cr, uid, partner_id, context).tax_ids
            if tax_ids:
                result['value']['invoice_line_tax_id'] = [tax.id for tax in tax_ids]

        return result
    
    _columns = {
        'uos_id': fields.many2one('product.uom', 'Unit', ondelete='set null', select=True),
        'price_unit': fields.float('Price', required=True, digits_compute= dp.get_precision('Product Price')),
        'quantity': fields.float('QTY', digits_compute= dp.get_precision('Product Unit of Measure'), required=True),
        'discount': fields.float('Disc%', digits_compute= dp.get_precision('Discount')),
        'invoice_line_tax_id': fields.many2many('account.tax', 'account_invoice_line_tax', 'invoice_line_id', 'tax_id', 'Tax', domain=[('parent_id','=',False)]),
    }
    
    def default_get(self, cr, uid, fields, context=None):
        result = super(account_invoice_line, self).default_get(cr, uid, fields, context=context)
        if context.get('invoice_partner_id',False):
            partner = self.pool.get('res.partner').browse(cr, uid, context['invoice_partner_id'])
            result.update({'discount':partner.fixed_discount})
        return result
    
account_invoice_line

class account_move_line(osv.osv):
    _inherit = "account.move.line"
    
    _columns = {
    }
    
    def _update_check(self, cr, uid, ids, context=None):
        reconcile_obj = self.pool.get('account.move.reconcile')
        done = {}
        for line in self.browse(cr, uid, ids, context=context):
            err_msg = _('Move name (id): %s (%s)') % (line.move_id.name, str(line.move_id.id))
            if line.move_id.state <> 'draft' and (not line.journal_id.entry_posted):
                raise osv.except_osv(_('Error!'), _('You cannot do this modification on a confirmed entry. You can just change some non legal fields or you must unconfirm the journal entry first.\n%s.') % err_msg)
            #Thanh: Allow delete Reconcilie Entry
            if line.reconcile_id:
                reconcile_obj.unlink(cr, uid, [line.reconcile_id.id], context)
#                 raise osv.except_osv(_('Error!'), _('You cannot do this modification on a reconciled entry. You can just change some non legal fields or you must unreconcile first.\n%s.') % err_msg)
            t = (line.journal_id.id, line.period_id.id)
            if t not in done:
                self._update_journal_check(cr, uid, line.journal_id.id, line.period_id.id, context)
                done[t] = True
        return True
    
account_move_line()

# class account_invoice_tax(osv.osv):
#     _inherit = "account.invoice.tax"
#
#     _columns = {
#         'account_id': fields.many2one('account.account', 'Tax Account', required=True, domain="[('type','<>','view'),('type','<>','income'), ('type', '<>', 'closed'), ('company_id', '=', parent.company_id)]"),
#     }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
