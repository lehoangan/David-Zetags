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
        self.partner_invoice = False
        self.partner_shipping = False
        self.date_order = ''
        self.carrier = ''
        self.ship_by = ''
        self.localcontext.update({
            'display_address': self.display_address,
            'get_bill_partner': self.get_bill_partner,
            'get_shipping_partner': self.get_shipping_partner,
            'get_date_order': self.get_date_order,
            'get_carrier': self.get_carrier,
            'get_ship_by': self.get_ship_by,
            'get_taxes': self.get_taxes,
        })
    
    def display_address(self, partner):
        address = self.pool.get('res.partner')._display_address(self.cr, self.uid, partner)
        return address
    
    def get_date_order(self):
        return self.date_order
    
    def get_carrier(self):
        return self.carrier
    
    def get_ship_by(self):
        return self.ship_by
    
    def get_bill_partner(self, invoice):
        if not self.partner_invoice:
            self.cr.execute('SELECT order_id FROM sale_order_invoice_rel WHERE invoice_id=%s'%(invoice.id))
            res = [x[0] for x in self.cr.fetchall()]
            self.partner_invoice = invoice.partner_id
            if len(res):
                order = self.pool.get('sale.order').browse(self.cr, self.uid, res[0])
                self.partner_invoice = order.partner_invoice_id
                self.date_order = order.date_order
                self.carrier = order.carrier_id.name or ''
                self.ship_by = order.carrier_id and order.carrier_id.partner_id.name or ''
        return self.partner_invoice
    
    def get_shipping_partner(self, invoice):
        if not self.partner_shipping:
            self.cr.execute('SELECT order_id FROM sale_order_invoice_rel WHERE invoice_id=%s'%(invoice.id))
            res = [x[0] for x in self.cr.fetchall()]
            self.partner_shipping = invoice.partner_id
            if len(res):
                self.partner_shipping = self.pool.get('sale.order').browse(self.cr, self.uid, res[0]).partner_shipping_id
        return self.partner_shipping
    
    def get_taxes(self, taxes):
        taxes = ''
        for tax in taxes:
            taxes += tax.name + ', '
        if len(taxes):
            taxes = taxes[:-2]
        return taxes


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
