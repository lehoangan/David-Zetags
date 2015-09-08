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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime
import openerp.addons.decimal_precision as dp

class account_account(osv.osv):
    _inherit = "account.account"
    _columns = {
    }
    
    # def search(self, cr, uid, args, offset=0, limit=None, order=None,
    #         context=None, count=False):
    #     if context is None:
    #         context = {}
    #     if context.get('filter_by_pricelist_currency',False):
    #         pricelist = self.pool.get('product.pricelist').browse(cr, uid, context['filter_by_pricelist_currency'])
    #         if pricelist.currency_id != self.pool.get('res.users').browse(cr, uid, uid, context).company_id.currency_id:
    #             args.append(('currency_id','=', pricelist.currency_id.id))
    #         else:
    #             args.append(('currency_id','=', False))
    #     return super(account_account, self).search(cr, uid, args, offset, limit,
    #             order, context=context, count=count)
        
account_account()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
