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
from datetime import datetime
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare

class bank_reconcilation(osv.osv):
    _name = "bank.reconcilation"

    def _default_last_date(self, cr, uid, context=None):
        res = False
        old_ids = self.search(cr, uid, [('state', '=', 'reconciled')], order="id desc", limit=1)
        if old_ids:
            res = self.browse(cr, uid, old_ids[0]).date

        return res

    def _get_last_reconcile_date(self, cr, uid, ids, name, args, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id] = False
            old_ids = self.search(cr, uid, [('state', '=', 'reconciled'),
                                            ('id', '!=', obj.id)], order="id desc", limit=1)
            if old_ids:
                res[obj.id] = self.browse(cr, uid, old_ids[0]).date

        return res

    def _compute_opening_balance(self, cr, uid, ids, name, args, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id] = False
            old_ids = self.search(cr, uid, [('state', '=', 'reconciled'),
                                            ('id', '!=', obj.id)], order="id desc", limit=1)
            if old_ids:
                res[obj.id] = self.browse(cr, uid, old_ids[0]).calculated_balance

        return res

    def _compute_closing_balance(self, cr, uid, ids, name, args, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id] = obj.opening_balance + obj.statement_balance
        return res

    def _compute_calculated_balance(self, cr, uid, ids, name, args, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context):
            opening_balance = 0
            old_ids = self.search(cr, uid, [('state', '=', 'reconciled'),
                                            ('id', '!=', obj.id)], order="id desc", limit=1)
            if old_ids:
                opening_balance = self.browse(cr, uid, old_ids[0]).calculated_balance

            res[obj.id] = opening_balance
            for line in obj.line_id:
                if line.choose:
                    res[obj.id] += line.debit - line.credit
        return res

    _columns = {
        'name': fields.char('Description', 100, required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'account_id': fields.many2one('account.account', 'Account', domain="[('company_id','=',company_id),('z_reconcile', '=', True)]", readonly=True, states={'draft': [('readonly', False)]}),
        'date': fields.date('Reconcile Date', readonly=True, states={'draft': [('readonly', False)]}),
        'last_reconcile_date': fields.function(_get_last_reconcile_date, type='date', string='Last Reconciled',
            store={
                'bank.reconcilation': (lambda self, cr, uid, ids, c={}: ids, ['date'], 20),
            }),
        'opening_balance': fields.function(_compute_opening_balance, type='float', string='Opening Balance',
            store={
                'bank.reconcilation': (lambda self, cr, uid, ids, c={}: ids, ['statement_balance', 'line_id'], 20),
            }),
        'calculated_balance': fields.function(_compute_calculated_balance, type='float', string='Calculated Balance',
            store={
                'bank.reconcilation': (lambda self, cr, uid, ids, c={}: ids, ['statement_balance', 'line_id'], 20),
            }),
        'statement_balance': fields.float('Statement Balance', readonly=True, states={'draft': [('readonly', False)]}),
        'closing_balance': fields.function(_compute_closing_balance, type='float', string='Closing Balance',
            store={
                'bank.reconcilation': (lambda self, cr, uid, ids, c={}: ids, ['statement_balance', 'line_id'], 20),
            }),
        'line_id': fields.one2many('bank.reconcilation.line', 'order_id', 'Detail', readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection([('draft','Draft'), ('reconciled', 'Reconciled')], 'State', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }
    _defaults={
        'state': 'draft',
        'last_reconcile_date': _default_last_date,
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.account', context=c),
    }

    def unlink(self, cr, uid, ids, context=None):
        objects = self.read(cr, uid, ids, ['state'])
        for t in objects:
            if t['state'] != 'draft':
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete reconciled bank !'))
        return super(bank_reconcilation, self).unlink(cr, uid, ids, context)

    def onchange_line_id(self, cr, uid, ids, line_id, opening_balance, context=None):
        if not line_id:
            return {'value': {}}

        result = {}
        total = opening_balance
        for line in line_id:
            if line[2] and line[2].get('choose', False):
                if line[1]:
                    obj = self.pool.get('bank.reconcilation.line').browse(cr, uid, line[1])
                    total += (obj.debit - obj.credit)
                else:
                    total += (line[2].get('debit', 0) - line[2].get('credit', 0))
            elif line[1]:
                obj = self.pool.get('bank.reconcilation.line').browse(cr, uid, line[1])
                if obj.choose:
                    total += (obj.debit - obj.credit)
        result.update({'calculated_balance': total})
        return {'value': result}

    def onchange_date_account(self, cr, uid, ids, account_id, date, context=None):
        if not account_id or not date:
            return {'value': {}}
        vals = {}
        #default last reconcile date + 'Opening Balance
        old_ids = self.search(cr, uid, [('state', '=', 'reconciled'),
                                        ('id', 'not in', ids)], order="id desc", limit=1)
        if old_ids:
            old_obj = self.browse(cr, uid, old_ids[0])
            vals.update({'last_reconcile_date': old_obj.date,
                         'opening_balance': old_obj.calculated_balance})

        if date:
            #get line detail
            condition = '(ml.z_reconciled is NULL or ml.z_reconciled = FALSE) AND'
            if account_id:
                condition += ' ml.account_id = %s'%account_id
                if date:
                    condition += '''AND ml.date <= '%s' '''%date
            elif date:
                condition += ''' ml.date <= '%s' '''%date
            sql = '''SELECT DISTINCT ml.id, ml.date, ml.partner_id, ml.account_id, ml.debit,
                          ml.credit, ml.currency_id, ml.tax_code_id, ml.state
                    FROM account_move_line ml
                    WHERE %s
                '''%(condition)

            cr.execute(sql)
            datas = cr.dictfetchall()
            res = []
            for data in datas:
                res.append({'move_line_id': data['id'],
                            'date': data['date'],
                            'partner_id': data['partner_id'] and data['partner_id'] or False,
                            'account_id': data['account_id'] and data['account_id'] or False,
                            'debit': data['debit'] or 0,
                            'credit': data['credit'] or 0,
                            'currency_id': data['currency_id'] and data['currency_id'] or False,
                            'tax_code_id': data['tax_code_id'] and data['tax_code_id'] or False,
                            'state': data['state'],
                            })
            vals.update({'line_id': res})
        return {'value': vals}

    def button_reconcile(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context):
            move_ids = []
            for line in obj.line_id:
                if line.choose:
                    move_ids.append(line.move_line_id.id)
            if obj.calculated_balance != obj.statement_balance:
                raise osv.except_osv(_('Error!'), _('Your balance does not reconcile. Calculated and Statement Balances must reconcile'))
            if not move_ids:
                raise osv.except_osv(_('Error!'), _('Please choose entry to reconciliation'))
            cr.execute('UPDATE account_move_line set z_reconciled= TRUE where id in %s '%str(tuple(move_ids + [-1,-1])))
        self.write(cr, uid, ids, {'state': 'reconciled'}, context)
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context):
            next_ids = self.search(cr, uid, [('date', '>', obj.date),('state', '=', 'reconciled'), ])
            if next_ids:
                raise osv.except_osv(_('Error!'), _('Please remove the next reconciliation first'))
            move_ids = []
            for line in obj.line_id:
                if line.choose:
                    move_ids.append(line.move_line_id.id)

            if not move_ids:
                raise osv.except_osv(_('Error!'), _('Please choose entry to reconciliation'))
            cr.execute('UPDATE account_move_line set z_reconciled= FALSE where id in %s '%str(tuple(move_ids + [-1,-1])))
        self.write(cr, uid, ids, {'state': 'draft'}, context)
        return True



bank_reconcilation()

class bank_reconcilation_line(osv.osv):
    _name = "bank.reconcilation.line"
    _columns = {
        'order_id': fields.many2one('bank.reconcilation', 'Parent', ondelete='cascade'),
        'move_line_id': fields.many2one('account.move.line', 'Move Items', domain="[('account_id', '=', parent.account_id)]"),
        'date': fields.related('move_line_id', 'date',string='Date', type='date',
                               store={
                                        'bank.reconcilation.line': (lambda self, cr, uid, ids, c={}: ids, ['move_line_id'], 10),
                                    }),
        'partner_id': fields.related('move_line_id', 'partner_id',string='Partner', type='many2one', relation="res.partner"),
        'account_id': fields.related('move_line_id', 'account_id',string='Account', type='many2one', relation="account.account"),
        'debit': fields.related('move_line_id', 'debit',string='Debit', type='float'),
        'credit': fields.related('move_line_id', 'credit',string='Credit', type='float'),
        'currency_id': fields.related('move_line_id', 'currency_id',string='Curremcy', type='many2one', relation="res.currency"),
        'tax_code_id': fields.related('move_line_id', 'tax_code_id',string='Tax Account', type='many2one', relation="account.tax.code"),
        'state': fields.related('move_line_id', 'state',string='Status', type='selection', selection=[('draft','Unbalanced'), ('valid','Balanced')]),
        'choose': fields.boolean('Select'),
    }
    _order = "date desc"


bank_reconcilation()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
