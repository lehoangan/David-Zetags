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

class delivery_carrier(osv.osv):
    _inherit = "delivery.carrier"
    _order = 'name'
    _columns = {
        'minimum_charge_per_shipment': fields.float('Minimum charge per shipment'),
        
        'delivery_grid_lines': fields.one2many('delivery.grid.line', 'carrier_id', 'Delivery Grid Line'),
        
        'account_id': fields.many2one('account.account', 'Delivery Account', required=True, domain="[('type','!=','view')]"),
    }
delivery_carrier()

class delivery_grid(osv.osv):
    _inherit = "delivery.grid"
    _columns = {
        'region_ids': fields.many2many('res.region', 'delivery_grid_region_rel', 'grid_id', 'region_id', 'Regions'),
        
        'product_categ_id': fields.many2one('product.category','Product Category', domain="[('type','=','normal')]"),
    }
    
    def get_price(self, cr, uid, id, order, dt, context=None):
        total = 0
        weight = 0
        volume = 0
        units = 0
        for line in order.order_line:
            if not line.product_id:
                continue
            total += line.price_subtotal or 0.0
            weight += (line.product_id.weight or 0.0) * line.product_uom_qty
            volume += (line.product_id.volume or 0.0) * line.product_uom_qty
            
            #Thanh: Add Unit condition
            units += line.product_uom_qty


        return self.get_price_from_picking(cr, uid, id, total,weight, volume, units, context=context)
    
    def get_price_from_picking(self, cr, uid, id, total, weight, volume, units, context=None):
        grid = self.browse(cr, uid, id, context=context)
        price = 0.0
        ok = False

        for line in grid.line_ids:
            price_dict = {'price': total, 'volume':volume, 'weight': weight, 'wv':volume*weight, 'units': units}
            test = eval(line.type+line.operator+str(line.max_value), price_dict)
            if test:
                if line.price_type=='variable':
                    price = line.list_price * price_dict[line.variable_factor]
                else:
                    price = line.list_price
                ok = True
                
                #Thanh: Check if price less than minimum then get the minimum price
                if price < line.min_price:
                    price = line.min_price
                break
        if not ok:
            raise osv.except_osv(_('No price available!'), _('No line matched this product or order in the chosen delivery grid.'))

        return price
    
delivery_grid()

class delivery_grid_line(osv.osv):
    _inherit = "delivery.grid.line"
    _columns = {
        'type': fields.selection([('units','Units'),
                                  ('weight','Weight'),
                                  ('volume','Volume'),
                                  ('wv','Weight * Volume'), 
                                  ('price','Price')],
                                  'Variable', required=True),
        'min_price': fields.float('Min. Price', required=True),
        
        'grid_id': fields.many2one('delivery.grid', 'Delivery Category',required=True, ondelete='cascade'),
        
        'carrier_id': fields.many2one('delivery.carrier', 'Carrier', ondelete='cascade'),
        
    }
    
    def _auto_init(self, cr, context=None):
        super(delivery_grid_line, self)._auto_init(cr, context)
        cr.execute('''
        select dgl.id, dg.carrier_id
        from delivery_grid_line dgl join delivery_grid dg on dgl.grid_id = dg.id
        where dgl.carrier_id IS NULL
        ''')
        res = cr.fetchall()
        for line in res:
            cr.execute("UPDATE delivery_grid_line SET carrier_id=%s WHERE id=%s"%(line[1],line[0]))
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('grid_id',False):
            cr.execute('''
                select carrier_id
                from delivery_grid
                where id=%s
                '''%(vals['grid_id']))
            res = [x[0] for x in cr.fetchall()]
            vals.update({'carrier_id': res and res[0] or False})
        return super(delivery_grid_line, self).write(cr, uid, ids, vals, context=context)
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('grid_id',False) and not vals.get('carrier_id',False):
            cr.execute('''
                select carrier_id
                from delivery_grid
                where id=%s
                '''%(vals['grid_id']))
            res = [x[0] for x in cr.fetchall()]
            vals.update({'carrier_id': res and res[0] or False})
        return super(delivery_grid_line, self).create(cr, uid, vals, context=context)
    
delivery_grid_line()
 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
