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

class hr_payslip(osv.osv):
    _inherit = "hr.payslip"
    _columns = {
    }

    def hr_verify_sheet(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context):
            if not obj.line_ids:
                self.compute_sheet(cr, uid, [obj.id], context)
        return self.write(cr, uid, ids, {'state': 'verify'}, context=context)


hr_payslip()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
