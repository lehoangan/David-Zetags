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
from openerp import SUPERUSER_ID
import netsvc

class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def has_valuation_moves(self, cr, uid, move):
        return self.pool.get('account.move').search(cr, uid, [
            ('ref', '=', move.picking_id.name),
            ])

    def action_revert_done(self, cr, uid, ids, context=None):
        if not len(ids):
            return False
        for picking in self.browse(cr, uid, ids, context):
            for line in picking.move_lines:
                if self.has_valuation_moves(cr, uid, line):
                    raise orm.except_orm(
                        _('Error'),
                        _('Line %s has valuation moves (%s). \
                            Remove them first') % (line.name,
                                                   line.picking_id.name))
                line.write({'state': 'draft'})
            self.write(cr, uid, [picking.id], {'state': 'draft'})
            if picking.invoice_state == 'invoiced' and not picking.invoice_id:
                self.write(cr, uid, [picking.id],
                           {'invoice_state': '2binvoiced'})
            wf_service = netsvc.LocalService("workflow")
            # Deleting the existing instance of workflow
            wf_service.trg_delete(uid, 'stock.picking', picking.id, cr)
            wf_service.trg_create(uid, 'stock.picking', picking.id, cr)
        for (id, name) in self.name_get(cr, uid, ids):
            message = _(
                "The stock picking '%s' has been set in draft state."
                ) % (name,)
            self.log(cr, uid, id, message)
        return True


class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'

    def action_revert_done(self, cr, uid, ids, context=None):
        #override in order to redirect to stock.picking object
        return self.pool.get('stock.picking').action_revert_done(
            cr, uid, ids, context=context)


class stock_picking_in(osv.osv):
    _inherit = 'stock.picking.in'

    def action_revert_done(self, cr, uid, ids, context=None):
        #override in order to redirect to stock.picking object
        return self.pool.get('stock.picking').action_revert_done(
            cr, uid, ids, context=context)

class stock_move(osv.osv):
    _inherit = "stock.move"
    
    def _get_product_attribute(self, cr, uid, ids, name, args, context=None):
        res = {}
        for move in self.browse(cr, uid, ids, context=context):
            res[move.id] = ''
            for attribute in move.product_id.attribute_ids:
                res[move.id] += attribute.name.name + '=' + attribute.value.name + ', '
            if res[move.id] != '':
                res[move.id] = res[move.id][:-2]
        return res
    
    _columns = {
        'attributes': fields.function(_get_product_attribute, type='text', string='Attributes',
            store={
                'stock.move': (lambda self, cr, uid, ids, c={}: ids, ['product_id'], 20),
            }),
    }
    
    def _auto_init(self, cr, context=None):
        super(stock_move, self)._auto_init(cr, context)
        cr.execute('''
        select id
        from stock_move
        where attributes IS NULL
        ''')
        res_ids = [x[0] for x in cr.fetchall()]
        for stock_move_id in res_ids:
            data = self._get_product_attribute(cr, SUPERUSER_ID, [stock_move_id], False, False, context=context)
            cr.execute("UPDATE stock_move SET attributes='%s' WHERE id=%s"%(data[stock_move_id],stock_move_id))
            
stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
