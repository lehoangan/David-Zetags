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

from openerp.osv import fields, osv

class account_report_general_ledger(osv.osv_memory):
    _inherit = "account.report.general.ledger"

    _columns = {
        'account_filter': fields.selection([('all', 'All Accounts'), ('one', 'One Account')],
                                           'Account Filter', required=True),
        'account_filter_id': fields.many2one('account.account', 'Select Account'),
    }
    _defaults = {
        'account_filter': 'all',
    }

    def pre_print_report(self, cr, uid, ids, data, context=None):
        data = super(account_report_general_ledger, self).pre_print_report(cr, uid, ids, data, context)
        if context is None:
            context = {}
        vals = self.read(cr, uid, ids,
                         ['account_filter', 'account_filter_id'],
                         context=context)[0]
        data['form'].update(vals)
        return data
account_report_general_ledger()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
