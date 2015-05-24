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

class marketing_method(osv.osv):
    _name = "marketing.method"
    _columns = {
        'name': fields.char('Name', required=True, size=256, select=True),
    }

marketing_method()

class marketing_method_line(osv.osv):
    _name = "marketing.method.line"
    _columns = {
        'name': fields.char('Name', required=True, size=256, select=True),
        'method_id': fields.many2one('marketing.method', 'Method', required=True, ondelete='cascade', select=True)
    }

marketing_method_line()

class crm_lead(osv.osv):
    _inherit = "crm.lead"
    _columns = {
        'method_line_id': fields.many2one('marketing.method.line', 'Source', required=False, select=True)
    }
    
crm_lead()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
