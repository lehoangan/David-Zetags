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
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class procurement_order(osv.osv):
    """
    Procurement Orders
    """
    _inherit = "procurement.order"

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms procurement and writes exception message if any.
        @return: True
        """
        move_obj = self.pool.get('stock.move')
        for procurement in self.browse(cr, uid, ids, context=context):
            if procurement.product_qty == 0.00:
                raise osv.except_osv(_('Data Insufficient!'),
                    _('Please check the quantity in procurement order(s) for the product "%s", it should not be 0 or less!' % procurement.product_id.name))
            if procurement.product_id.type in ('product', 'consu'):
                if not procurement.move_id:
                    source = procurement.location_id.id
                    if procurement.procure_method == 'make_to_order':
                        source = procurement.product_id.property_stock_procurement.id
                    id = move_obj.create(cr, uid, {
                        'name': procurement.product_qty > 0 and procurement.name or '%s (%s)'%(procurement.name, 'MINUS'),
                        'location_id': procurement.product_qty > 0 and source or procurement.location_id.id,
                        'location_dest_id': procurement.product_qty > 0 and procurement.location_id.id or source,
                        'product_id': procurement.product_id.id,
                        'product_qty': procurement.product_qty < 0 and -procurement.product_qty or procurement.product_qty,
                        'product_uom': procurement.product_uom.id,
                        'date_expected': procurement.date_planned,
                        'state': 'draft',
                        'company_id': procurement.company_id.id,
                        'auto_validate': True,
                    })
                    move_obj.action_confirm(cr, uid, [id], context=context)
                    self.write(cr, uid, [procurement.id], {'move_id': id, 'close_move': 1})
                elif procurement.product_qty <0:
                    source = procurement.move_id.location_id.id
                    dest = procurement.move_id.location_dest_id.id
                    procurement.move_id.write({'location_id': dest,
                                               'location_dest_id': source,
                                               'product_qty': - procurement.move_id.product_qty})

        self.write(cr, uid, ids, {'state': 'confirmed', 'message': ''})
        return True
