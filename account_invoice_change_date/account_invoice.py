
# -*- encoding: utf-8 -*-
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

from osv import osv, fields
from tools.translate import _

class account_change_date(osv.osv_memory):
    _name = 'account.change.date'
    _description = 'Change Date Period'

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(account_change_date, self).default_get(cr,
                                                uid, fields, context=context)
        if context.get('active_id'):
            obj_inv = self.pool.get('account.invoice')
            invoice = obj_inv.browse(cr, uid, context['active_id'], context=context)
            line_ids = []
            res.update({'current_date': invoice.date_invoice})
            for l in invoice.move_id.line_id:
                if not l.date_maturity: continue
                line_ids.append({'current_date': l.date_maturity})
            res.update({'due_date_ids': line_ids})
        return res

    _columns = {
        'current_date': fields.date('Current Date'),
        'date': fields.date('New Date', required=True),
        'period_id' : fields.many2one('account.period', 'Period'),
        'due_date_ids': fields.one2many('account.change.date.due', 'parent_id', 'Due Date'),
    }

    def onchange_date(self, cr, uid, ids, date, context=None):
        """ On change of Date Compute Pierod.
        
        @param date: Invoice Date
        @return: period ID
        """
        obj_period = self.pool.get('account.period')
        
        res = {}
        if date:            
            period_ids = obj_period.search(cr,uid,[('date_start','<=',date), ('date_stop','>=',date), ('state','=','draft'), ('special', '!=', True) ], context)
            if period_ids:
                res['value'] = {'period_id' : period_ids[0]}
            else:
                raise osv.except_osv(_('Error'), _('You can not set a date in a closed period !'))
  
        return res

    def change_date(self, cr, uid, ids, context=None):
        obj_inv = self.pool.get('account.invoice')

        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        new_date = data.date
        new_period_id = data.period_id.id
        
        invoice = obj_inv.browse(cr, uid, context['active_id'], context=context)
        if invoice.period_id.id == new_period_id and invoice.date_invoice == new_date: 
            return {}

        invoice.move_id.button_cancel()

        invoice.write({'date_invoice': new_date, 'period_id': new_period_id}, context=context)
        invoice.move_id.write({'date': new_date, 'period_id': new_period_id}, context=context)

        for line in data.due_date_ids:
            if invoice.date_due == line.current_date:
                invoice.write({'date_due': line.date}, context=context)
            for l in invoice.move_id.line_id:
                if not l.date_maturity:
                    cr.execute('''UPDATE account_move_line SET period_id= %s, date= '%s' WHERE id = %s
                                                  ''' % (new_period_id, new_date, l.id))
                if l.date_maturity == line.current_date:
                    cr.execute('''UPDATE account_move_line SET date_maturity= '%s', period_id= %s, date= '%s' WHERE id = %s
                              '''%(str(line.date), str(new_period_id), str(new_date), str(l.id)))
        invoice.move_id.post()
        return {'type': 'ir.actions.act_window_close'}

account_change_date()

class account_change_date_due(osv.osv_memory):
    _name = 'account.change.date.due'
    _description = 'Change Due Date Period'
    _columns = {
        'parent_id': fields.many2one('account.change.date.due', 'Parent'),
        'current_date': fields.date('Current Due Date'),
        'date': fields.date('New Due Date', required=True),
        'period_id' : fields.many2one('account.period', 'Period'),
    }

    def onchange_date(self, cr, uid, ids, date, context=None):
        """ On change of Date Compute Pierod.

        @param date: Invoice Date
        @return: period ID
        """
        obj_period = self.pool.get('account.period')

        res = {}
        if date:
            period_ids = obj_period.search(cr, uid, [('date_start', '<=', date), ('date_stop', '>=', date),
                                                     ('state', '=', 'draft'), ('special', '!=', True)], context)
            if period_ids:
                res['value'] = {'period_id': period_ids[0]}
            else:
                raise osv.except_osv(_('Error'), _('You can not set a date in a closed period !'))

        return res

