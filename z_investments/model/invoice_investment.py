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
import openerp
import openerp.addons.decimal_precision as dp
from openerp import netsvc
from openerp.tools import float_compare


class invoice_investment(osv.osv):
    _name = 'invoice.investment'
    _inherit = "account.invoice"

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
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + \
                                              res[invoice.id][
                                                  'amount_untaxed'] + invoice.shipping_charge
        return res

    def _get_investment_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('invoice.investment.line').browse(cr, uid, ids,
                                                                 context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('invoice.investment.tax').browse(cr, uid, ids,
                                                               context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    def _get_investment_from_line(self, cr, uid, ids, context=None):
        move = {}
        for line in self.pool.get('account.move.line').browse(cr, uid, ids,
                                                              context=context):
            if line.reconcile_partial_id:
                for line2 in line.reconcile_partial_id.line_partial_ids:
                    move[line2.move_id.id] = True
            if line.reconcile_id:
                for line2 in line.reconcile_id.line_id:
                    move[line2.move_id.id] = True
        invoice_ids = []
        if move:
            invoice_ids = self.pool.get('invoice.investment').search(cr, uid, [
                ('move_id', 'in', move.keys())], context=context)
        return invoice_ids

    def _get_investment_from_reconcile(self, cr, uid, ids, context=None):
        move = {}
        for r in self.pool.get('account.move.reconcile').browse(cr, uid, ids,
                                                                context=context):
            for line in r.line_partial_ids:
                move[line.move_id.id] = True
            for line in r.line_id:
                move[line.move_id.id] = True

        invoice_ids = []
        if move:
            invoice_ids = self.pool.get('invoice.investment').search(cr, uid, [
                ('move_id', 'in', move.keys())], context=context)
        return invoice_ids

    def _get_amount_deposit(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = 0
            for line in order.prepayment_lines:
                res[order.id] += (
                            line.amount + line.bank_fee_deducted + line.discount_allowed)
        return res

    def _get_order_from_deposit(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.prepayment').browse(cr, uid,
                                                                       ids,
                                                                       context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _amount_residual(self, cr, uid, ids, name, args, context=None):
        result = {}
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

    def _reconciled(self, cr, uid, ids, name, args, context=None):
        res = {}
        wf_service = netsvc.LocalService("workflow")
        for inv in self.browse(cr, uid, ids, context=context):
            res[inv.id] = self.test_paid(cr, uid, [inv.id])
            print '=============', inv
            if not res[inv.id] and inv.state == 'paid':
                wf_service.trg_validate(uid, 'invoice.investment', inv.id, 'open_test', cr)
        return res

    _columns = {
        'is_investment': fields.boolean('Is Investment'),
        'invoice_line': fields.one2many('invoice.investment.line', 'invoice_id',
                                        'Invoice Lines', readonly=True,
                                        states={
                                            'draft': [('readonly', False)]}),
        'tax_line': fields.one2many('invoice.investment.tax', 'invoice_id',
                                    'Tax Lines', readonly=True,
                                    states={'draft': [('readonly', False)]}),
        'prepayment_lines': fields.one2many('account.invoice.prepayment',
                                            'invoice_investment_id', readonly=True,
                                            states={'draft': [
                                                ('readonly', False)]}),
        'tax_id': fields.many2many('account.tax',
                                   'invoice_investment_shipping_charge_tax', 'order_id',
                                   'tax_id', 'Taxes', readonly=True,
                                   states={'draft': [('readonly', False)]}),
        'deposit_paid': fields.function(_get_amount_deposit,
                                        digits_compute=dp.get_precision(
                                            'Account'), string='Deposit Paid',
                                        store={
                                            'invoice.investment': (
                                            lambda self, cr, uid, ids,
                                                   c={}: ids,
                                            ['prepayment_lines'], 10),
                                            'account.invoice.prepayment': (
                                            _get_order_from_deposit,
                                            ['amount'], 10),
                                        }),

        'amount_untaxed': fields.function(_amount_all,
                                          digits_compute=dp.get_precision(
                                              'Account'), string='Subtotal',
                                          track_visibility='always',
                                          store={
                                              'invoice.investment': (
                                              lambda self, cr, uid, ids,
                                                     c={}: ids,
                                              ['invoice_line'], 20),
                                              'invoice.investment.tax': (
                                              _get_invoice_tax, None, 20),
                                              'invoice.investment.line': (
                                              _get_investment_line, ['price_unit',
                                                                  'invoice_line_tax_id',
                                                                  'quantity',
                                                                  'discount',
                                                                  'invoice_id'],
                                              20),
                                          },
                                          multi='all'),
        'amount_tax': fields.function(_amount_all,
                                      digits_compute=dp.get_precision(
                                          'Account'), string='Tax',
                                      store={
                                          'invoice.investment': (
                                          lambda self, cr, uid, ids, c={}: ids,
                                          ['invoice_line', 'tax_id'], 20),
                                          'invoice.investment.tax': (
                                          _get_invoice_tax, None, 20),
                                          'invoice.investment.line': (
                                          _get_investment_line,
                                          ['price_unit', 'invoice_line_tax_id',
                                           'quantity', 'discount',
                                           'invoice_id'], 20),
                                      },
                                      multi='all'),

        'amount_total': fields.function(_amount_all,
                                        digits_compute=dp.get_precision(
                                            'Account'), string='Total',
                                        store={
                                            'invoice.investment': (
                                            lambda self, cr, uid, ids,
                                                   c={}: ids, ['invoice_line',
                                                               'shipping_charge'],
                                            20),
                                            'invoice.investment.tax': (
                                            _get_invoice_tax, None, 20),
                                            'invoice.investment.line': (
                                            _get_investment_from_reconcile, ['price_unit',
                                                                'invoice_line_tax_id',
                                                                'quantity',
                                                                'discount',
                                                                'invoice_id'],
                                            20),
                                        },
                                        multi='all'),

        # Thanh: Change the way computing Balance
        'residual': fields.function(_amount_residual,
                                    digits_compute=dp.get_precision('Account'),
                                    string='Balance',
                                    store={
                                        'invoice.investment': (
                                        lambda self, cr, uid, ids, c={}: ids,
                                        ['invoice_line', 'move_id'], 50),
                                        'invoice.investment.tax': (
                                        _get_invoice_tax, None, 50),
                                        'invoice.investment.line': (
                                        _get_investment_line,
                                        ['price_unit', 'invoice_line_tax_id',
                                         'quantity', 'discount', 'invoice_id'],
                                        50),
                                        'account.move.line': (
                                        _get_investment_from_line, None, 50),
                                        'account.move.reconcile': (
                                        _get_investment_from_reconcile, None, 50),
                                    },
                                    help="Remaining amount due."),
        'reconciled': fields.function(_reconciled, string='Paid/Reconciled',
                                      type='boolean',
                                      store={
                                          'invoice.investment': (
                                          lambda self, cr, uid, ids, c={}: ids,
                                          None, 50),
                                      # Check if we can remove ?
                                          'account.move.line': (
                                          _get_investment_from_line, None, 50),
                                          'account.move.reconcile': (
                                          _get_investment_from_reconcile, None,
                                          50),
                                      },
                                      help="It indicates that the invoice has been paid and the journal entry of the invoice has been reconciled with one or several journal entries of payment."),
    }

    def button_reset_taxes(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        cur_obj = self.pool.get('res.currency')
        ait_obj = self.pool.get('invoice.investment.tax')
        for id in ids:
            cr.execute("DELETE FROM invoice_investment_tax WHERE invoice_id=%s AND manual is False", (id,))
            inv = self.browse(cr, uid, id, context=ctx)
            old_company_id = self.pool.get('sale.order').write_partner_company_to_user(cr, uid, inv, context)
            partner = inv.partner_id
            if partner.lang:
                ctx.update({'lang': partner.lang})

            tax_grouped = ait_obj.compute_investment(cr, uid, id, context=ctx)
            for taxe in tax_grouped.values():
                ait_obj.create(cr, uid, taxe)

            #anlee:  revert company for user
            if old_company_id:
                self.pool.get('res.users').write(cr, uid, [uid],{'company_id': old_company_id})
        # Update the stored value (fields.function), so we write to trigger recompute
        self.write(cr, uid, ids, {'invoice_line':[]}, context=ctx)
        return True
invoice_investment()

class invoice_investment_line(osv.osv):
    _name = 'invoice.investment.line'
    _inherit = "account.invoice.line"

    _columns = {
        'invoice_id': fields.many2one('invoice.investment', 'Invoice Reference',
                                      ondelete='cascade', select=True),
        'invoice_line_tax_id': fields.many2many('account.tax',
                                                'account_investment_invoice_line_tax',
                                                'invoice_line_id', 'tax_id',
                                                'Tax', domain=[
                ('parent_id', '=', False)]),
    }
invoice_investment_line()

class invoice_investment_tax(osv.osv):
    _name = "invoice.investment.tax"
    _inherit = "account.invoice.tax"

    _columns = {
        'invoice_id': fields.many2one('invoice.investment',
                                     'Invoice Reference',
                                      ondelete='cascade', select=True),
        'manual': fields.boolean('Manual'),
    }

    def compute_investment(self, cr, uid, invoice_id, context=None):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('invoice.investment').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
        for line in inv.invoice_line:
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, line.product_id, inv.partner_id)['taxes']:
                val={}
                val['invoice_id'] = inv.id
                val['tax_id'] = tax['id']
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = cur_obj.round(cr, uid, cur, tax['price_unit'] * line['quantity'])

                if inv.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']

                key = (val['tax_id'], val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']


        #tax for shipping
        inv = self.pool.get('invoice.investment').browse(cr, uid, invoice_id, context=context)
        if inv.tax_id:
            cur_obj = self.pool.get('res.currency')
            cur = inv.currency_id
            company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
            for tax in self.pool.get('account.tax').compute_all(cr, uid, inv.tax_id, inv.shipping_charge, 1, False, inv.partner_id)['taxes']:
                val={}
                val['base'] = cur_obj.round(cr, uid, cur, tax['price_unit'])
                val['invoice_id'] = inv.id
                val['tax_id'] = tax['id']
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                if inv.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or fields.date.context_today(self, cr, uid, context=context)}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or fields.date.context_today(self, cr, uid, context=context)}, round=False)
                    val['account_id'] = tax['account_collected_id']
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or fields.date.context_today(self, cr, uid, context=context)}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or fields.date.context_today(self, cr, uid, context=context)}, round=False)
                    val['account_id'] = tax['account_paid_id']
                    val['account_analytic_id'] = tax['account_analytic_paid_id']

                key = (val['tax_id'], val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
                key2 = (val['tax_id'], val['tax_code_id'], val['base_code_id'], val['account_id'])
                if not key in tax_grouped.keys():
                    if key2 in tax_grouped.keys():
                        key = key2
                if not key in tax_grouped.keys() and not key2 in tax_grouped.keys() and tax_grouped.keys() and len(tax_grouped.keys()[0]) == 3:
                    key = key2

                if not key in tax_grouped.keys():
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
        return tax_grouped
invoice_investment_tax()

class account_invoice_prepayment(osv.osv):
    _inherit = "account.invoice.prepayment"

    _columns = {
        'invoice_investment_id': fields.many2one('invoice.investment',
                                                 'Invoice Reference',
                                                 ondelete='cascade',
                                                 select=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice',
                                      required=False, ondelete='cascade',
                                      select=True),
    }

account_invoice_prepayment()
