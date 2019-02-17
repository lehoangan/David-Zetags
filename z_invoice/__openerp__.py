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
    'name': 'Z - Invoice',
    'version': '1.1',
    'category': 'Zetags',
    'description': """
    """,
    'author': 'Le Hoang An <lehoangan1988@gmail.com>',
    'images': [],
    'depends': ['z_base','sale','account','account_cancel',
                'account_voucher','stock','sale_stock',
                'report_aeroo',
                'z_shipping_cost','z_product','z_product_attribute','z_customer'],
    'data': [
         "security/ir.model.access.csv",
         "sale_report.xml",
         "sale_view.xml",
         "invoice_view.xml",
         "voucher_view.xml",
         "account_move_view.xml",
         "account_journal_view.xml",
         "delivery_order_view.xml",
         "stock_report.xml",
         "account_report.xml",
         'menu.xml',
         "wizard/invoice_statement_view.xml",
         "wizard/invoice_payment_statement_view.xml",
         "wizard/warning_message_view.xml",
         "wizard/download_labels_view.xml",
    ],
    'demo': [],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
