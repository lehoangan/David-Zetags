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
from openerp.addons.account.report.account_partner_balance import partner_balance
from openerp.report import report_sxw
from openerp.tools.translate import _

class partner_balance_zateg(partner_balance):

    def __init__(self, cr, uid, name, context=None):
        super(partner_balance_zateg, self).__init__(cr, uid, name, context=context)
        self.account_ids = []
        self.localcontext.update( {
            'time': time,
            'partners': self._get_partner_list,
            'sum_currency': self._sum_currency,
            'lines': self.lines,
            'sum_debit': self._sum_debit,
            'sum_credit': self._sum_credit,
            'payment_partners': self._get_payment_partner_list,
            'sum_payment_currency': self._sum_payment_currency,
            'payment_lines': self.payment_lines,
            'sum_payment_debit': self._sum_payment_debit,
            'sum_payment_credit': self._sum_payment_credit,
        })

    def set_context(self, objects, data, ids, report_type=None):
        if data['form']['currency_id']:
            ctx = data['form'].get('used_context', {})
            if ctx:
                data['form']['used_context'].update({'currency_id': data['form']['currency_id'][0]})
            else:
                data['form'].update({'used_context': {'currency_id': data['form']['currency_id'][0]}})

        if data['form']['partner_id']:
            ctx = data['form'].get('used_context', {})
            if ctx:
                data['form']['used_context'].update({'partner_id': data['form']['partner_id'][0]})
            else:
                data['form'].update({'used_context': {'partner_id': data['form']['partner_id'][0]}})
        self.display_partner = data['form'].get('display_partner', 'non-zero_balance')
        obj_move = self.pool.get('account.move.line')
        self.query = obj_move._query_get(self.cr, self.uid, obj='l', context=data['form'].get('used_context', {}))
        self.result_selection = data['form'].get('result_selection')
        self.target_move = data['form'].get('target_move', 'all')

        if (self.result_selection == 'customer'):
            self.ACCOUNT_TYPE = ('receivable',)
            self.PAYMENT_TYPE = ('receipt',)
        elif (self.result_selection == 'supplier'):
            self.ACCOUNT_TYPE = ('payable',)
            self.PAYMENT_TYPE = ('payment',)
        else:
            self.ACCOUNT_TYPE = ('payable', 'receivable')
            self.PAYMENT_TYPE = ('payment','receipt')

        self.cr.execute("SELECT a.id " \
                        "FROM account_account a " \
                        "LEFT JOIN account_account_type t " \
                        "ON (a.type = t.code) " \
                        "WHERE a.type IN %s " \
                        "AND a.active", (self.ACCOUNT_TYPE,))
        self.account_ids = [a for (a,) in self.cr.fetchall()]
        self.cr.execute("SELECT a.id " \
                        "FROM account_account a " \
                        "LEFT JOIN account_account_type t " \
                        "ON (a.type = t.code) " \
                        "WHERE a.type = 'liquidity' " \
                        "AND a.active")
        self.payment_account_ids = [a for (a,) in self.cr.fetchall()]
        return super(partner_balance, self).set_context(objects, data, ids, report_type=report_type)

    def _get_partner_list(self):
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']

        self.cr.execute(
                "SELECT DISTINCT part.id, part.id, part.name, l.currency_id " \
                "FROM account_move_line AS l " \
                "JOIN account_move am ON (am.id = l.move_id)" \
                "JOIN account_invoice invoice ON (am.id = invoice.move_id)" \
                "LEFT JOIN res_partner AS part ON (l.partner_id=part.id) " \
                "WHERE l.account_id IN %s"  \
                    "AND am.state IN %s" \
                    "AND " + self.query + " GROUP BY part.id, part.name, l.currency_id",
                    (tuple(self.account_ids), tuple(move_state)))
        res = self.cr.dictfetchall()
        return res

    def _sum_debit(self, partner):
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']
        partner_id = partner.get('id', False)
        currency_id = partner.get('currency_id', False)
        partner = ' AND l.partner_id is null '
        if partner_id:
            partner = ' AND l.partner_id =%s '%partner_id
        currency = ' AND l.currency_id is null '
        if currency_id:
            currency = ' AND l.currency_id =%s '%currency_id

        self.cr.execute(
                "SELECT sum(debit) " \
                "FROM account_move_line AS l " \
                "JOIN account_move am ON (am.id = l.move_id)" \
                "JOIN account_invoice invoice ON (am.id = invoice.move_id)" \
                "WHERE l.account_id IN %s"  \
                    "AND am.state IN %s" \
                    "AND " + self.query + partner + currency + "",
                    (tuple(self.account_ids), tuple(move_state)))
        temp_res = float(self.cr.fetchone()[0] or 0.0)
        return temp_res

    def _sum_credit(self, partner):
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']

        partner_id = partner.get('id', False)
        currency_id = partner.get('currency_id', False)
        partner = ' AND l.partner_id is null '
        if partner_id:
            partner = ' AND l.partner_id =%s ' % partner_id
        currency = ' AND l.currency_id is null '
        if currency_id:
            currency = ' AND l.currency_id =%s ' % currency_id

        self.cr.execute(
                "SELECT sum(credit) " \
                "FROM account_move_line AS l " \
                "JOIN account_move am ON (am.id = l.move_id)" \
                "JOIN account_invoice invoice ON (am.id = invoice.move_id)" \
                "WHERE l.account_id IN %s" \
                    "AND am.state IN %s" \
                    "AND " + self.query + partner + currency + "",
                    (tuple(self.account_ids), tuple(move_state)))
        temp_res = float(self.cr.fetchone()[0] or 0.0)
        return temp_res

    def _sum_currency(self, partner):
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']

        partner_id = partner.get('id', False)
        currency_id = partner.get('currency_id', False)
        partner = ' AND l.partner_id is null '
        if partner_id:
            partner = ' AND l.partner_id =%s ' % partner_id
        currency = ' AND l.currency_id is null '
        if currency_id:
            currency = ' AND l.currency_id =%s ' % currency_id


        self.cr.execute(
                "SELECT sum(amount_currency) " \
                "FROM account_move_line AS l " \
                "JOIN account_move am ON (am.id = l.move_id)" \
                "JOIN account_invoice invoice ON (am.id = invoice.move_id)" \
                "WHERE l.account_id IN %s" \
                    "AND am.state IN %s" \
                    "AND " + self.query + partner + currency + "",
                    (tuple(self.account_ids), tuple(move_state)))
        amount_currency = float(self.cr.fetchone()[0] or 0.0)
        currency = False
        if currency_id:
            currency = self.pool.get('res.currency').browse(self.cr, self.uid, currency_id)
        return amount_currency, currency

    def lines(self, partner):
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']

        partner_id = partner.get('id', False)
        currency_id = partner.get('currency_id', False)
        partner = ' AND l.partner_id is null '
        if partner_id:
            partner = ' AND l.partner_id =%s ' % partner_id
        currency = ' AND l.currency_id is null '
        if currency_id:
            currency = ' AND l.currency_id =%s ' % currency_id

        self.cr.execute(
            "SELECT l.date, am.name, invoice.number, sum(debit) AS debit, sum(credit) AS credit, " \
            "l.currency_id, sum(amount_currency) AS amount_currency " \
            "FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) " \
            "JOIN account_account ac ON (l.account_id = ac.id)" \
            "JOIN account_move am ON (am.id = l.move_id)" \
            "JOIN account_invoice invoice ON (am.id = invoice.move_id)" \
            "WHERE ac.type IN %s " \
            "AND am.state IN %s " \
            "AND " + self.query + partner + currency + "" \
            "GROUP BY l.date, am.name, invoice.number,l.currency_id " \
            "ORDER BY l.date",
            (self.ACCOUNT_TYPE, tuple(move_state)))
        res = self.cr.dictfetchall()
        currency = False
        if currency_id:
            currency = self.pool.get('res.currency').browse(self.cr, self.uid, currency_id)
        for r in res:
            r.update({'currency': currency})
        return res






    def _get_payment_partner_list(self):
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']

        self.cr.execute(
                "SELECT DISTINCT part.id, part.id, part.name, l.currency_id " \
                "FROM account_move_line AS l " \
                "JOIN account_move am ON (am.id = l.move_id)"
                "JOIN account_voucher av ON (am.id = av.move_id)"\
                "LEFT JOIN res_partner AS part ON (av.partner_id=part.id) " \
                "WHERE av.type IN %s"  \
                    "AND am.state IN %s" \
                    "AND " + self.query + " GROUP BY part.id, part.name, l.currency_id",
                    (self.PAYMENT_TYPE, tuple(move_state)))
        res = self.cr.dictfetchall()
        return res

    def _sum_payment_debit(self, partner):
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']
        partner_id = partner.get('id', False)
        currency_id = partner.get('currency_id', False)
        partner = ' AND l.partner_id is null '
        if partner_id:
            partner = ' AND l.partner_id =%s '%partner_id
        currency = ' AND l.currency_id is null '
        if currency_id:
            currency = ' AND l.currency_id =%s '%currency_id

        self.cr.execute(
                "SELECT sum(debit) " \
                "FROM account_move_line AS l " \
                "JOIN account_move am ON (am.id = l.move_id)" \
                "JOIN account_voucher av ON (am.id = av.move_id)"\
                "WHERE l.account_id IN %s and av.type IN %s "  \
                    "AND am.state IN %s" \
                    "AND " + self.query + partner + currency + "",
                    (tuple(self.payment_account_ids), self.PAYMENT_TYPE, tuple(move_state)))
        temp_res = float(self.cr.fetchone()[0] or 0.0)
        return temp_res

    def _sum_payment_credit(self, partner):
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']

        partner_id = partner.get('id', False)
        currency_id = partner.get('currency_id', False)
        partner = ' AND l.partner_id is null '
        if partner_id:
            partner = ' AND l.partner_id =%s ' % partner_id
        currency = ' AND l.currency_id is null '
        if currency_id:
            currency = ' AND l.currency_id =%s ' % currency_id

        self.cr.execute(
                "SELECT sum(credit) " \
                "FROM account_move_line AS l " \
                "JOIN account_move am ON (am.id = l.move_id)" \
                "JOIN account_voucher av ON (am.id = av.move_id)"\
                "WHERE l.account_id IN %s and av.type IN %s " \
                    "AND am.state IN %s" \
                    "AND " + self.query + partner + currency + "",
                    (tuple(self.payment_account_ids), self.PAYMENT_TYPE, tuple(move_state)))
        temp_res = float(self.cr.fetchone()[0] or 0.0)
        return temp_res

    def _sum_payment_currency(self, partner):
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']

        partner_id = partner.get('id', False)
        currency_id = partner.get('currency_id', False)
        partner = ' AND l.partner_id is null '
        if partner_id:
            partner = ' AND l.partner_id =%s ' % partner_id
        currency = ' AND l.currency_id is null '
        if currency_id:
            currency = ' AND l.currency_id =%s ' % currency_id


        self.cr.execute(
                "SELECT sum(amount_currency) " \
                "FROM account_move_line AS l " \
                "JOIN account_move am ON (am.id = l.move_id)" \
                "JOIN account_voucher av ON (am.id = av.move_id)"\
                "WHERE l.account_id IN %s and av.type IN %s " \
                    "AND am.state IN %s" \
                    "AND " + self.query + partner + currency + "",
                    (tuple(self.payment_account_ids), self.PAYMENT_TYPE, tuple(move_state)))
        amount_currency = float(self.cr.fetchone()[0] or 0.0)
        currency = False
        if currency_id:
            currency = self.pool.get('res.currency').browse(self.cr, self.uid, currency_id)
        return amount_currency, currency

    def payment_lines(self, partner):
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']

        partner_id = partner.get('id', False)
        currency_id = partner.get('currency_id', False)
        partner = ' AND l.partner_id is null '
        if partner_id:
            partner = ' AND l.partner_id =%s ' % partner_id
        currency = ' AND l.currency_id is null '
        if currency_id:
            currency = ' AND l.currency_id =%s ' % currency_id

        self.cr.execute(
            "SELECT l.date, am.name, av.number as number, sum(debit) AS debit, sum(credit) AS credit, " \
            "l.currency_id, sum(amount_currency) AS amount_currency " \
            "FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) " \
            "JOIN account_account ac ON (l.account_id = ac.id)" \
            "JOIN account_move am ON (am.id = l.move_id)" \
            "JOIN account_voucher av ON (am.id = av.move_id)"\
            "WHERE ac.type IN %s and av.type IN %s " \
            "AND am.state IN %s " \
            "AND " + self.query + partner + currency + "" \
            "GROUP BY l.date, am.name, av.number,l.currency_id " \
            "ORDER BY l.date",
            (('liquidity',), self.PAYMENT_TYPE, tuple(move_state)))
        res = self.cr.dictfetchall()
        currency = False
        if currency_id:
            currency = self.pool.get('res.currency').browse(self.cr, self.uid, currency_id)
        for r in res:
            r.update({'currency': currency})
        return res

from openerp.netsvc import Service
del Service._services['report.account.partner.balance']

report_sxw.report_sxw('report.account.partner.balance', 'res.partner',
                      'z_account/report/account_partner_balance.rml',parser=partner_balance_zateg, header="internal")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
