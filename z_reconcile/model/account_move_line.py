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

class account_move_line(osv.osv):
    _inherit = "account.move.line"
    _columns = {
        'z_reconcile': fields.related('account_id', 'z_reconcile',string='Z-Reconcile', type='boolean'),
        'z_reconciled': fields.boolean('Bank Reconcile'),
    }

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


account_move_line()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
