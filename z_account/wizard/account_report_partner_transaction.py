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

class account_partner_transaction(osv.osv_memory):
    _name = 'account.partner.transaction'
    _inherit = 'account.partner.ledger'
    _columns = {
        'journal_ids': fields.many2many('account.journal', 'zetag_account_partner_transation_journal_rel', 'account_id',
                                        'journal_id', 'Journals', required=True),
        'hide_zero': fields.boolean('Hide Zero Transactions'),
        'report_detail': fields.selection([('all', ' All Transaction'),
                                         ('invoice', 'Total Invoice Values'),
                                         ('payment', 'Total Payment Values')], 'Detail')
    }

    _defaults = {
        'hide_zero': True,
        'page_split': True,
        'report_detail': 'all',
    }

    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['report_detail','initial_balance', 'filter', 'page_split', 'amount_currency', 'currency_id', 'partner_id','hide_zero'])[0])
        if data['form']['partner_id']:
            data.update({
                'model': 'res.partner',
                'ids': [data['form']['partner_id'][0]]
            })
        if data['form']['page_split']:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.third_party_transaction',
                'datas': data,
        }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.third_party_transaction_other',
                'datas': data,
        }

account_partner_transaction()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
