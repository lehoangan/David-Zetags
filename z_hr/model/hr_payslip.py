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
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import netsvc

class hr_payslip(osv.osv):
    _inherit = "hr.payslip"
    _columns = {
        'paid_date': fields.date('Paid Date', required=True),
        'payment_ref': fields.char('Payment Ref', 250),
        'memo': fields.char('Memo', 250),
        'payment_account': fields.many2one('account.journal', 'Payment Account', domain="[('company_id', '=', company_id)]"),
        'payment_method': fields.many2one('payment.methods', 'Payment Method'),
    }

    _defaults = {
        'paid_date': lambda *a: time.strftime('%Y-%m-%d'),
        'date_from': False,
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def action_revert_done(self, cr, uid, ids, context=None):
        if not len(ids):
            return False
        for slip in self.browse(cr, uid, ids, context):
            self.write(cr, uid, [slip.id], {'state': 'cancel'})
            if slip.move_id:
                slip.move_id.button_cancel()
                slip.move_id.unlink()
            wf_service = netsvc.LocalService("workflow")
            # Deleting the existing instance of workflow
            wf_service.trg_delete(uid, 'hr.payslip', slip.id, cr)
            wf_service.trg_create(uid, 'hr.payslip', slip.id, cr)
            wf_service.trg_validate(uid, 'hr.payslip', slip.id, 'cancel_sheet', cr)
        return True

    def hr_verify_sheet(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context):
            if not obj.line_ids:
                self.compute_sheet(cr, uid, [obj.id], context)
        return self.write(cr, uid, ids, {'state': 'verify'}, context=context)

    def process_sheet(self, cr, uid, ids, context=None):
        res = super(hr_payslip, self).process_sheet(cr, uid, ids, context=context)
        period_pool = self.pool.get('account.period')
        for payslip in self.browse(cr, uid, ids, context):
            if payslip.move_id and payslip.paid_date:
                period_ids = period_pool.find(cr, uid, payslip.paid_date, context)
                payslip.move_id.button_cancel()
                for move in payslip.move_id.line_id:
                    move.write({'date': payslip.paid_date,
                                'period_id': period_ids[0],
                                })
                payslip.move_id.write({'date': payslip.paid_date,
                                        'period_id': period_ids[0],})
                payslip.move_id.button_validate()

        return res

    def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False,
                             context=None):

        if not date_from and date_to and employee_id:
            contract_obj = self.pool.get('hr.contract')
            if not contract_id:
                contract_ids = self.get_contract(cr, uid, self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context), date_from, date_to, context=context)
                if contract_ids:
                    contract_id = contract_ids[0]
            contract_record = contract_obj.browse(cr, uid, contract_id, context=context)

            schedule_pay = contract_record.schedule_pay
            days = 0
            if 'weekly' == schedule_pay:
                days = 7
            elif 'bi-weekly' == schedule_pay:
                days = 14
            elif 'semi-monthly' == schedule_pay:  # impossible
                days = 15
            elif 'monthly' == schedule_pay:
                days = 30
            elif 'quarterly' == schedule_pay:
                days = 91
            elif 'semi-annually' == schedule_pay:
                days = 182
            elif 'annually' == schedule_pay:
                days = 365
            date_to = datetime.strptime(date_to, "%Y-%m-%d")
            day_from = date_to - relativedelta(days=days)
            date_from =  day_from.strftime("%Y-%m-%d")

        res = super(hr_payslip, self).onchange_employee_id(cr, uid, ids, date_from, date_to, employee_id, contract_id, context)
        if contract_id:
            contract_obj = self.pool.get('hr.contract')
            contract_record = contract_obj.browse(cr, uid, contract_id, context=context)
            if contract_record.journal_id:
                res['value'].update({'payment_account': contract_record.journal_id.id})
            if contract_record.payment_method:
                res['value'].update({'payment_method': contract_record.payment_method.id})
        res['value'].update({'date_from': date_from})
        return res

    def get_contract(self, cr, uid, employee, date_from, date_to, context=None):
        contract_ids = super(hr_payslip, self).get_contract(cr, uid, employee, date_from, date_to, context)
        if not contract_ids and not date_from and date_to:
            contract_obj = self.pool.get('hr.contract')
            contract_ids = contract_obj.search(cr, uid, [('employee_id', '=', employee.id)], context=context)
        return contract_ids

    def onchange_date_to(self, cr, uid, ids, date_to, context={}):
        if date_to:
            print date_to
        return {}


hr_payslip()

class hr_contract(osv.osv):
    _inherit = "hr.contract"
    _columns = {
        'journal_id': fields.many2one('account.journal', 'Payment Account', domain="[('company_id', '=', company_id)]"),
        'payment_method': fields.many2one('payment.methods', 'Payment Method'),
    }

hr_contract()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
