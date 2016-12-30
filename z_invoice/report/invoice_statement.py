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
            'get_total': self._get_data_report_months,
            'get_bill_partner': self.get_bill_partner,
            'get_partner': self.get_partner,
            'get_address': self.get_address,
            'time': time,
        })

    def get_bill_partner(self, form):
        if not self.partner:
            self.partner = self.pool.get('res.partner').browse(self.cr, self.uid, form['partner_id'][0])
        invoice = self.partner
        for child in self.partner.child_ids:
            if child.type == 'invoice':
                invoice = child
        return invoice

    def _get_data_report_months(self,form):
        now_time = datetime.datetime.now()
        date_01  = now_time - timedelta(days=30)
        date_01= datetime.datetime.strftime(date_01, '%Y-%m-%d')
        date_02  = now_time - timedelta(days=60)
        date_02 = datetime.datetime.strftime(date_02, '%Y-%m-%d')
        date_03  = now_time - timedelta(days=90)
        date_03 = datetime.datetime.strftime(date_03, '%Y-%m-%d')
        date_04  = now_time - timedelta(days=120)
        date_04 = datetime.datetime.strftime(date_04, '%Y-%m-%d')

        self.cr.execute('''
        SELECT rc."name" AS currency_name,
            SUM(CASE WHEN date_trunc('day',ai.date_invoice)>='%s' THEN ai.residual ELSE 0 END ) AS amount_1,
            SUM(CASE WHEN date_trunc('day',ai.date_invoice)<'%s' AND date_trunc('day',ai.date_invoice)>='%s' THEN ai.residual ELSE 0 END ) AS amount_2,
            SUM(CASE WHEN date_trunc('day',ai.date_invoice)<'%s' AND date_trunc('day',ai.date_invoice)>='%s' THEN ai.residual ELSE 0 END ) AS amount_3,
            SUM(CASE WHEN date_trunc('day',ai.date_invoice)<'%s' THEN ai.residual ELSE 0 END ) AS amount_4
            FROM account_invoice ai
            INNER JOIN account_move am ON ai.move_id = am."id"
            LEFT JOIN res_currency rc ON ai.currency_id = rc."id"
            WHERE ai.partner_id = %s AND ai.state = 'open'
            GROUP BY rc."name"
        '''%(date_01,date_01, date_02,date_02,date_03,date_03,form['partner_id'][0]))
        res = self.cr.dictfetchall()
        return res

    def get_data(self, form):
        res = []
        invoice_obj = self.pool.get('account.invoice')
        cr, uid = self.cr, self.uid
        domain = [('state', '=', 'open')]
        if form['partner_id']:
            domain += [('partner_id', '=', form['partner_id'][0])]

        invoice_ids = invoice_obj.search(cr, uid, domain)
        for inv in invoice_obj.browse(cr, uid, invoice_ids):
            data ={
                'number': inv.number,
                'date_due': inv.date_due,
                'date': inv.date_invoice,
                'currency': inv.currency_id.name,
                'amount': inv.residual,
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

