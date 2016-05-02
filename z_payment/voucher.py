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
from openerp.tools import float_compare

class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {
        'deduct_bank_fee_account_id': fields.many2one(
            'account.account',
            string="Deduct Bank Fee Account",
            domain="[('type', '=', 'other'),('company_id','=', id)]",),
        'deduct_payment_discount_account_id': fields.many2one(
            'account.account',
            string="Deduct Payment Discount Account",
            domain="[('type', '=', 'other'),('company_id','=', id)]",),
        'deduct_currency_account_id': fields.many2one(
            'account.account',
            string="Deduct Currency Gain/Loss Account",
            domain="[('type', '!=', 'view'),('company_id','=', id)]",),
    }

    def action_open_entries(self, cr, uid, ids, context=None):
        sql = ''' SELECT move_id FROM account_invoice WHERE type in ('out_invoice','out_refund') and move_id is not null
                  UNION
                  SELECT move_id FROM account_voucher WHERE type in ('sale','receipt') and move_id is not null
              '''
        cr.execute(sql)
        data = cr.dictfetchall()
        move_ids = [tmp['move_id'] for tmp in data]

        return {
        'view_type':'form',
        'view_mode':'tree,form',
        'res_model':'account.move',
        'view_id':False,
        'type':'ir.actions.act_window',
        'domain':[('id','in',move_ids)],
        'context': context,
      }

res_company()

class account_config_settings(osv.osv_memory):
    _inherit = 'account.config.settings'
    _columns = {
        'deduct_bank_fee_account_id': fields.related(
            'company_id', 'deduct_bank_fee_account_id',
            type='many2one',
            relation='account.account',
            string="Deduct Bank Fee Account", 
            domain="[('type', '=', 'other')]"),
        'deduct_payment_discount_account_id': fields.related(
            'company_id', 'deduct_payment_discount_account_id',
            type="many2one",
            relation='account.account',
            string="Deduct Payment Discount Account",
            domain="[('type', '=', 'other')]"),
        'deduct_currency_account_id': fields.related(
            'company_id', 'deduct_currency_account_id',
            type="many2one",
            relation='account.account',
            string="Deduct Currency Gain/Loss Account"
        ),
    }
    
    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = super(account_config_settings, self).onchange_company_id(cr, uid, ids, company_id, context=context)
        if company_id:
            company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
            res['value'].update({'deduct_bank_fee_account_id': company.deduct_bank_fee_account_id and company.deduct_bank_fee_account_id.id or False, 
                                 'deduct_payment_discount_account_id': company.deduct_payment_discount_account_id and company.deduct_payment_discount_account_id.id or False,
                                 'deduct_currency_account_id': company.deduct_currency_account_id and company.deduct_currency_account_id.id or False})
        else: 
            res['value'].update({'deduct_bank_fee_account_id': False, 
                                 'deduct_payment_discount_account_id': False,
                                 'deduct_currency_account_id': False})
        return res
    
class account_voucher(osv.osv):
    _inherit = "account.voucher"
    
    def _get_total_to_apply(self, cr, uid, ids, name, args, context=None):
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            res[voucher.id] = voucher.amount + voucher.bank_fee_deducted + voucher.discount_allowed
        return res
    
    def _get_writeoff_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        currency_obj = self.pool.get('res.currency')
        res = {}
        debit = credit = 0.0
        for voucher in self.browse(cr, uid, ids, context=context):
            sign = voucher.type == 'payment' and -1 or 1
            for l in voucher.line_dr_ids:
                debit += l.amount
            for l in voucher.line_cr_ids:
                credit += l.amount
            currency = voucher.currency_id or voucher.company_id.currency_id
            #Thanh: Change the way of calculate of Writeoff amount
