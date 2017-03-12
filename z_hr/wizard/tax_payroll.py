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

class tax_payroll_wizard(osv.osv_memory):
    _name = 'tax.payroll.wizard'
    _columns = {
        'date_start': fields.date('Date Start'),
        'date_stop': fields.date('Date Stop'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'basic_ids': fields.many2many('account.account', string='Basic Accounts', domain=[('type', '!=', 'view')]),
        'tax_ids': fields.many2many('account.account', string='Tax Accounts', domain=[('type', '!=', 'view')]),
        'super_ids': fields.many2many('account.account', string='Superannuation Accounts', domain=[('type', '!=', 'view')]),
        'net_ids': fields.many2many('account.account', string='Net Accounts', domain=[('type', '!=', 'view')]),
    }

    # def _get_basic_ids(self, cr, uid, context=None):
    #     account_ids = self.pool.get('account.account').search(cr, uid, [('name', 'like', 'Wages & Salaries')])
    #     return account_ids
    #
    # def _get_tax_ids(self, cr, uid, context=None):
    #     account_ids = self.pool.get('account.account').search(cr, uid, [('name', 'like', 'Wages & Salaries')])
    #     return account_ids
    #
    # def _get_super_ids(self, cr, uid, context=None):
    #     account_ids = self.pool.get('account.account').search(cr, uid, [('name', 'like', 'Wages & Salaries')])
    #     return account_ids
    #
    # def _get_net_ids(self, cr, uid, context=None):
    #     account_ids = self.pool.get('account.account').search(cr, uid, [('name', 'like', 'Wages & Salaries')])
    #     return account_ids

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid,
                                                                                                 'account.invoice',
                                                                                                 context=c),
        # 'basic_ids': _get_basic_ids,
        # 'tax_ids': _get_tax_ids,
        # 'super_ids': _get_super_ids,
        # 'net_ids': _get_net_ids,
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
            'report_name':'tax.payroll.zetags',
            'datas' : datas,
       }

tax_payroll_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
