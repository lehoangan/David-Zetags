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

from openerp.report import report_sxw

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.invoice = False
        self.localcontext.update({
            'display_address': self.display_address,
            'get_amount_paid': self.get_amount_paid,
            'get_amount_due': self.get_amount_due,
            'get_taxes': self.get_taxes,
        })
    
    def display_address(self, partner):
        address = self.pool.get('res.partner')._display_address(self.cr, self.uid, partner)
        return address
    
    def get_amount_paid(self, order):
        self.cr.execute('SELECT invoice_id FROM sale_order_invoice_rel WHERE order_id=%s'%(order.id))
        res = [x[0] for x in self.cr.fetchall()]
        if len(res):
            self.invoice = self.pool.get('account.invoice').browse(self.cr, self.uid, res[0])
            return self.invoice.amount_total - self.invoice.residual
        return 0.0
    
    def get_amount_due(self):
        if self.invoice:
            return self.invoice.residual
        return 0.0
    
    def get_taxes(self, taxes):
        taxes = ''
        for tax in taxes:
            taxes += tax.name + ', '
        if len(taxes):
            taxes = taxes[:-2]
        return taxes
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

