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
    'name': 'Z - Product',
    'version': '1.1',
    'category': 'Zetags',
    'description': """
    1) "In Product Form:
        - Move “Category” from main section to above “Internal Reference” and resize
        - Create a new field called “Description” and place in old Category position. Allow up to 30 chars.
        - Rename “EAN13 Bar Code” to just “Bar Code”
        - Bar code field has some restrictions in formatting for EAN13. Remove restrictions to allow up to 24 chars either numeric or alpha numeric mix.
        - Under “Procurements” TAB below Units of Measure add field “Track Inventory” with checkbox"
    2) "- Add new table called “Attributes” and allow group and attribute sub group. Create Menu Product Attributes below Menu Products
         + Example open window for Attributes and add Group called Colour
         + Allow to create group and add attributes such as white, green , red etc
        
        - In Product Form:
         + In product “Procurements” TAB change under “Attributes” heading make “Attribute” 
         + Lookup new Attributes Group
         + Then for Attributes value lookup newly created Attributes value: Atribute = Colour Value = green, red, yellow"   
    """,
    'author': 'Le Truong Thanh <thanh.lt1689@gmail.com>',
    'images': [],
    'depends': ['z_base','product','mrp'],
    'data': [
        'security/ir.model.access.csv',
        'product_view.xml',
        'bom_view.xml',
    ],
    'demo': [],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
