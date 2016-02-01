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
        'tax_id': fields.many2one('account.tax', 'Tax'),
    }

    def onchange_tax_id(self, cr, uid, ids, tax_id, context=None):
        if not tax_id:
            return {'value': {}}

        tax_obj = self.pool.get('account.tax').browse(cr, uid, tax_id, context)
        return {'value': {'tax_code_id': tax_obj.tax_code_id and tax_obj.tax_code_id.id or False}}

account_move_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
