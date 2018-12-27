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

class invoice_payment_statement_wizard(osv.osv_memory):
    _name = 'invoice.payment.statement.wizard'
    _columns = {
        'date_start': fields.date('Date Start'),
        'date_stop': fields.date('Date Stop'),
        'partner_id': fields.many2one(
            'res.partner', 'Customer', required=True),
        'currency_id': fields.many2one(
            'res.currency', 'Currency', required=True),
    }
    def _get_uds(self, cr, uid, context):
        ids =self.pool.get('res.currency').search(
            cr, uid, [('name', '=', 'USD')])
        return ids and ids[0] or False

    _defaults = {
        'currency_id': _get_uds,
    }

    def print_report(self, cr, uid, ids, context=None):
        """ To print the report of Product cost structure
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param context: A standard dictionary
        @return : Report
        """
        if context is None:
            context = {}
        datas = {'ids' : context.get('active_ids',[])}
        res = self.read(cr, uid, ids, [])
        res = res and res[0] or {}
        datas['form'] = res

        return {
            'type' : 'ir.actions.report.xml',
            'report_name':'account.payment.statement.zetags',
            'datas' : datas,
       }

invoice_payment_statement_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
