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
    'name': 'Z - Customer',
    'version': '1.1',
    'category': 'Zetags',
    'description': """
    1) Menu Sales / Sales / Customers:
        - Remove Kanban view, Just show List + Form Views
        - Filter Cutomer who is a Company (Not contact)
    2) Add new menu Contacts below menu Customers:
        - Filter Contacts only
       """,
    'author': 'Le Hoang An <lehoangan1988@gmail.com>',
    'images': [],
    'depends': ['z_base','account','base_vat','product','sale','z_localization','z_shipping_cost'],
    'data': [
        'res_partner_view.xml',
    ],
    'demo': [],
    'test': [
    ],
    'js': [
        'static/src/js/show_popup_customer_alert.js',
    ],
    'css' : [
        "static/src/css/base.css",
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
