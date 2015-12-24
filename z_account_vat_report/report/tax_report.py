# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2014 credativ Ltd
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
from openerp.addons.account.report.common_report_header import common_report_header

class Parser(report_sxw.rml_parse, common_report_header):


    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.an_period_ids = []
        self.company_id = data['form']['company_id']
        self.type = data['form']['based_on']
        period_obj = self.pool.get('account.period')
        self.display_detail = data['form']['display_detail']
        res['periods'] = ''
        res['fiscalyear'] = data['form'].get('fiscalyear_id', False)
        if data['form'].get('period_from', False) and data['form'].get('period_to', False):
            self.an_period_ids = period_obj.build_ctx_periods(self.cr, self.uid, data['form']['period_from'], data['form']['period_to'])
            periods_l = period_obj.read(self.cr, self.uid, self.an_period_ids, ['name'])
            for period in periods_l:
                if res['periods'] == '':
                    res['periods'] = period['name']
                else:
                    res['periods'] += ", "+ period['name']
        else:
            self.cr.execute ("select id from account_period where fiscalyear_id = %s",(res['fiscalyear'],))
            periods = self.cr.fetchall()
            for p in periods:
                self.an_period_ids.append(p[0])
        return super(Parser, self).set_context(objects, data, new_ids, report_type=report_type)


    def __init__(self, cr, uid, name, context=None):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_tax': self.get_tax,
            'get_date_limit': self._get_date_limit,
            'get_lines': self.get_lines,
        })

    def _get_date_limit(self, year, period, bound='low', context=None):
        cr  = self.cr
        uid = self.uid
        pd_obj = self.pool.get('account.period')
        yr_obj = self.pool.get('account.fiscalyear')

        ret = ''
        field = (bound == 'high') and 'date_stop' or 'date_start'
        if period:
            ret = pd_obj.read(cr, uid, period, [field], context=context)[field]
        else:
            op = (bound == 'high') and 'MAX' or 'MIN'
            sql = 'SELECT ' + op + '(' + field + ') ' \
                + 'FROM account_period ' \
                + 'WHERE fiscalyear_id = %d' % year
            cr.execute(sql)
            res = cr.fetchall()
            if res and res[0]:
                ret = res[0][0]
        return ret

    def get_tax(self):
        period_list = self.an_period_ids
        cr = self.cr
        uid = self.uid

        if not period_list:
            self.cr.execute ("select id from account_fiscalyear")
            fy = self.cr.fetchall()
            self.cr.execute ("select id from account_period where fiscalyear_id = %s",(fy[0][0],))
            periods = self.cr.fetchall()
            for p in periods:
                period_list.append(p[0])
        invoice_obj = self.pool.get('account.invoice')
        result = {}
        for type in [('out_invoice', 'out_refund'),('in_invoice', 'in_refund')]:
            state = ('state', 'not in', ['draft', 'cancel', 'proforma', 'proforma2'])
            if self.type == 'payments':
                state = ('state', '=', 'paid')
            invoice_ids = invoice_obj.search(cr, uid, [('type', 'in', type),
                                                       ('period_id', 'in', period_list),
                                                       ('company_id', '=', self.company_id),
                                                       state],
                                                        order='date_invoice desc')

            for invoice in invoice_obj.browse(cr, uid, invoice_ids):
                rate =1
                if invoice.currency_id != invoice.company_id.currency_id:
                    for move in invoice.move_id.line_id:
                        if move.amount_currency:
                            rate = (move.debit + move.credit) / abs(move.amount_currency)
                            break

                for tax in invoice.tax_line:
                    amount = (tax.base + invoice.shipping_charge) * rate
                    mtax = tax.amount * rate
                    if tax.name not in result.keys():
                        result.update({tax.name: {
                                                    'sale': type == ('out_invoice', 'out_refund') and amount or 0,
                                                    'tax_sale': type == ('out_invoice', 'out_refund') and mtax or 0,
                                                    'purchase': type != ('out_invoice', 'out_refund') and amount or 0,
                                                    'tax_purchase': type != ('out_invoice', 'out_refund') and mtax or 0,
                                                    'currency': invoice.company_id.currency_id.name,
                                                }})
                    else:
                        if type == ('out_invoice', 'out_refund'):
                            result[tax.name]['sale'] += amount
                            result[tax.name]['tax_sale'] += mtax
                        else:
                            result[tax.name]['purchase'] += amount
                            result[tax.name]['tax_purchase'] += mtax

        return result


    def _get_basedon(self, form):
        based_on = form['form']['based_on']
        if based_on == 'invoices':
            return _('Invoices')
        elif based_on == 'payments':
            return _('Payments')


    def get_lines(self, tax_name):
        period_list = self.an_period_ids
        cr = self.cr
        uid = self.uid

        if not period_list:
            self.cr.execute ("select id from account_fiscalyear")
            fy = self.cr.fetchall()
            self.cr.execute ("select id from account_period where fiscalyear_id = %s",(fy[0][0],))
            periods = self.cr.fetchall()
            for p in periods:
                period_list.append(p[0])
        invoice_obj = self.pool.get('account.invoice')
        result = []
        for type in [('out_invoice', 'out_refund'),('in_invoice', 'in_refund')]:
            state = ('state', 'not in', ['draft', 'cancel', 'proforma', 'proforma2'])
            if self.type == 'payments':
                state = ('state', '=', 'paid')
            invoice_ids = invoice_obj.search(cr, uid, [('type', 'in', type),
                                                       ('period_id', 'in', period_list),
                                                       ('company_id', '=', self.company_id),
                                                       state],
                                                        order='date_invoice desc')

            for invoice in invoice_obj.browse(cr, uid, invoice_ids):
                details = []
                for line in invoice.invoice_line:
                    if line.account_id.name not in details:
                        details += [line.account_id.name]
                for tax in invoice.tax_line:
                    if tax.name == tax_name:
                        result += [{
                            'date': invoice.date_invoice,
                            'partner': invoice.partner_id.name,
                            'ref': invoice.number,
                            'detail': ','.join(details),
                            'tax': tax_name or '',
                            'sale': type == ('out_invoice', 'out_refund') and tax.base + invoice.shipping_charge or '',
                            'tax_sale': type == ('out_invoice', 'out_refund') and tax.amount or '',
                            'purchase': type != ('out_invoice', 'out_refund') and tax.base + invoice.shipping_charge or '',
                            'tax_purchase': type != ('out_invoice', 'out_refund') and tax.amount or '',
                            'currency': invoice.currency_id.name,
                        }]
        return result


