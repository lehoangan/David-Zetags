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

class packaging(osv.osv):
    _name = "packaging"
    _columns = {
        'index': fields.integer('Index', required=True),
        'name': fields.char('Description', size=50, required=True),
    }
    
packaging()

class product_tariff_code(osv.osv):
    _name = "product.tariff.code"
    _columns = {
        'name': fields.char('Description', size=50, required=True),
    }
    
packaging()

class product_template(osv.osv):
    _inherit = "product.template"
    _columns = {
        'description': fields.char('Description', size=50, translate=True),
    }
    
product_template()

class product_product(osv.osv):
    _inherit = "product.product"
    
    def _compute_sell_price(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            total = 0.0
            for line in obj.component_ids:
                total += line.list_price
            result[obj.id] = total
        return result
    
    def _get_product(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('mrp.bom').browse(cr, uid, ids, context=context):
            if line.main_product_id:
                result[line.main_product_id.id] = True
        return result.keys()
    
    _columns = {
        'ean13': fields.char('Barcode', size=30, help="International Article Number used for product identification."),
        'track_inventory': fields.boolean('Track Inventory'),
        'hide': fields.boolean('Hide'),
        
        'packaging_id': fields.many2one('packaging', 'Packaging'),
        'product_tariff_code_id': fields.many2one('product.tariff.code', 'HS Tariff Code'),
        'component_ids': fields.one2many('mrp.bom', 'main_product_id', 'Components'),
        
        'est_sell_price': fields.function(_compute_sell_price,
            string="Est Sell Price", type="float", digits_compute=dp.get_precision('Product Price'),
                store={
                    'product.product': (lambda self, cr, uid, ids, c={}: ids, ['component_ids'], 20),
                    'mrp.bom': (_get_product, ['product_id','product_uom','product_qty'], 30),
                }),
    }
    
    def _check_ean_key(self, cr, uid, ids, context=None):
#         for product in self.read(cr, uid, ids, ['ean13'], context=context):
#             res = check_ean(product['ean13'])
#         return res
        return True
    _constraints = [(_check_ean_key, 'You provided an invalid "EAN13 Barcode" reference. You may use the "Internal Reference" field instead.', ['ean13'])]
    
    def copy(self, cr, uid, id, default=None, context=None):
        if context is None:
            context={}

        if not default:
            default = {}

        product = self.read(cr, uid, id, ['property_account_income','property_account_expense'], context=context)
        default = default.copy()
        if product['property_account_income']:
            default.update(property_account_income=product['property_account_income'][0])
        if product['property_account_expense']:
            default.update(property_account_expense=product['property_account_expense'][0])
        return super(product_product, self).copy(cr, uid, id, default=default,
                context=context)

    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []
        #Thanh: Just show only Product Name
        def _name_get(d):
            name = d.get('name','')
            # code = d.get('default_code',False)
            # if code:
            #     name = '[%s] %s' % (code,name)
            # if d.get('variants'):
            #     name = name + ' - %s' % (d['variants'],)
            return (d['id'], name)

        partner_id = context.get('partner_id', False)

        result = []
        for product in self.browse(cr, user, ids, context=context):
            sellers = filter(lambda x: x.name.id == partner_id, product.seller_ids)
            if sellers:
                for s in sellers:
                    mydict = {
                              'id': product.id,
                              'name': s.product_name or product.name,
                              'default_code': s.product_code or product.default_code,
                              'variants': product.variants
                              }
                    result.append(_name_get(mydict))
            else:
                mydict = {
                          'id': product.id,
                          'name': product.name,
                          'default_code': product.default_code,
                          'variants': product.variants
                          }
                result.append(_name_get(mydict))
        return result
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('name',False):
            vals.update({'default_code': vals['name'],
                         'ean13': vals['name'],
                         'manufacturer_pname': vals['name'],
                         'manufacturer_pref': vals['name']})
        return super(product_product,self).write(cr, uid, ids, vals, context=context)
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('name',False):
            vals.update({'default_code': vals['name'],
                         'ean13': vals['name'],
                         'manufacturer_pname': vals['name'],
                         'manufacturer_pref': vals['name']})
        return super(product_product,self).create(cr, uid, vals, context=context)
    
    def unlink(self, cr, uid, ids, context=None):
        bom = self.pool.get('mrp.bom')
        bom_ids = bom.search(cr, uid, [('product_id','in',ids)])
        bom.unlink(cr, uid, bom_ids)
        return super(product_product,self).unlink(cr, uid, ids, context=context)
    
product_product()

class product_pricelist(osv.osv):
    _inherit = "product.pricelist"
    _columns = {
        'rate': fields.float('Rate', digits=(12,6)),
    }

class mrp_bom(osv.osv):
    _inherit = 'mrp.bom'
    
    def _get_bom_price_total(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            total = 0.0
            for line in obj.bom_lines:
                total += line.list_price
            result[obj.id] = total
        return result
    
    def _get_list_price(self, cr, uid, ids, name, args, context=None):
        uom = self.pool.get('product.uom')
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            price = uom._compute_price(cr, uid, obj.product_id.uom_id.id, obj.product_id.list_price, to_uom_id=obj.product_uom.id)
            result[obj.id] = price * obj.product_qty
        return result
    
    def _get_parent_bom(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('mrp.bom').browse(cr, uid, ids, context=context):
            if line.bom_id:
                result[line.bom_id.id] = True
        return result.keys()
    
    _columns = {
        'list_price': fields.function(_get_list_price,
            string="Price", type="float", digits_compute=dp.get_precision('Product Price'),
                store={
                    'mrp.bom': (lambda self, cr, uid, ids, c={}: ids, ['product_id','product_uom','product_qty'], 10),
                }),
        
        'bom_price_total': fields.function(_get_bom_price_total,
            string="Price Total", type="float", digits_compute=dp.get_precision('Product Price'),
                store={
                    'mrp.bom': (lambda self, cr, uid, ids, c={}: ids, ['bom_lines'], 20),
                    'mrp.bom': (_get_parent_bom, ['product_id','product_uom','product_qty'], 30),
                }),
        'main_product_id': fields.many2one('product.product', 'Main Product', ondelete="cascade"),
        
    }

    def _check_existing_bom(self, cr, uid, ids, context=None):
        boms = self.browse(cr, uid, ids, context=context)
        for bom in boms:
            exist_ids = self.search(cr, uid, [('id','!=',bom.id),('bom_id','=',False),('product_id','=',bom.product_id.id)])
            if exist_ids:
                return False
        return True

    _constraints = [
        (_check_existing_bom, 'Error ! These is an existing BOM for this Product.', []),
    ]

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if not vals.get('bom_id',False) and vals.get('main_product_id',False):
            exist_bom_ids = self.pool.get('mrp.bom').search(cr, uid, [('product_id','=',vals['main_product_id'])])
            if exist_bom_ids:
                vals.update({'bom_id':exist_bom_ids[0]})
            else:
                value = self.onchange_product_id(cr, uid, [], vals['main_product_id'], False, context=context)
                value = value['value']
                value.update({'product_id':vals['main_product_id']})
                new_bom_id = self.create(cr, uid, value)
                vals.update({'bom_id':new_bom_id})
        return super(mrp_bom, self).create(cr, uid, vals, context=context)

    def _auto_init(self, cr, context=None):
        super(mrp_bom, self)._auto_init(cr, context)

        #Thanh:
        cr.execute('''
        select id, product_id
        from mrp_bom
        where bom_id IS NULL
        ''')
        res = cr.fetchall()
        for line in res:
            cr.execute("UPDATE mrp_bom SET main_product_id=%s WHERE bom_id=%s"%(line[1],line[0]))

mrp_bom()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
