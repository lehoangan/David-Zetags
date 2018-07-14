# -*- coding: utf-8 -*-################################################################################    OpenERP, Open Source Management Solution#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).##    This program is free software: you can redistribute it and/or modify#    it under the terms of the GNU Affero General Public License as#    published by the Free Software Foundation, either version 3 of the#    License, or (at your option) any later version.##    This program is distributed in the hope that it will be useful,#    but WITHOUT ANY WARRANTY; without even the implied warranty of#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the#    GNU Affero General Public License for more details.##    You should have received a copy of the GNU Affero General Public License#    along with this program.  If not, see <http://www.gnu.org/licenses/>.###############################################################################import timefrom openerp.osv import fields, osvfrom openerp.tools.translate import _from datetime import datetimeimport openerp.addons.decimal_precision as dpclass account_move(osv.osv):    _inherit = "account.move"    _columns = {        'period_id': fields.many2one('account.period', 'Period', required=True, states={'posted': [('readonly', True)]}),                                     # domain="['|',('company_id', '=', company_id), ('company_id', '=', False)]"),        'journal_id': fields.many2one('account.journal', 'Journal', required=True,                                      states={'posted': [('readonly', True)]}),                                      # domain="['|',('company_id', '=', company_id), ('company_id', '=', False)]"),        'revalue': fields.boolean('Revalue Currency'),    }account_move()class account_move_line(osv.osv):    _inherit = "account.move.line"    _columns = {    }    def _query_get(self, cr, uid, obj='l', context=None):        clause = super(account_move_line, self)._query_get(cr, uid, obj, context)        if context.get('report_detail') == 'invoice':            clause += " AND " + obj + ".move_id in (SELECT move_id FROM account_invoice)"        elif context.get('report_detail') == 'payment':            clause += " AND " + obj + ".move_id in (SELECT move_id FROM account_voucher)"        if context.get('unpaid_invoice'):            clause += " AND " + obj + ".reconcile_id is null"        if context.get('hide_zero'):            clause += " AND ROUND(" + obj + ".debit + " + obj + ".credit, 2) > 0 "        if context.get('is_currency'):            clause += " AND " + obj + ".currency_id is not null "        if context.get('ex_account_ids'):            clause += " AND " + obj + ".account_id not in %s " % str(tuple(context['ex_account_ids'] + [-1, -1]))        if context.get('partner_id'):            clause += " AND " + obj + ".partner_id = %s" % context['partner_id']        if context.get('currency_id'):            company_currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id            if context['currency_id'] != company_currency_id:                clause += " AND " + obj + ".currency_id = %s" % context['currency_id']            else:                clause += " AND (" + obj + ".currency_id is null OR " + obj + ".currency_id = %s )" % context[                    'currency_id']        if context.get('not_opening_period'):            opening_periods = self.pool.get('account.period').search(cr, uid, [('special', '=', True)])            opening_periods += [-1,-1]            clause += " AND " + obj + ".period_id not in %s "%str(tuple(opening_periods))            opening_journals = self.pool.get('account.journal').search(cr, uid, [('type', '=', 'situation')])            opening_journals += [-1, -1]            clause += " AND " + obj + ".journal_id not in %s " % str(tuple(opening_journals))        # print clause        return clauseaccount_move_line()