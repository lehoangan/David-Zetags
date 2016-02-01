##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
from account.report.account_aged_partner_balance import aged_trial_report
from openerp.report import report_sxw

class aged_trial_report_zateg(aged_trial_report):
    def __init__(self, cr, uid, name, context):
        super(aged_trial_report_zateg, self).__init__(cr, uid, name, context=context)
        self.total_account = []
        self.localcontext.update({
            'time': time,
            'get_lines_with_out_partner': self._get_lines_with_out_partner,
            'get_lines': self._get_lines,
            'get_total': self._get_total,
            'get_direction': self._get_direction,
            'get_for_period': self._get_for_period,
            'get_company': self._get_company,
            'get_currency': self._get_currency,
            'get_partners':self._get_partners,
            'get_account': self._get_account,
            'get_fiscalyear': self._get_fiscalyear,
            'get_target_move': self._get_target_move,
        })

    def set_context(self, objects, data, ids, report_type=None):
        if data['form']['currency_id']:
            ctx = data['form'].get('used_context', {})
            if ctx:
                data['form']['used_context'].update({'currency_id': data['form']['currency_id'][0]})
            else:
                data['form'].update({'used_context': {'currency_id': data['form']['currency_id'][0]}})
        return super(aged_trial_report_zateg, self).set_context(objects, data, ids, report_type=report_type)
from openerp.netsvc import Service
del Service._services['report.account.aged_trial_balance']

report_sxw.report_sxw('report.account.aged_trial_balance', 'res.partner',
        'addons/account/report/account_aged_partner_balance.rml',parser=aged_trial_report_zateg, header="internal landscape")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
