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

class account_partner_balance(osv.osv_memory):
    _inherit = 'account.partner.balance'
    _columns = {
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'partner_id': fields.many2one('res.partner', 'Filter Partner'),
        'debit_credit_show': fields.selection([('both', 'Debit + Credit'),
                                               ('debit', 'Debit'),
                                               ('credit', 'credit')], 'Debit or Credit'),
        'report_type': fields.selection([('both', 'Invoice + Payment'),
                                        ('invoice', 'Invoice'),
                                        ('payment', 'Payment')], 'Invoice or Payment'),
    }

    _defaults = {
        'debit_credit_show': 'both',
        'report_type': 'both',
    }

    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['display_partner', 'currency_id', 'partner_id', 'debit_credit_show', 'report_type'])[0])
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.partner.balance',
            'datas': data,
    }

account_partner_balance()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
