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
        
        self.localcontext.update({
            'get_account': self._get_account,
            'get_opening_amount': self._get_opening_amount,
            'get_details': self._get_details
        })
    
    def _get_account(self, form):
        account = self.pool.get('account.account').browse(self.cr, self.uid, form['account_id'][0])
        return '[%s] %s'%(account.code, account.name)

    def _get_opening_amount(self, form):
        cr = self.cr
        uid = self.uid
        date_start = form['date_start']
        date_stop = form['date_stop']
        account_id = form['account_id'][0]

        sql = '''
                SELECT sum(debit-credit) as amount
                FROM account_move_line
                WHERE date < '%s' AND account_id = %s
        '''%(date_start, account_id)

        cr.execute(sql)
        return cr.dictfetchone()['amount']

    def _get_details(self, form):
        cr = self.cr
        uid = self.uid
        date_start = form['date_start']
        date_stop = form['date_stop']
        account_id = form['account_id'][0]

        opening_amount = self._get_opening_amount(form)
        total_debit, total_credit = 0,0

        sql = '''
                SELECT move.name as no, line.name as memo, line.date,
                      line.debit, line.credit
                FROM account_move_line line
                JOIN account_move move on (line.move_id = move.id)
                WHERE line.date >= '%s' AND line.date <= '%s' AND line.account_id = %s
        '''%(date_start, date_stop, account_id)

        cr.execute(sql)
        datas = cr.dictfetchall()
        result = []
        for data in datas:
            total_credit += data['credit']
            total_debit += data['debit']
            opening_amount += (data['debit'] - data['credit'])
            result.append({
                'id': data['no'],
                'src': data['debit'] and 'CD' or 'CR',
                'date': data['date'],
                'memo': data['memo'],
                'debit': data['debit'] and data['debit'] or '',
                'credit': data['credit'] and data['credit'] or '',
                'ending': opening_amount,
            })
        result.append({
            'id': '',
            'src': '',
            'memo': 'TOTAL:',
            'date': '',
            'debit': total_debit,
            'credit': total_credit,
            'ending': opening_amount,
        })
        return result
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

