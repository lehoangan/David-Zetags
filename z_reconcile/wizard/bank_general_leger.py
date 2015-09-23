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

class bank_general_leger_wizard(osv.osv_memory):
    _name = 'bank.general.leger.wizard'
    _columns = {
        'date_start': fields.date('Date Start', required=True),
        'date_stop': fields.date('Date Stop', required=True),
        'account_id': fields.many2one('account.account', 'Account', required=True, domain="[('company_id','=',company_id),('z_reconcile', '=', True)]"),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.account', context=c),
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
            'report_name':'bank.general.leger',
            'datas' : datas,
       }

bank_general_leger_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
