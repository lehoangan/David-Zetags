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

import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime

class product_attribute_value(osv.osv):
    _name = "product.attribute.value"
    _columns = {
        'name' : fields.char('Value', size=64, required=True),
        'product_attribute_id': fields.many2one('product.attribute', 'Attribute', ondelete='cascade'),
    }
product_attribute_value()

class product_attribute(osv.osv):
    _name = "product.attribute"
    _columns = {
        'name' : fields.char('Attribute', size=64, required=True),
        'value' : fields.one2many('product.attribute.value', 'product_attribute_id', 'Value'),
    }
product_attribute()

class product_manufacturer_attribute(osv.osv):
    _inherit = "product.manufacturer.attribute"
    _columns = {
        'name' : fields.many2one("product.attribute", 'Attribute', required=True),
        'value' : fields.many2one('product.attribute.value', 'Value', domain="[('product_attribute_id','=',name)]", required=True),
    }
    
    def onchange_attribute(self, cr, uid, ids, name, context=None):
        v = {}
        v['value'] = False
        return {'value': v}
    
product_manufacturer_attribute()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
