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
from account.report.account_general_ledger import general_ledger
from openerp.report import report_sxw

class general_ledger_zateg(general_ledger):

    def __init__(self, cr, uid, name, context=None):
        super(general_ledger_zateg, self).__init__(cr, uid, name, context=context)

    def set_context(self, objects, data, ids, report_type=None):
        if (data['form']['account_filter'] == 'one' and data['form']['account_filter_id']):
            new_ids = [data['form']['account_filter_id'][0]]
            objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
            data['model'] = 'account.report.general.ledger'
        return super(general_ledger_zateg, self).set_context(objects, data, ids, report_type=report_type)

from openerp.netsvc import Service
del Service._services['report.account.general.ledger']
del Service._services['report.account.general.ledger_landscape']

report_sxw.report_sxw('report.account.general.ledger', 'account.account', 'addons/account/report/account_general_ledger.rml', parser=general_ledger_zateg, header='internal')
report_sxw.report_sxw('report.account.general.ledger_landscape', 'account.account', 'addons/account/report/account_general_ledger_landscape.rml', parser=general_ledger_zateg, header='internal landscape')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
