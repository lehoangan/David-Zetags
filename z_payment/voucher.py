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
    }
    
    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = super(account_config_settings, self).onchange_company_id(cr, uid, ids, company_id, context=context)
        if company_id:
            company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
            res['value'].update({'deduct_bank_fee_account_id': company.deduct_bank_fee_account_id and company.deduct_bank_fee_account_id.id or False, 
                                 'deduct_payment_discount_account_id': company.deduct_payment_discount_account_id and company.deduct_payment_discount_account_id.id or False})
        else: 
            res['value'].update({'deduct_bank_fee_account_id': False, 
                                 'deduct_payment_discount_account_id': False})
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

    def onchange_reconcile(self, cr, uid, ids, choose, amount, amount_unreconciled, context=None):
        vals = {'amount': 0.0, 'reconcile': False}
        if choose:
            vals = { 'amount': amount_unreconciled, 'reconcile': True}
        return {'value': vals}

account_voucher_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
