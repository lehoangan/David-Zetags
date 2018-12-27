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
import datetime
from datetime import date, timedelta
from openerp.report import report_sxw

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.partner = False
        self.localcontext.update({
            'display_address': self.display_address,
            'get_data': self.get_data,
            'get_payement': self.get_current_payement,
            'get_partner': self.get_partner,
            'get_address': self.get_address,
            'get_total': self.get_total,
            'get_bill_partner': self.get_bill_partner,
            'time': time,
        })

    def get_total(self, form):
        domain = [('state', 'in', ('open', 'paid'))]
        opening_invoice_amount = 0
        if form['partner_id'] and form['date_start']:
            domain += [('partner_id', '=', form['partner_id'][0])]
            domain += [('date_invoice', '<', form['date_start'])]
            invoices = self.get_invoice(domain, form)
            opening_invoice_amount = sum([data['amount'] for data in invoices])

        invoices = self.get_data(form)
        invoice_amount = sum([data['amount'] for data in invoices])

        opening_payment_amount = 0
        domain = [('journal_id.type', 'in', ['bank', 'cash']),
                  ('type', '=', 'receipt'),
                  ('state', '=', 'posted')]
        if form['partner_id'] and form['date_start']:
            domain += [('partner_id', '=', form['partner_id'][0])]
            domain += [('date', '<', form['date_start'])]
            payments = self.detail_payment(domain, form)
            opening_payment_amount = sum([data['amount'] for data in payments])

        payments = self.get_current_payement(form)
        payment_amount = sum([data['amount'] for data in payments])

        opening_amount = opening_invoice_amount - opening_payment_amount
        ending_amount = opening_amount + invoice_amount
        ending_amount -= payment_amount
        return [(opening_amount, invoice_amount, payment_amount, ending_amount)]

    def get_current_payement(self, form):
        domain = [('journal_id.type', 'in', ['bank', 'cash']),
                  ('type','=','receipt'),
                  ('state', '=', 'posted')]
        if form['partner_id']:
            domain += [('partner_id', '=', form['partner_id'][0])]
        if form['date_start']:
            domain += [('date', '>=', form['date_start'])]
        if form['date_stop']:
            domain += [('date', '<=', form['date_stop'])]
        res = self.detail_payment(domain, form)

        return res

    def detail_payment(self, domain, form):
        res = []
        cr, uid = self.cr, self.uid
        currency_id = False
        if form['currency_id']:
            currency_id = form['currency_id'][0]

        payment_obj = self.pool.get('account.voucher')
        payment_oids = payment_obj.search(cr, uid, domain)
        for obj in payment_obj.browse(cr, uid, payment_oids):
            amount = obj.amount
            if obj.total_to_apply > amount:
                amount = obj.total_to_apply
            if currency_id != obj.currency_id.id:
                context = {'date': obj.date}
                amount = self.pool.get('res.currency').compute(
                    cr, uid, obj.currency_id.id, currency_id,
                    amount, context)
            number = obj.number
            if not obj.move_ids:
                number = '[WRONG][No Enty]%s'%number
            else:
                reconcile = [l for l in obj.move_ids if l.account_id.reconcile]
                if not reconcile:
                    number = '[WRONG][No Recivable]%s'%number
            data ={
                'number': number,
                'date': obj.date,
                'currency': obj.currency_id.name,
                'amount': amount,
            }
            res += [data]
        return res

    def get_bill_partner(self, form):
        if not self.partner:
            self.partner = self.pool.get('res.partner').browse(self.cr, self.uid, form['partner_id'][0])
        invoice = self.partner
        for child in self.partner.child_ids:
            if child.type == 'invoice':
                invoice = child
        return invoice


    def get_data(self, form):
        domain = [('state', 'in', ('open', 'paid'))]
        if form['partner_id']:
            domain += [('partner_id', '=', form['partner_id'][0])]
        if form['date_start']:
            domain += [('date_invoice', '>=', form['date_start'])]
        if form['date_stop']:
            domain += [('date_invoice', '<=', form['date_stop'])]
        return self.get_invoice(domain, form)

    def get_invoice(self, domain, form):
        res = []
        invoice_obj = self.pool.get('account.invoice')
        cr, uid = self.cr, self.uid
        currency_id = False
        if form['currency_id']:
            currency_id = form['currency_id'][0]
        invoice_ids = invoice_obj.search(cr, uid, domain)
        for inv in invoice_obj.browse(cr, uid, invoice_ids):
            amount = inv.amount_total
            if currency_id != inv.currency_id.id:
                context = {'date': inv.date_invoice}
                amount = self.pool.get('res.currency').compute(
                    cr, uid, inv.currency_id.id, currency_id,
                    amount, context)
            data ={
                'number': inv.number,
                'date_due': inv.date_due,
                'date': inv.date_invoice,
                'currency': inv.currency_id.name,
                'amount': inv.type == 'out_refund' and -amount or amount,
            }
            res += [data]
        return res

    def display_address(self, partner):
        address = partner.street and partner.street + ' / ' or ''
        address += partner.street2 and partner.street2 + ' / ' or ''
        address += partner.city and partner.city.name + ' / ' or ''
        address += partner.state_id and partner.state_id.name + ' / ' or ''
        address += partner.zip and partner.zip.name + ' / ' or ''
        address += partner.country_id and partner.country_id.name + ' / ' or ''
        if address:
            address = address[:-3]
        return address


    def get_partner(self, form):
        if not self.partner:
            self.partner = self.pool.get('res.partner').browse(self.cr, self.uid, form['partner_id'][0])
        return self.partner

    def get_address(self, partner):
        address = partner.city and partner.city.name + ', ' or ''
        address += partner.state_id and partner.state_id.name + ', ' or ''
        address += partner.zip and partner.zip.name or ''
        return address


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

