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
from account.report.account_partner_ledger import third_party_ledger
from openerp.report import report_sxw

class partner_ledger_zateg(third_party_ledger):

    def __init__(self, cr, uid, name, context=None):
        super(partner_ledger_zateg, self).__init__(cr, uid, name, context=context)
        self.init_bal_sum = 0.0
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'sum_debit_partner': self._sum_debit_partner,
            'sum_credit_partner': self._sum_credit_partner,
            'get_currency': self._get_currency,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period,
            'get_account': self._get_account,
            'get_filter': self._get_filter,
            'get_start_date': self._get_start_date,
            'get_end_date': self._get_end_date,
            'get_fiscalyear': self._get_fiscalyear,
            'get_journal': self._get_journal,
            'get_partners':self._get_partners,
            'get_intial_balance':self._get_intial_balance,
            'display_initial_balance':self._display_initial_balance,
            'display_currency':self._display_currency,
            'get_target_move': self._get_target_move,
        })

    def set_context(self, objects, data, ids, report_type=None):
        if data['form']['hide_zero']:
            ctx = data['form'].get('used_context', {})
            if ctx:
                data['form']['used_context'].update({'hide_zero': data['form']['hide_zero']})
            else:
                data['form'].update({'used_context': {'hide_zero': data['form']['hide_zero']}})

        if data['form']['unpaid_invoice']:
            ctx = data['form'].get('used_context', {})
            if ctx:
                data['form']['used_context'].update({'unpaid_invoice': data['form']['unpaid_invoice']})
            else:
                data['form'].update({'used_context': {'unpaid_invoice': data['form']['unpaid_invoice']}})

        if data['form']['currency_id']:
            ctx = data['form'].get('used_context', {})
            if ctx:
                data['form']['used_context'].update({'currency_id': data['form']['currency_id'][0]})
            else:
                data['form'].update({'used_context': {'currency_id': data['form']['currency_id'][0]}})

        if data['form']['partner_id']:
            ctx = data['form'].get('used_context', {})
            if ctx:
                data['form']['used_context'].update({'partner_id': data['form']['partner_id'][0]})
            else:
                data['form'].update({'used_context': {'partner_id': data['form']['partner_id'][0]}})
        res = super(partner_ledger_zateg, self).set_context(objects, data, ids, report_type=report_type)
        if data['form']['hide_zero']:
            objects = self.localcontext['objects']
            new_objs = []
            for partner in objects:
                debit = self._sum_debit_partner(partner)
                credit = self._sum_credit_partner(partner)
                if debit or credit:
                    new_objs.append(partner)
            self.localcontext['objects'] = new_objs

        return res

from openerp.netsvc import Service
del Service._services['report.account.third_party_ledger']
del Service._services['report.account.third_party_ledger_other']

report_sxw.report_sxw('report.account.third_party_ledger', 'res.partner',
        'addons/z_account/report/account_partner_ledger.rml',parser=partner_ledger_zateg,
        header='internal')

report_sxw.report_sxw('report.account.third_party_ledger_other', 'res.partner',
        'addons/z_account/report/account_partner_ledger_other.rml',parser=partner_ledger_zateg,
        header='internal')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
