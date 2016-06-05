# -*- coding: utf-8 -*-################################################################################    OpenERP, Open Source Management Solution#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).##    This program is free software: you can redistribute it and/or modify#    it under the terms of the GNU Affero General Public License as#    published by the Free Software Foundation, either version 3 of the#    License, or (at your option) any later version.##    This program is distributed in the hope that it will be useful,#    but WITHOUT ANY WARRANTY; without even the implied warranty of#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the#    GNU Affero General Public License for more details.##    You should have received a copy of the GNU Affero General Public License#    along with this program.  If not, see <http://www.gnu.org/licenses/>.###############################################################################from openerp.osv import fields, osvfrom openerp import toolsfrom openerp import SUPERUSER_IDclass ir_rule(osv.osv):    _inherit = 'ir.rule'    @tools.ormcache()    def _compute_domain(self, cr, uid, model_name, mode="read"):        sql = '''        SELECT non_switch_company FROM res_users WHERE id = %s        '''%str(uid)        cr.execute(sql)        non_switch_company = cr.dictfetchone()['non_switch_company']        if non_switch_company:            return None        return super(ir_rule, self)._compute_domain(cr, uid, model_name, mode)ir_rule()