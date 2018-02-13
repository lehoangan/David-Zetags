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
from openerp.tools import float_compare

class account_move(osv.osv):
    _inherit = "account.move"
    _columns = {
    }

    def copy(self, cr, uid, id, default=None, context=None):
        move_id = super(account_move, self).copy(cr, uid, id, default, context)
        for line in self.browse(cr, uid, move_id).line_id:
            line.write({'z_reconciled': False})
        return move_id

    def onchange_date(self, cr, uid, ids, date, context=None):
        if not date:
            return {'value': {'period_id': False}}

        periods = self.pool.get('account.period').find(cr, uid, dt=date, context=context)
        if periods:
            return {'value': {'period_id': periods[0]}}
        return {'value': {'period_id': False}}
account_move()

class account_move_line(osv.osv):
    _inherit = "account.move.line"

    def _get_status(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for line_id in ids:
            res[line_id] = False
        for line in self.browse(cursor, user, ids, context):
            res[line.id] = line.state
            if line.z_reconciled and line.state == 'valid':
                res[line.id] = 'reconcile'
        return res

    _columns = {
        'z_reconcile': fields.related('account_id', 'z_reconcile',string='Z-Reconcile', type='boolean'),
        'z_reconciled': fields.boolean('Bank Reconcile'),
        'fcstate': fields.function(_get_status, type='selection',
                                   selection=[('draft','Unbalanced'), ('valid','Balanced'), ('reconcile', 'Reconciled')],
                                   string='Status', readonly=True),
        'no_reconcile': fields.boolean('No Bank Reconcile', copy=False),
    }

    _defaults = {
        'no_reconcile': False,
    }

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default = default.copy()
        default.update(z_reconciled=False)
        return super(account_move_line, self).copy(cr, uid, id, default, context)

    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        for obj in self.browse(cr, uid, ids, context):
            if 'z_reconciled' in vals and not vals['z_reconciled']: continue
            if obj.fcstate == 'reconcile':
                raise osv.except_osv(_('Error!'), _('Please remove this entry in bank reconcile first'))
        return super(account_move_line, self).write(cr, uid, ids, vals, context, check, update_check)

    def unlink(self, cr, uid, ids, context=None):
        if type(ids) == type(1):
            ids = [ids]
        reconcile = self.pool.get('bank.reconcilation.line')
        reconcile_ids = reconcile.search(cr, uid, [('move_line_id', 'in', ids)])
        if reconcile_ids:
            for obj in reconcile.browse(cr, uid, reconcile_ids):
                if obj.order_id.state == 'draft' or not obj.choose:
                    obj.unlink()
                else:
                    raise osv.except_osv(_('Error!'), _('Please remove this entry in bank reconcile "%s" first')%obj.order_id.name)
        return super(account_move_line, self).unlink(cr, uid, ids, context)

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        result = []
        for line in self.browse(cr, uid, ids, context=context):
            if line.name and line.account_id.type == 'payable':
                result.append((line.id, (line.move_id.name or '')+' ('+line.name+')'))
            elif line.ref:
                result.append((line.id, (line.move_id.name or '') + ' (' + line.ref + ')'))
            else:
                result.append((line.id, line.move_id.name))
        return result


account_move_line()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
