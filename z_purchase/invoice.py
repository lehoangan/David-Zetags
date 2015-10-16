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
import openerp
import openerp.addons.decimal_precision as dp
from openerp import netsvc
from openerp.tools import float_compare

class account_invoice(osv.osv):
    _inherit = "account.invoice"

    def onchange_date_invoice(self, cr, uid, ids, date_invoice, partner_id, payment_term, context):
        result = {'value': {}}
        if partner_id and date_invoice:
            p = self.pool.get('res.partner').browse(cr, uid, partner_id)
            partner_payment_term = p.property_supplier_payment_term and p.property_supplier_payment_term.id or False
            if not payment_term:
                payment_term = partner_payment_term
            if payment_term:
                to_update = self.onchange_payment_term_date_invoice(
                    cr, uid, ids, partner_payment_term, date_invoice)
                result['value'].update(to_update['value'])
            else:
                result['value']['date_due'] = False
        return result



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
