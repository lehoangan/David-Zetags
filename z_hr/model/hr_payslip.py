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
        'payment_account_id': fields.many2one('account.account', 'Payment Account',
                                              domain="[('type', '=', 'liquidity'), ('company_id', '=', company_id)]"),
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
            if contract_id:
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
            if contract_record.payment_account_id:
                res['value'].update({'payment_account_id': contract_record.payment_account_id.id})
            if contract_record.payment_method:
                res['value'].update({'payment_method': contract_record.payment_method.id})
        if employee_id:
            employee = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
            if not  res['value'].get('payment_account_id') and employee.payment_account_id:
                res['value'].update({'payment_account_id': employee.payment_account_id.id})
            if not  res['value'].get('payment_method') and employee.payment_method:
                res['value'].update({'payment_method': employee.payment_method.id})
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

from lxml import etree
class hr_contract(osv.osv):
    _inherit = "hr.contract"
    _columns = {
        'payment_account_id': fields.many2one('account.account', 'Payment Account',
                                              domain="[('type', '=', 'liquidity')]"),
        'payment_method': fields.many2one('payment.methods', 'Payment Method'),
    }

    def onchange_employee_id(self, cr, uid, ids, employee_id, context=None):
        vals = {}
        if employee_id:
            employee = self.pool.get('hr.employee').browse(cr, uid, employee_id, context)
            if employee.payment_account_id:
                vals.update({'payment_account_id': employee.payment_account_id.id})
            if employee.payment_method:
                vals.update({'payment_method': employee.payment_method.id})
        return {'value': vals}

    def fields_view_get(self, cr, uid, view_id=None, view_type=None, context=None, toolbar=False, submenu=False):
        res = super(hr_contract, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context,
                                                       toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'], parser=None, base_url=None)
            company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
            node = doc.xpath("//field[@name='payment_account_id']")[0]
            node.set('domain', "[('type', '=', 'liquidity'), ('company_id', '=', %s)]"%company_id)
            res['arch'] = etree.tostring(doc, encoding="utf-8")
        return res

hr_contract()

class hr_employee(osv.osv):
    _inherit = "hr.employee"
    _columns = {
        'payment_account_id': fields.many2one('account.account', 'Payment Account',
                                              domain="[('type', '=', 'liquidity')]"),
        'payment_method': fields.many2one('payment.methods', 'Payment Method'),
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type=None, context=None, toolbar=False, submenu=False):
        res = super(hr_employee, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context,
                                                       toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'], parser=None, base_url=None)
            company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
            node = doc.xpath("//field[@name='payment_account_id']")[0]
            node.set('domain', "[('type', '=', 'liquidity'), ('company_id', '=', %s)]"%company_id)
            res['arch'] = etree.tostring(doc, encoding="utf-8")
        return res

hr_employee()


class hr_payslip_employees(osv.osv_memory):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self, cr, uid, ids, context=None):
        res = super(hr_payslip_employees, self).compute_sheet(cr, uid, ids, context=context)
        run_pool = self.pool.get('hr.payslip.run')
        if context is None:
            context = {}
        if context and context.get('active_id', False):
            run_data = run_pool.browse(cr, uid, context['active_id'], context)
            for payslip in run_data.slip_ids:
                employee = payslip.employee_id
                vals = {}
                if employee.payment_account_id:
                    vals.update({'payment_account_id': employee.payment_account_id.id})
                if employee.payment_method:
                    vals.update({'payment_method': employee.payment_method.id})
                if vals:
                    payslip.write(vals)
        return res
hr_payslip_employees()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
