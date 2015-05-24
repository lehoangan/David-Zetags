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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class ir_ui_menu(osv.osv):
    _inherit = "ir.ui.menu"

    _columns = {
    }
    
    def _auto_init(self, cr, context=None):
        super(ir_ui_menu, self)._auto_init(cr, context)
        #Thanh: Update Menu Parent Left and Right for module Marketing
        def browse_rec(root, pos=0):
            cr.execute("SELECT id FROM ir_ui_menu WHERE parent_id=%s order by sequence"%(root))
            pos2 = pos + 1
            for id in cr.fetchall():
                pos2 = browse_rec(id[0], pos2)
            cr.execute('update ir_ui_menu set parent_left=%s, parent_right=%s where id=%s', (pos, pos2, root))
            return pos2 + 1  
        query = "SELECT id FROM ir_ui_menu WHERE parent_id IS NULL and name='Marketing' order by sequence"
        pos = 0
        cr.execute(query)
        for (root,) in cr.fetchall():
            pos = browse_rec(root, pos)
            
ir_ui_menu()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
