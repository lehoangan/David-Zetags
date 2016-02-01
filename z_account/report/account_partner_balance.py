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
from account.report.account_partner_balance import partner_balance
from openerp.report import report_sxw

class partner_balance_zateg(partner_balance):

    def __init__(self, cr, uid, name, context=None):
        super(partner_balance_zateg, self).__init__(cr, uid, name, context=context)
        self.account_ids = []
        self.localcontext.update( {
            'time': time,
            'lines': self.lines,
            'sum_debit': self._sum_debit,
            'sum_credit': self._sum_credit,
            'sum_litige': self._sum_litige,
            'get_fiscalyear': self._get_fiscalyear,
            'get_journal': self._get_journal,
            'get_filter': self._get_filter,
            'get_account': self._get_account,
            'get_start_date':self._get_start_date,
            'get_end_date':self._get_end_date,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period,
            'get_partners':self._get_partners,
            'get_target_move': self._get_target_move,
        })

    def set_context(self, objects, data, ids, report_type=None):
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
        return super(partner_balance_zateg, self).set_context(objects, data, ids, report_type=report_type)

from openerp.netsvc import Service
del Service._services['report.account.partner.balance']

report_sxw.report_sxw('report.account.partner.balance', 'res.partner', 'account/report/account_partner_balance.rml',parser=partner_balance_zateg, header="internal")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
