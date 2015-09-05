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
    _columns = {
        'name': fields.char('Description', 100),
        'account_id': fields.many2one('account.account', 'Account', domain=[('z_reconcile', '=', True)]),
        'date': fields.date('Date'),
        'opening_balance': fields.float('Opening Balance'),
        'expected_balance': fields.float('Expected Balance'),
        'closing_balance': fields.float('Closing Balance'),
        'line_id': fields.one2many('bank.reconcilation.line', 'order_id', 'Detail'),
    }
    
    def onchange_date_account(self, cr, uid, ids, account_id, date, context=None):
        if not account_id and not date:
            return {'value': {}}
        vals = {}
        sql = ''
        return {'value': vals}
    
    def button_reconcile(self, cr, uid, ids, context=None):
        return True


bank_reconcilation()

class bank_reconcilation_line(osv.osv):
    _name = "bank.reconcilation.line"
    _columns = {
        'order_id': fields.many2one('bank.reconcilation', 'Parent'),
        'move_line_id': fields.many2one('account.move.line', 'Move Items', domain="[('account_id', '=', parent.account_id)]"),
        'date': fields.related('move_line_id', 'date',string='Date', type='date'),
        'partner_id': fields.related('move_line_id', 'partner_id',string='Partner', type='many2one', relation="res.partner"),
        'account_id': fields.related('move_line_id', 'account_id',string='Account', type='many2one', relation="account.account"),
        'debit': fields.related('move_line_id', 'debit',string='Debit', type='float'),
        'credit': fields.related('move_line_id', 'credit',string='Credit', type='float'),
        'currency_id': fields.related('move_line_id', 'currency_id',string='Curremcy', type='many2one', relation="res.currency"),
        'tax_code_id': fields.related('move_line_id', 'tax_code_id',string='Tax Account', type='many2one', relation="account.tax.code"),
        'state': fields.related('move_line_id', 'state',string='Status', type='selection', selection=[('draft','Unbalanced'), ('valid','Balanced')]),
        'choose': fields.boolean('Select'),
    }


bank_reconcilation()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
