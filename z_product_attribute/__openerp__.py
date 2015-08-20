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
    'name': 'Z - Product Attributes',
    'version': '1.1',
    'category': 'Zetags',
    'description': """
    1) "- Add new table called “Attributes” and allow group and attribute sub group. Create Menu Product Attributes below Menu Products
         + Example open window for Attributes and add Group called Colour
         + Allow to create group and add attributes such as white, green , red etc
        
        - In Product Form:
         + In product “Procurements” TAB change under “Attributes” heading make “Attribute” 
         + Lookup new Attributes Group
         + Then for Attributes value lookup newly created Attributes value: Atribute = Colour Value = green, red, yellow"   
    """,
    'author': 'Le Hoang An <lehoangan1988@gmail.com>',
    'images': [],
    'depends': ['z_base','z_product','product_manufacturer'],
    'data': [
             'product_view.xml',
    ],
    'demo': [],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
