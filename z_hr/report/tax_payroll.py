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
            'get_total': self.get_total,
            'time': time,
        })



    def get_data(self, form):
        res = []
        payslip_obj = self.pool.get('hr.payslip')
        cr, uid = self.cr, self.uid
        domain = [('move_id', '!=', False),('state', '=', 'done'), ('company_id', '=', form['company_id'][0])]
        if form['date_start']:
            domain += [('date_from', '>=', form['date_start'])]
        if form['date_stop']:
            domain += [('date_to', '<=', form['date_stop'])]

        pl_ids = payslip_obj.search(cr, uid, domain)
        for pl in payslip_obj.browse(cr, uid, pl_ids):
            basic = tax = super = net = 0
            for line in pl.line_ids:
                if 'BASIC' in line.code.upper():
                    basic += line.amount
                if 'SUPER' in line.code.upper():
                    super += line.amount
                if 'TAX' in line.code.upper():
                    tax += line.amount
                if 'NET' in line.code.upper():
                    net += line.amount
            data ={
                'number': pl.number,
                'date': pl.move_id and pl.move_id.date or '',
                'emp': pl.employee_id and pl.employee_id.name or False,
                'from': pl.date_from,
                'to': pl.date_to,
                'basic': basic,
                'tax': tax,
                'super': super,
                'net': net,
            }
            res += [data]
        return res

    def get_total(self, form):
        res = []
        payslip_obj = self.pool.get('hr.payslip')
        cr, uid = self.cr, self.uid
        domain = [('state', '=', 'done'),('company_id', '=', form['company_id'][0])]
        if form['date_start']:
            domain += [('date_from', '>=', form['date_start'])]
        if form['date_stop']:
            domain += [('date_to', '<=', form['date_stop'])]

        pl_ids = payslip_obj.search(cr, uid, domain)
        basic = tax = super = net = 0
        for pl in payslip_obj.browse(cr, uid, pl_ids):
            for line in pl.line_ids:
                for line in pl.line_ids:
                    if 'BASIC' in line.code.upper():
                        basic += line.amount
                    if 'SUPER' in line.code.upper():
                        super += line.amount
                    if 'TAX' in line.code.upper():
                        tax += line.amount
                    if 'NET' in line.code.upper():
                        net += line.amount
            # for line in pl.move_id.line_id:
            #     if line.account_id.id in form['basic_ids']:
            #         basic += abs(line.debit - line.credit)
            #     if line.account_id.id in form['tax_ids']:
            #         tax += abs(line.debit - line.credit)
            #     if line.account_id.id in form['super_ids']:
            #         super += abs(line.debit - line.credit)
            #     if line.account_id.id in form['net_ids']:
            #         net += abs(line.debit - line.credit)
        data ={
            'basic': basic,
            'tax': tax,
            'super': super,
            'net': net,
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


    def get_address(self, partner):
        address = partner.city and partner.city.name + ', ' or ''
        address += partner.state_id and partner.state_id.name + ', ' or ''
        address += partner.zip and partner.zip.name or ''
        return address


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

