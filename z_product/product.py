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
import openerp.addons.decimal_precision as dp

def rounding(f, r):
    if not r:
        return f
    return round(f / r) * r

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
    
product_tariff_code()

class product_template(osv.osv):
    _inherit = "product.template"
    _columns = {
        'description': fields.char('Description', size=60, translate=True),
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

    def _get_list_price(self, cr, uid, ids, field_names, arg=None, context=None):
        result = {}
        if not ids: return result
        pricelis_ids = self.pool.get('product.pricelist').search(cr, uid, [('show', '=', True)])
        show_price = self.pool.get('show.product.price')
        for id in ids:

            all_ids = []
            for pricelist_id in pricelis_ids:
                show_ids = show_price.search(cr, uid, [('product_id', '=', id), ('pricelist_id', '=', pricelist_id)])
                if not show_ids:
                    show_id = show_price.create(cr, uid, {
                        'product_id': id,
                        'pricelist_id': pricelist_id
                    })
                    show_ids += [show_id]
                all_ids += show_ids

            result.setdefault(id, all_ids)
        return result

    def _get_list_price_text(self, cr, uid, ids, field_names, arg=None, context=None):
        result = {}
        if not ids: return result

        for prod in self.browse(cr, uid, ids, context):
            all_ids = []
            for pricelist in prod.price_ids:
                all_ids.append('%s: %s'%(pricelist.pricelist_id.name, '{0:.2f}'.format(pricelist.price)))

            result.update({prod.id: '\n'.join(all_ids)})
        return result
    
    _columns = {
        'ean13': fields.char('Barcode', size=30, help="International Article Number used for product identification."),
        'track_inventory': fields.boolean('Track Inventory'),
        'hide': fields.boolean('Hide'),
        
        'packaging_id': fields.many2one('packaging', 'Packaging'),
        'ul_id': fields.many2one('product.ul', 'Type of Package', required=True),
        'product_tariff_code_id': fields.many2one('product.tariff.code', 'HS Tariff Code'),
        'component_ids': fields.one2many('mrp.bom', 'main_product_id', 'Components'),
        
        'est_sell_price': fields.function(_compute_sell_price,
            string="Est Sell Price", type="float", digits_compute=dp.get_precision('Product Price'),
                store={
                    'product.product': (lambda self, cr, uid, ids, c={}: ids, ['component_ids'], 20),
                    'mrp.bom': (_get_product, ['product_id','product_uom','product_qty'], 30),
                }),
        'price_ids': fields.function(_get_list_price, method=True, type='one2many', relation='show.product.price',
                                     string='List Price'),
        'price_text': fields.function(_get_list_price_text, method=True, type='text', string='List Price'),
        'dimension_l': fields.float('L', digits=(16,2)),
        'dimension_w': fields.float('W', digits=(16, 2)),
        'dimension_h': fields.float('H', digits=(16, 2)),
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
        for product in self.browse(cr, uid, ids, context):
            for line in product.price_ids:
                line.unlink()
        return super(product_product,self).unlink(cr, uid, ids, context=context)
    
product_product()

class zetag_product_pricelist(osv.osv):
    _inherit = "product.pricelist"
    _columns = {
        'rate': fields.float('Rate', digits=(12,6)),
        'show': fields.boolean('Show in Multi Currency List'),
    }

    def price_get_multi(self, cr, uid, pricelist_ids, products_by_qty_by_partner, context=None):
        """multi products 'price_get'.
           @param pricelist_ids:
           @param products_by_qty:
           @param partner:
           @param context: {
             'date': Date of the pricelist (%Y-%m-%d),}
           @return: a dict of dict with product_id as key and a dict 'price by pricelist' as value
        """

        def _create_parent_category_list(id, lst):
            if not id:
                return []
            parent = product_category_tree.get(id)
            if parent:
                lst.append(parent)
                return _create_parent_category_list(parent, lst)
            else:
                return lst
        # _create_parent_category_list

        if context is None:
            context = {}

        date = context.get('date') or time.strftime('%Y-%m-%d')

        currency_obj = self.pool.get('res.currency')
        product_obj = self.pool.get('product.product')
        product_category_obj = self.pool.get('product.category')
        product_uom_obj = self.pool.get('product.uom')
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        price_type_obj = self.pool.get('product.price.type')

        # product.pricelist.version:
        if not pricelist_ids:
            pricelist_ids = self.pool.get('product.pricelist').search(cr, uid, [], context=context)

        pricelist_version_ids = self.pool.get('product.pricelist.version').search(cr, uid, [
                                                        ('pricelist_id', 'in', pricelist_ids),
                                                        '|',
                                                        ('date_start', '=', False),
                                                        ('date_start', '<=', date),
                                                        '|',
                                                        ('date_end', '=', False),
                                                        ('date_end', '>=', date),
                                                    ])
        if len(pricelist_ids) != len(pricelist_version_ids):
            raise osv.except_osv(_('Warning!'), _("At least one pricelist has no active version !\nPlease create or activate one."))

        # product.product:
        product_ids = [i[0] for i in products_by_qty_by_partner]
        #products = dict([(item['id'], item) for item in product_obj.read(cr, uid, product_ids, ['categ_id', 'product_tmpl_id', 'uos_id', 'uom_id'])])
        products = product_obj.browse(cr, uid, product_ids, context=context)
        products_dict = dict([(item.id, item) for item in products])

        # product.category:
        product_category_ids = product_category_obj.search(cr, uid, [])
        product_categories = product_category_obj.read(cr, uid, product_category_ids, ['parent_id'])
        product_category_tree = dict([(item['id'], item['parent_id'][0]) for item in product_categories if item['parent_id']])

        results = {}
        for product_id, qty, partner in products_by_qty_by_partner:
            for pricelist_id in pricelist_ids:
                price = False

                tmpl_id = products_dict[product_id].product_tmpl_id and products_dict[product_id].product_tmpl_id.id or False

                categ_id = products_dict[product_id].categ_id and products_dict[product_id].categ_id.id or False
                categ_ids = _create_parent_category_list(categ_id, [categ_id])
                if categ_ids:
                    categ_where = '(categ_id IN (' + ','.join(map(str, categ_ids)) + '))'
                else:
                    categ_where = '(categ_id IS NULL)'

                if partner:
                    partner_where = 'base <> -2 OR %s IN (SELECT name FROM product_supplierinfo WHERE product_id = %s) '
                    partner_args = (partner, tmpl_id)
                else:
                    partner_where = 'base <> -2 '
                    partner_args = ()

                cr.execute(
                    'SELECT i.*, pl.currency_id, pl.rate as z_rate '
                    'FROM product_pricelist_item AS i, '
                        'product_pricelist_version AS v, product_pricelist AS pl '
                    'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = %s) '
                        'AND (product_id IS NULL OR product_id = %s) '
                        'AND (' + categ_where + ' OR (categ_id IS NULL)) '
                        'AND (' + partner_where + ') '
                        'AND price_version_id = %s '
                        'AND (min_quantity IS NULL OR min_quantity <= %s) '
                        'AND i.price_version_id = v.id AND v.pricelist_id = pl.id '
                    'ORDER BY sequence',
                    (tmpl_id, product_id) + partner_args + (pricelist_version_ids[0], qty))
                res1 = cr.dictfetchall()
                uom_price_already_computed = False
                for res in res1:
                    if res:
                        if res['base'] == -1:
                            if not res['base_pricelist_id']:
                                price = 0.0
                            else:
                                price_tmp = self.price_get(cr, uid,
                                        [res['base_pricelist_id']], product_id,
                                        qty, context=context)[res['base_pricelist_id']]
                                ptype_src = self.browse(cr, uid, res['base_pricelist_id']).currency_id.id
                                uom_price_already_computed = True
                                price = currency_obj.compute(cr, uid,
                                        ptype_src, res['currency_id'],
                                        price_tmp, round=False,
                                        context=context)
                        elif res['base'] == -2:
                            # this section could be improved by moving the queries outside the loop:
                            where = []
                            if partner:
                                where = [('name', '=', partner) ]
                            sinfo = supplierinfo_obj.search(cr, uid,
                                    [('product_id', '=', tmpl_id)] + where)
                            price = 0.0
                            if sinfo:
                                qty_in_product_uom = qty
                                from_uom = context.get('uom') or product_obj.read(cr, uid, [product_id], ['uom_id'])[0]['uom_id'][0]
                                supplier = supplierinfo_obj.browse(cr, uid, sinfo, context=context)[0]
                                seller_uom = supplier.product_uom and supplier.product_uom.id or False
                                if seller_uom and from_uom and from_uom != seller_uom:
                                    qty_in_product_uom = product_uom_obj._compute_qty(cr, uid, from_uom, qty, to_uom_id=seller_uom)
                                else:
                                    uom_price_already_computed = True
                                cr.execute('SELECT * ' \
                                        'FROM pricelist_partnerinfo ' \
                                        'WHERE suppinfo_id IN %s' \
                                            'AND min_quantity <= %s ' \
                                        'ORDER BY min_quantity DESC LIMIT 1', (tuple(sinfo),qty_in_product_uom,))
                                res2 = cr.dictfetchone()
                                if res2:
                                    price = res2['price']
                        else:
                            price_type = price_type_obj.browse(cr, uid, int(res['base']))
                            uom_price_already_computed = True
                            price = product_obj.price_get(cr, uid, [product_id], price_type.field, context=context)[product_id]
                            # price = currency_obj.compute(cr, uid,
                            #         price_type.currency_id.id, res['currency_id'],
                            #         product_obj.price_get(cr, uid, [product_id],
                            #         price_type.field, context=context)[product_id], round=False, context=context)

                        if price is not False:
                            price_limit = price
                            price = price * (1.0+(res['price_discount'] or 0.0))
                            price = rounding(price, res['price_round']) #TOFIX: rounding with tools.float_rouding
                            price += (res['price_surcharge'] or 0.0)
                            if res['price_min_margin']:
                                price = max(price, price_limit+res['price_min_margin'])
                            if res['price_max_margin']:
                                price = min(price, price_limit+res['price_max_margin'])
                            if res['z_rate']:
                                price = rounding(price * res['z_rate'], res['price_round'])
                            break

                    else:
                        # False means no valid line found ! But we may not raise an
                        # exception here because it breaks the search
                        price = False

                if price:
                    results['item_id'] = res['id']
                    if 'uom' in context and not uom_price_already_computed:
                        product = products_dict[product_id]
                        uom = product.uos_id or product.uom_id
                        price = product_uom_obj._compute_price(cr, uid, uom.id, price, context['uom'])

                if results.get(product_id):
                    results[product_id][pricelist_id] = price
                else:
                    results[product_id] = {pricelist_id: price}

        return results
zetag_product_pricelist()

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