#             res[voucher.id] =  currency_obj.round(cr, uid, currency, voucher.amount - sign * (credit - debit))
            res[voucher.id] =  currency_obj.round(cr, uid, currency, (voucher.amount + voucher.bank_fee_deducted + voucher.discount_allowed) - sign * (credit - debit))
        return res
    
    _columns = {
        'bank_fee_deducted': fields.float('Bank Fee Deducted', digits_compute=dp.get_precision('Account'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'discount_allowed': fields.float('Discount Allowed', digits_compute=dp.get_precision('Account'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'total_to_apply': fields.function(_get_total_to_apply, type='float', string='Total to Apply', digits_compute=dp.get_precision('Account'), readonly=True),
        
        'writeoff_amount': fields.function(_get_writeoff_amount, string='Difference Amount', type='float', readonly=True, help="Computed as the difference between the amount stated in the voucher and the sum of allocation on the voucher lines."),
        
        'company_currency_id': fields.related('company_id','currency_id', type='many2one', relation='res.currency', string='Company Currency', readonly=True),
    }
    _defaults = {
        'bank_fee_deducted': 0,
        'discount_allowed': 0,
    }

    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        result = super(account_voucher, self).recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context)
        # print '=================', context
        if result.get('value', False) and context.get('active_model', '') != 'account.invoice':
            if result['value'].get('line_cr_ids', False):
                for dict in result['value']['line_cr_ids']:
                    dict['reconcile'] = False
                    dict['amount'] = 0
            if result['value'].get('line_dr_ids', False):
                for dict in result['value']['line_dr_ids']:
                    dict['reconcile'] = False
                    dict['amount'] = 0
        return result

    def action_move_line_create(self, cr, uid, ids, context=None):
        order = self.browse(cr, uid, ids[0])
        old_company_id = self.write_partner_company_to_user(cr, uid, order, context)
        res = super(account_voucher, self).action_move_line_create(cr, uid, ids, context)
        if old_company_id:
            self.pool.get('res.users').write(cr, uid, [uid],{'company_id': old_company_id})
        return res

    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        res = super(account_voucher, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context)
        if not res:
            res = {'value': {}}
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if partner.company_id:
                res['value'].update({'company_id': partner.company_id.id})
        return res

    #Thanh: Add bank_fee_deducted and discount_allowed to onchange for total_to_apply
    def onchange_line_ids(self, cr, uid, ids, line_dr_ids, line_cr_ids, amount, voucher_currency, type, 
                          bank_fee_deducted = 0.0,
                          discount_allowed = 0.0,
                          context=None):
        if context is None:
            context = {}
        #Thanh: Pass amount = total_to_apply to original onchange_amount
        try:
            total_to_apply = amount + bank_fee_deducted + discount_allowed
        except Exception, ex:
            total_to_apply = 0.0
            
        res = super(account_voucher, self).onchange_line_ids(cr, uid, ids, line_dr_ids, line_cr_ids, total_to_apply, voucher_currency, type, context=context)
        return res
    
    def onchange_amount(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, 
                        bank_fee_deducted = 0.0,
                        discount_allowed = 0.0,
                        context=None):
        if context is None:
            context = {}
        #Thanh: Pass amount = total_to_apply to original onchange_amount
        try:
            total_to_apply = amount + bank_fee_deducted + discount_allowed
        except Exception, ex:
            total_to_apply = amount
            
        res = super(account_voucher, self).onchange_amount(cr, uid, ids, total_to_apply, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=context)
        res['value']['total_to_apply'] = total_to_apply
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if partner.company_id:
                res['value'].update({'company_id': partner.company_id.id})
        return res
    
    #Thanh: New function creating Bank Fee move line
    def move_line_bank_fee(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
        cur_obj = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        
        diff_currency = company_currency <> current_currency
        
        deduct_bank_fee_account_id = voucher.company_id.deduct_bank_fee_account_id
        if not deduct_bank_fee_account_id:
            raise osv.except_osv(_('Insufficient Configuration!'),_("You must set an account for Bank Fees in Settings/Configuration/Accounting."))
        
        ctx = {'date': voucher.date or False}
        debit = credit = voucher.bank_fee_deducted
        amount_currency = 0.0
        if diff_currency:
            debit = credit = cur_obj.compute(cr, uid, current_currency, company_currency, voucher.bank_fee_deducted, context=ctx)
            amount_currency = voucher.bank_fee_deducted
            
        if voucher.type in ('receipt'):
            credit = 0.0
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1

        move_line = {
                'name': 'Bank Fee',
                'debit': debit,
                'credit': credit,
                'account_id': deduct_bank_fee_account_id.id,
                'move_id': move_id,
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'partner_id': voucher.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * amount_currency or 0.0,
                'date': voucher.date,
                'date_maturity': voucher.date_due
            }

        return move_line_pool.create(cr, uid, move_line)
    
    #Thanh: New function creating Discount Allowed move line
    def move_line_discount_allowed(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
        cur_obj = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        
        diff_currency = company_currency <> current_currency
        
        deduct_payment_discount_account_id = voucher.company_id.deduct_payment_discount_account_id
        if not deduct_payment_discount_account_id:
            raise osv.except_osv(_('Insufficient Configuration!'),_("You must set an account for Discounts Allowed in Settings/Configuration/Accounting."))
        
        ctx = {'date': voucher.date or False}
        debit = credit = voucher.discount_allowed
        amount_currency = 0.0
        if diff_currency:
            debit = credit = cur_obj.compute(cr, uid, current_currency, company_currency, voucher.discount_allowed, context=ctx)
            amount_currency = voucher.discount_allowed

        if voucher.type in ('receipt'):
            credit = 0.0
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1

        move_line = {
                'name': 'Discount Allowed',
                'debit': debit,
                'credit': credit,
                'account_id': deduct_payment_discount_account_id.id,
                'move_id': move_id,
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'partner_id': voucher.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * amount_currency or 0.0,
                'date': voucher.date,
                'date_maturity': voucher.date_due
            }

        return move_line_pool.create(cr, uid, move_line)

    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        tot_line = line_total
        rec_lst_ids = []

        date = self.read(cr, uid, voucher_id, ['date'], context=context)['date']
        ctx = context.copy()
        ctx.update({'date': date})
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
        voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
        ctx.update({
            'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
            'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
        prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        for line in voucher.line_ids:
            #create one move line per voucher line where amount is not 0.0
            # AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
            if not line.reconcile and not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
            # if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
            # currency rate difference
            if line.amount == line.amount_unreconciled:
                if not line.move_line_id:
                    raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
                sign = line.type =='dr' and -1 or 1
                currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
            else:
                currency_rate_difference = 0.0
            move_line = {
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': voucher.date
            }
            if amount < 0:
                amount = -amount
                if line.type == 'dr':
                    line.type = 'cr'
                else:
                    line.type = 'dr'

            if (line.type=='dr'):
                tot_line += amount
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount

            if voucher.tax_id and voucher.type in ('sale', 'purchase'):
                move_line.update({
                    'account_tax_id': voucher.tax_id.id,
                })

            if move_line.get('account_tax_id', False):
                tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
                if not (tax_data.base_code_id and tax_data.tax_code_id):
                    raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))

            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            amount_currency = False
            if line.move_line_id:
                # We want to set it on the account move line as soon as the original line had a foreign currency
                if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
                    # we compute the amount in that foreign currency.
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the voucher and the voucher line share the same currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        amount_currency = sign * (line.amount)
                    else:
                        # if the rate is specified on the voucher, it will be used thanks to the special keys in the context
                        # otherwise we use the rates of the system
                        amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
                if line.amount == line.amount_unreconciled:
                    foreign_currency_diff = line.move_line_id.amount_residual_currency - abs(amount_currency)

            move_line['amount_currency'] = amount_currency
            voucher_line = move_line_obj.create(cr, uid, move_line)
            rec_ids = [voucher_line, line.move_line_id.id]

            if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
                move_line_obj.create(cr, uid, exch_lines[1], context)
                rec_ids.append(new_id)

            if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
                # Change difference entry in voucher currency
                move_line_foreign_currency = {
                    'journal_id': line.voucher_id.journal_id.id,
                    'period_id': line.voucher_id.period_id.id,
                    'name': _('change')+': '+(line.name or '/'),
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': line.voucher_id.partner_id.id,
                    'currency_id': line.move_line_id.currency_id.id,
                    'amount_currency': -1 * foreign_currency_diff,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': line.voucher_id.date,
                }
                new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
                rec_ids.append(new_id)
            if line.move_line_id.id:
                rec_lst_ids.append(rec_ids)
        return (tot_line, rec_lst_ids)

    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            local_context = dict(context, force_company=voucher.journal_id.company_id.id)
            if voucher.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, voucher.id, context)
            current_currency = self._get_current_currency(cr, uid, voucher.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, voucher.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name

            #Anlee: Create move for Bank Fee and Discount Allowed
            move_line_ids = []
            if voucher.type in ('receipt'):
                if voucher.bank_fee_deducted:
                    move_line_id = self.move_line_bank_fee(cr, uid, voucher.id, move_id, company_currency, current_currency, context)
                    move_line_ids += [move_line_id]
                if voucher.discount_allowed:
                    move_line_id = self.move_line_discount_allowed(cr, uid, voucher.id, move_id, company_currency, current_currency, context)
                    move_line_ids += [move_line_id]
            #Anlee: Create move for Bank Fee and Discount Allowed

            # Create the first line of the voucher
            move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, local_context), local_context)
            move_line_ids += [move_line_id]
            move_line_brws = move_line_pool.browse(cr, uid, move_line_ids, context=context)
            line_total = 0
            for move_line_brw in move_line_brws:
                line_total += move_line_brw.debit - move_line_brw.credit
            rec_list_ids = []
            if voucher.type == 'sale':
                line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            elif voucher.type == 'purchase':
                line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            # Create one move line per voucher line where amount is not 0.0
            line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)

            # Create the writeoff line if needed
            ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, local_context)
            if ml_writeoff:
                move_line_pool.create(cr, uid, ml_writeoff, local_context)

            # We post the voucher.
            self.write(cr, uid, [voucher.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            if voucher.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
            # We automatically reconcile the account move lines.
            reconcile = False
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
        return True
account_voucher()

class account_voucher_line(osv.osv):
    _inherit = 'account.voucher.line'

    _columns = {
        'choose': fields.boolean('Choose'),
    }

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('reconcile', False) and not vals.get('choose', False):
            vals['choose'] = True
        return super(account_voucher_line, self).write(cr, uid, ids, vals, context)

    def create(self, cr, uid, vals, context=None):
        if vals.get('reconcile', False) and not vals.get('choose', False):
            vals['choose'] = True
        return super(account_voucher_line, self).create(cr, uid, vals, context)

    def onchange_reconcile(self, cr, uid, ids, choose, amount, amount_unreconciled, context=None):
        vals = {'amount': 0.0, 'reconcile': False}
        if choose:
            vals = { 'amount': amount_unreconciled, 'reconcile': True}
        return {'value': vals}

account_voucher_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
