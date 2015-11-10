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
import netsvc

class hr_payslip(osv.osv):
    _inherit = "hr.payslip"
    _columns = {
        'paid_date': fields.date('Paid Date'),
    }

    def action_revert_done(self, cr, uid, ids, context=None):
        if not len(ids):
            return False
        for slip in self.browse(cr, uid, ids, context):
            self.write(cr, uid, [slip.id], {'state': 'cancel'})
            if slip.move_id:
                slip.move_id.button_cancel()
                slip.move_id.unlink()
            wf_service = netsvc.LocalService("workflow")
            # Deleting the existing instance of workflow
            wf_service.trg_delete(uid, 'hr.payslip', slip.id, cr)
            wf_service.trg_create(uid, 'hr.payslip', slip.id, cr)
            wf_service.trg_validate(uid, 'hr.payslip', slip.id, 'cancel_sheet', cr)
        return True

    def hr_verify_sheet(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context):
            if not obj.line_ids:
                self.compute_sheet(cr, uid, [obj.id], context)
        return self.write(cr, uid, ids, {'state': 'verify'}, context=context)

    def process_sheet(self, cr, uid, ids, context=None):
        res = super(hr_payslip, self).process_sheet(cr, uid, ids, context=context)
        period_pool = self.pool.get('account.period')
        for payslip in self.browse(cr, uid, ids, context):
            if payslip.move_id and payslip.paid_date:
                period_ids = period_pool.find(cr, uid, payslip.paid_date, context)
                payslip.move_id.button_cancel()
                for move in payslip.move_id.line_id:
                    move.write({'date': payslip.paid_date,
                                'period_id': period_ids[0],
                                })
                payslip.move_id.write({'date': payslip.paid_date,
                                        'period_id': period_ids[0],})
                payslip.move_id.button_validate()

        return res


hr_payslip()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
