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

class account_partner_ledger(osv.osv_memory):
    _inherit = 'account.partner.ledger'
    _columns = {
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'partner_id': fields.many2one('res.partner', 'Filter Partner'),
        'hide_zero': fields.boolean('Hide Zero Transactions'),
        'unpaid_invoice': fields.boolean('Only Unpaid Invoices'),
    }
    _defaults = {
        'hide_zero': True,
        'unpaid_invoice': True, }

    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['unpaid_invoice', 'initial_balance', 'filter', 'page_split', 'amount_currency', 'currency_id', 'partner_id', 'hide_zero'])[0])
        if data['form']['page_split']:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.third_party_ledger',
                'datas': data,
        }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.third_party_ledger_other',
                'datas': data,
        }

account_partner_ledger()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
