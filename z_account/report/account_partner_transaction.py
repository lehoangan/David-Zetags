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
from z_account.report.account_partner_ledger import partner_ledger_zateg
from openerp.report import report_sxw

class partner_transation_zateg(partner_ledger_zateg):

    def __init__(self, cr, uid, name, context=None):
        super(partner_transation_zateg, self).__init__(cr, uid, name, context=context)
        self.init_bal_sum = 0.0
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'sum_debit_partner': self._sum_debit_partner,
            'sum_credit_partner': self._sum_credit_partner,
            'get_currency': self._get_currency,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period,
            'get_account': self._get_account,
            'get_filter': self._get_filter,
            'get_start_date': self._get_start_date,
            'get_end_date': self._get_end_date,
            'get_fiscalyear': self._get_fiscalyear,
            'get_journal': self._get_journal,
            'get_partners':self._get_partners,
            'get_intial_balance':self._get_intial_balance,
            'display_initial_balance':self._display_initial_balance,
            'display_currency':self._display_currency,
            'get_target_move': self._get_target_move,
        })

    def set_context(self, objects, data, ids, report_type=None):
        ctx = data['form'].get('used_context', {})
        if ctx:
            data['form']['used_context'].update({'is_currency': True})
        else:
            data['form'].update({'used_context': {'is_currency': True}})

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

        if data['form']['hide_zero']:
            ctx = data['form'].get('used_context', {})
            if ctx:
                data['form']['used_context'].update({'hide_zero': data['form']['hide_zero']})
            else:
                data['form'].update({'used_context': {'hide_zero': data['form']['hide_zero']}})
        return super(partner_transation_zateg, self).set_context(objects, data, ids, report_type=report_type)

    def lines(self, partner):
        move_state = ['draft', 'posted']
        if self.target_move == 'posted':
            move_state = ['posted']

        full_account = []
        if self.reconcil:
            RECONCILE_TAG = " "
        else:
            RECONCILE_TAG = "AND l.reconcile_id IS NULL"
        self.cr.execute(
            """ SELECT l.id, l.date, j.code, acc.code as a_code, acc.name as a_name, l.ref, m.name as move_name, l.name,
                CASE
                  WHEN l.debit > 0 THEN ABS(l.amount_currency)
                  ELSE 0
                END as debit,
                CASE
                  WHEN l.credit > 0 THEN ABS(l.amount_currency)
                  ELSE 0
                END as credit,
            l.amount_currency,l.currency_id, c.symbol AS currency_code """ \
            "FROM account_move_line l " \
            "LEFT JOIN account_journal j " \
            "ON (l.journal_id = j.id) " \
            "LEFT JOIN account_account acc " \
            "ON (l.account_id = acc.id) " \
            "LEFT JOIN res_currency c ON (l.currency_id=c.id)" \
            "LEFT JOIN account_move m ON (m.id=l.move_id)" \
            "WHERE l.currency_id is not null AND l.partner_id = %s " \
            "AND l.account_id IN %s AND " + self.query + " " \
                                                         "AND m.state IN %s " \
                                                         " " + RECONCILE_TAG + " " \
                                                                               "ORDER BY l.date",
            (partner.id, tuple(self.account_ids), tuple(move_state)))
        res = self.cr.dictfetchall()
        sum = 0.0
        if self.initial_balance:
            sum = self.init_bal_sum
        for r in res:
            sum += r['debit'] - r['credit']
            r['progress'] = sum
            full_account.append(r)
        return full_account

    def _get_intial_balance(self, partner):
        move_state = ['draft', 'posted']
        if self.target_move == 'posted':
            move_state = ['posted']
        if self.reconcil:
            RECONCILE_TAG = " "
        else:
            RECONCILE_TAG = "AND l.reconcile_id IS NULL"
        self.cr.execute(
            """SELECT COALESCE(SUM(l.debit),0.0),
                        COALESCE(SUM(l.credit),0.0),
                        COALESCE(sum(debit-credit), 0.0)
              FROM (SELECT CASE
                  WHEN l.debit > 0 THEN ABS(l.amount_currency)
                  ELSE 0
                END as debit,
                CASE
                  WHEN l.credit > 0 THEN ABS(l.amount_currency)
                  ELSE 0
                END as credit, l.currency_id """ \
            "FROM account_move_line AS l,  " \
            "account_move AS m "
            "WHERE l.partner_id = %s " \
            "AND m.id = l.move_id " \
            "AND m.state IN %s "
            "AND account_id IN %s" \
            " " + RECONCILE_TAG + " " \
            "AND " + self.init_query + "  ) as temp GROUP BY temp.currency_id",
            (partner.id, tuple(move_state), tuple(self.account_ids)))
        res = self.cr.fetchall()
        self.init_bal_sum = res[0][2]
        return res

    def _sum_debit_partner(self, partner):
        move_state = ['draft', 'posted']
        if self.target_move == 'posted':
            move_state = ['posted']

        result_tmp = 0.0
        result_init = 0.0
        if self.reconcil:
            RECONCILE_TAG = " "
        else:
            RECONCILE_TAG = "AND reconcile_id IS NULL"
        if self.initial_balance:
            self.cr.execute(
                """ SELECT sum(debit)
                  FROM (SELECT CASE
                          WHEN l.debit > 0 THEN ABS(l.amount_currency)
                          ELSE 0
                        END as debit """ \
                "FROM account_move_line AS l, " \
                "account_move AS m "
                "WHERE l.partner_id = %s" \
                "AND m.id = l.move_id " \
                "AND m.state IN %s "
                "AND account_id IN %s" \
                " " + RECONCILE_TAG + " " \
                                      "AND " + self.init_query + " )as tmp",
                (partner.id, tuple(move_state), tuple(self.account_ids)))
            contemp = self.cr.fetchone()
            if contemp != None:
                result_init = contemp[0] or 0.0
            else:
                result_init = result_tmp + 0.0

        self.cr.execute(
            """ SELECT sum(debit)
                  FROM (SELECT CASE
                          WHEN l.debit > 0 THEN ABS(l.amount_currency)
                          ELSE 0
                        END as debit """ \
            "FROM account_move_line AS l, " \
            "account_move AS m "
            "WHERE l.partner_id = %s " \
            "AND m.id = l.move_id " \
            "AND m.state IN %s "
            "AND account_id IN %s" \
            " " + RECONCILE_TAG + " " \
                                  "AND " + self.query + " )as tmp",
            (partner.id, tuple(move_state), tuple(self.account_ids),))

        contemp = self.cr.fetchone()
        if contemp != None:
            result_tmp = contemp[0] or 0.0
        else:
            result_tmp = result_tmp + 0.0

        return result_tmp + result_init

    def _sum_credit_partner(self, partner):
        move_state = ['draft', 'posted']
        if self.target_move == 'posted':
            move_state = ['posted']

        result_tmp = 0.0
        result_init = 0.0
        if self.reconcil:
            RECONCILE_TAG = " "
        else:
            RECONCILE_TAG = "AND reconcile_id IS NULL"
        if self.initial_balance:
            self.cr.execute(
                """ SELECT sum(credit)
                  FROM (SELECT CASE
                          WHEN l.credit > 0 THEN ABS(l.amount_currency)
                          ELSE 0
                        END as credit """ \
                "FROM account_move_line AS l, " \
                "account_move AS m  "
                "WHERE l.partner_id = %s" \
                "AND m.id = l.move_id " \
                "AND m.state IN %s "
                "AND account_id IN %s" \
                " " + RECONCILE_TAG + " " \
                                      "AND " + self.init_query + " )as tmp",
                (partner.id, tuple(move_state), tuple(self.account_ids)))
            contemp = self.cr.fetchone()
            if contemp != None:
                result_init = contemp[0] or 0.0
            else:
                result_init = result_tmp + 0.0

        self.cr.execute(
            """ SELECT sum(credit)
                  FROM (SELECT CASE
                          WHEN l.credit > 0 THEN ABS(l.amount_currency)
                          ELSE 0
                        END as credit """ \
            "FROM account_move_line AS l, " \
            "account_move AS m "
            "WHERE l.partner_id=%s " \
            "AND m.id = l.move_id " \
            "AND m.state IN %s "
            "AND account_id IN %s" \
            " " + RECONCILE_TAG + " " \
                                  "AND " + self.query + " )as tmp",
            (partner.id, tuple(move_state), tuple(self.account_ids),))

        contemp = self.cr.fetchone()
        if contemp != None:
            result_tmp = contemp[0] or 0.0
        else:
            result_tmp = result_tmp + 0.0
        return result_tmp + result_init

report_sxw.report_sxw('report.account.third_party_transaction', 'res.partner',
        'addons/z_account/report/account_partner_transaction.rml',parser=partner_transation_zateg,
        header='internal')

report_sxw.report_sxw('report.account.third_party_transaction_other', 'res.partner',
        'addons/z_account/report/account_partner_transaction_other.rml',parser=partner_transation_zateg,
        header='internal')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
