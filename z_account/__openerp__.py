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


{
    'name': 'Z - Account',
    'version': '1.1',
    'category': 'Zetags',
    'description': """
        1. Modify Balance Sheet report
     """,
    'author': 'An Le <lehoangan1988@gmail.com>',
    'images': [],
    'depends': ["account"],
    'data': [
        'wizard/account_financial_report_view.xml',
        'wizard/account_report_aged_partner_balance_view.xml',
        'wizard/account_report_partner_ledger_view.xml',
        'wizard/account_report_partner_balance_view.xml',
        'wizard/account_report_partner_transaction_view.xml',
        'wizard/account_report_general_ledger_view.xml',


        'report/report_define.xml',
        'view/forex_voucher_view.xml',
        'view/account_move_view.xml',
        'view/payment_methods_view.xml',

        'security/ir.model.access.csv',
        'security/security.xml',
    ],
    'demo': [],
    'test': [
    ],
    'css':[
        'static/src/css/account.css',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
