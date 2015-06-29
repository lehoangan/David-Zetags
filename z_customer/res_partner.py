# -*- coding: utf-8 -*-################################################################################    OpenERP, Open Source Management Solution#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).##    This program is free software: you can redistribute it and/or modify#    it under the terms of the GNU Affero General Public License as#    published by the Free Software Foundation, either version 3 of the#    License, or (at your option) any later version.##    This program is distributed in the hope that it will be useful,#    but WITHOUT ANY WARRANTY; without even the implied warranty of#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the#    GNU Affero General Public License for more details.##    You should have received a copy of the GNU Affero General Public License#    along with this program.  If not, see <http://www.gnu.org/licenses/>.###############################################################################import timefrom openerp.osv import fields, osvfrom openerp.tools.translate import _from datetime import datetimeimport openerp.addons.decimal_precision as dpclass res_partner_payment(osv.osv):    _name = "res.partner.payment"    _columns = {        'name': fields.char('Name', size=256, required=True),        'discount': fields.float('Discount (%)', digits=(5,2), required=True),        'days': fields.integer('Days', required=True),                'from_month_end': fields.boolean('From month end'),        'from_invoice_date': fields.boolean('From invoice date'),    }res_partner_payment()class Bank(osv.osv):    _inherit = 'res.bank'    _columns = {        'country_id': fields.many2one('res.country', 'Country'),        'state': fields.many2one("res.country.state", 'State', domain="[('country_id','=',country_id)]"),        'city': fields.many2one('res.city', 'City', domain="[('state_id','=',state)]"),        'zip': fields.many2one('postal.code', 'Zip', change_default=True, domain="[('city_id','=',city)]"),    }        def check_state_id(self, cr, uid, country_id, state_id):        cr.execute('SELECT id FROM res_country_state WHERE id=%s and country_id=%s'%(state_id, country_id))        res = cr.fetchone()        if res and res[0]:            return True        return False        def check_city_id(self, cr, uid, state_id, city):        cr.execute('SELECT id FROM res_city WHERE id=%s and state_id=%s'%(city, state_id))        res = cr.fetchone()        if res and res[0]:            return True        return False        def check_zip_id(self, cr, uid, city, zip):        cr.execute('SELECT id FROM postal_code WHERE id=%s and city_id=%s'%(zip, city))        res = cr.fetchone()        if res and res[0]:            return True        return False        def onchange_country_id(self, cr, uid, ids, country_id, state_id, city, zip, context=None):        value = {'state_id':False,'city':False,'zip':False}        if country_id:            country = self.pool.get('res.country').browse(cr, uid, country_id)            phone_code = country.phone_code            company_id = country.company_id.id            value.update({'phone':phone_code,'company_id':company_id})            if state_id and self.check_state_id(cr, uid, country_id, state_id):                value.update({'state_id':state_id})                if city and self.check_city_id(cr, uid, state_id, city):                    value.update({'city':city})                    if zip and self.check_zip_id(cr, uid, city, zip):                        value.update({'zip':zip})        return {'value':value}        def onchange_state(self, cr, uid, ids, state_id, city, zip, context=None):        value = {'city':False,'zip':False}        if state_id:            if city and self.check_city_id(cr, uid, state_id, city):                value.update({'city':city})                if zip and self.check_zip_id(cr, uid, city, zip):                    value.update({'zip':zip})        return {'value':value}        def onchange_city(self, cr, uid, ids, city, zip, context=None):        value = {'zip':False}        if city:            if zip and self.check_zip_id(cr, uid, city, zip):                value.update({'zip':zip})        return {'value':value}    Bank()class res_partner_bank(osv.osv):    _inherit = "res.partner.bank"    _columns = {        'country_id': fields.many2one('res.country', 'Country'),        'state_id': fields.many2one("res.country.state", 'State', domain="[('country_id','=',country_id)]"),        'city': fields.many2one('res.city', 'City', domain="[('state_id','=',state_id)]"),        'zip': fields.many2one('postal.code', 'Zip', change_default=True, domain="[('city_id','=',city)]"),    }    _defaults = {    }        def check_state_id(self, cr, uid, country_id, state_id):        cr.execute('SELECT id FROM res_country_state WHERE id=%s and country_id=%s'%(state_id, country_id))        res = cr.fetchone()        if res and res[0]:            return True        return False        def check_city_id(self, cr, uid, state_id, city):        cr.execute('SELECT id FROM res_city WHERE id=%s and state_id=%s'%(city, state_id))        res = cr.fetchone()        if res and res[0]:            return True        return False        def check_zip_id(self, cr, uid, city, zip):        cr.execute('SELECT id FROM postal_code WHERE id=%s and city_id=%s'%(zip, city))        res = cr.fetchone()        if res and res[0]:            return True        return False        def onchange_country_id(self, cr, uid, ids, country_id, state_id, city, zip, context=None):        value = {'state_id':False,'city':False,'zip':False}        if country_id:            country = self.pool.get('res.country').browse(cr, uid, country_id)            phone_code = country.phone_code            company_id = country.company_id.id            value.update({'phone':phone_code,'company_id':company_id})            if state_id and self.check_state_id(cr, uid, country_id, state_id):                value.update({'state_id':state_id})                if city and self.check_city_id(cr, uid, state_id, city):                    value.update({'city':city})                    if zip and self.check_zip_id(cr, uid, city, zip):                        value.update({'zip':zip})        return {'value':value}        def onchange_state(self, cr, uid, ids, state_id, city, zip, context=None):        value = {'city':False,'zip':False}        if state_id:            if city and self.check_city_id(cr, uid, state_id, city):                value.update({'city':city})                if zip and self.check_zip_id(cr, uid, city, zip):                    value.update({'zip':zip})        return {'value':value}        def onchange_city(self, cr, uid, ids, city, zip, context=None):        value = {'zip':False}        if city:            if zip and self.check_zip_id(cr, uid, city, zip):                value.update({'zip':zip})        return {'value':value}        def onchange_partner_id(self, cr, uid, id, partner_id, context=None):        result = {}        if partner_id:            part = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)            result['owner_name'] = part.name            result['street'] = part.street or False            result['city'] = part.city.id or False            result['zip'] =  part.zip.id or False            result['country_id'] =  part.country_id.id or False            result['state_id'] = part.state_id.id or False        return {'value': result}    res_partner_bank()class ir_actions_report_xml(osv.osv):    _inherit = "ir.actions.report.xml"    _columns = {        'use_default_customer': fields.boolean('Use default customer'),    }    ir_actions_report_xml()class res_partner(osv.osv):    _inherit = "res.partner"    _columns = {        'country_id': fields.many2one('res.country', 'Country'),        'state_id': fields.many2one("res.country.state", 'State', domain="[('country_id','=',country_id)]"),        'city': fields.many2one('res.city', 'City', domain="[('state_id','=',state_id)]"),        'zip': fields.many2one('postal.code', 'Zip', change_default=True, domain="[('city_id','=',city)]"),                'skype_id': fields.char('Skype ID', size=200),        'government_id': fields.char('Government ID', size=20),        'payment_ids': fields.many2many('res.partner.payment', 'partner_payment_rel', 'partner_id', 'payment_id', 'Payments'),        'tax_ids': fields.many2many('account.tax', 'partner_tax_rel', 'partner_id', 'tax_id', 'Taxes', domain=[('parent_id','=',False)]),                'fixed_discount': fields.float('Fixed Discount (%)', digits_compute= dp.get_precision('Discount')),        'default_shipping_id': fields.many2one('delivery.carrier', 'Default Shipping'),        'via_reseller_id': fields.many2one('res.partner', 'Via Reseller'),        'b2b_id': fields.many2one('res.partner', 'B2b'),        'alert': fields.text('Alert'),        'show_hscode_on_docs': fields.boolean('Show HS Code on Docs?'),        'non_standard_ship_invoice': fields.boolean('Non Standard Ship Invoice'),        'customer_sale_report_ids': fields.many2many('ir.actions.report.xml', 'customer_sale_report_rel',                                                      'partner_id', 'report_id',                                                     'Invoices'),                'default_payment_method': fields.many2one('account.journal', 'Default Payment Method', domain="[('type','=','bank'),('company_id','=',company_id)]"),        #Thanh: Add domain accounts belong into selected company        'property_account_payable': fields.property(            'account.account',            type='many2one',            relation='account.account',            string="Account Payable",            view_load=True,            domain="[('type', '=', 'payable'),('company_id', '=', company_id)]",            help="This account will be used instead of the default one as the payable account for the current partner",            required=True),        'property_account_receivable': fields.property(            'account.account',            type='many2one',            relation='account.account',            string="Account Receivable",            view_load=True,            domain="[('type', '=', 'receivable'),('company_id', '=', company_id)]",            help="This account will be used instead of the default one as the receivable account for the current partner",            required=True),        #Thanh: Add domain accounts belong into selected company                'property_expense_account': fields.property(            'account.account',            type='many2one',            relation='account.account',            string="Expense Account",            view_load=True,            domain="[('type', '!=', 'view'),('company_id', '=', company_id)]",            required=False),    }        _defaults = {        'type': 'default', # type 'default' is wildcard and thus inappropriate        'date': time.strftime('%Y-%m-%d'),        'show_hscode_on_docs': False,        'non_standard_ship_invoice': False,    }        def default_get(self, cr, uid, fields, context=None):        res = super(res_partner, self).default_get(cr, uid, fields, context=context)        report_obj = self.pool.get('ir.actions.report.xml')        if 'customer_sale_report_ids' in fields:            report_ids = report_obj.search(cr, uid, [('model','=','sale.order'),                                                    ('report_type','=','aeroo'),                                                    ('use_default_customer','=',True),])            res.update({'customer_sale_report_ids': [(6,0,report_ids)]})                        return res        def check_vat(self, cr, uid, ids, context=None):#         for partner in self.browse(cr, uid, ids, context=context):#             if not partner.vat:#                 continue#             if partner.is_company:#                 exist_ids = self.search(cr, uid, [('id','!=', partner.id),('is_company','=',True),('vat','=', partner.vat)])#                 if exist_ids:#                     return False        return True        _constraints = [(check_vat, 'This VAT number has been exist!', ["vat"])]        def onchange_company_id(self, cr, uid, ids, company_id, property_product_pricelist, country_id, context=None):        value = {'property_product_pricelist': False,                 'property_product_pricelist_purchase': False,                 'property_account_receivable': False,                 'property_account_payable': False,                }        account = self.pool.get('account.account')        pricelist = self.pool.get('product.pricelist')        if company_id:            account_rec_id = False            account_pay_id = False            currency_id = False            domain_rec = [('company_id','=',company_id),('type', '=', 'receivable')]            domain_pay = [('company_id','=',company_id),('type', '=', 'payable')]            if property_product_pricelist:                currency_id = pricelist.browse(cr, uid, property_product_pricelist).currency_id.id            else:                if country_id:                    country = self.pool.get('res.country').browse(cr, uid, country_id)                    currency_id = country.currency_id.id or False                        if currency_id:                account_rec_id = account.search(cr, uid, domain_rec + [('currency_id','in', [currency_id])])                account_rec_id = account_rec_id and account_rec_id[0] or False                                account_pay_id = account.search(cr, uid, domain_pay + [('currency_id','in', [currency_id])])                account_pay_id = account_pay_id and account_pay_id[0] or False                            if not account_rec_id:                account_rec_id = account.search(cr, uid, domain_rec)                account_rec_id = account_rec_id and account_rec_id[0] or False                        if not account_pay_id:                account_pay_id = account.search(cr, uid, domain_pay)                account_pay_id = account_pay_id and account_pay_id[0] or False            value.update({'property_account_receivable': account_rec_id,                          'property_account_payable': account_pay_id,})        return {'value':value}        def onchange_property_product_pricelist(self, cr, uid, ids, property_product_pricelist, context=None):        value = {}        return {'value':value}        def onchange_country_id(self, cr, uid, ids, company_id, country_id, property_product_pricelist, context=None):        value = {'state_id':False,'city':False,'zip':False,                 'property_account_receivable': False,                 'property_account_payable': False,}        account = self.pool.get('account.account')        pricelist = self.pool.get('product.pricelist')        if country_id:            country = self.pool.get('res.country').browse(cr, uid, country_id)            phone_code = country.phone_code            company_id = country.company_id.id            value.update({'phone':phone_code,'company_id':company_id, 'default_shipping_id': country.default_shipping_id.id or False,                          #'section_id': country.sales_team_id.id or False,                          #'user_id': country.sales_team_id and country.sales_team_id.user_id.id or False,                          'tax_ids': country.tax_ids and [(6,0,[x.id for x in country.tax_ids])] or False})                        if company_id:                account_rec_id = False                account_pay_id = False                currency_id = False                domain_rec = [('company_id','=',company_id),('type', '=', 'receivable')]                domain_pay = [('company_id','=',company_id),('type', '=', 'payable')]                if property_product_pricelist:                    currency_id = pricelist.browse(cr, uid, property_product_pricelist).currency_id.id                else:                    if country_id:                        country = self.pool.get('res.country').browse(cr, uid, country_id)                        currency_id = country.currency_id.id or False                                if currency_id:                    account_rec_id = account.search(cr, uid, domain_rec + [('currency_id','in', [currency_id])])                    account_rec_id = account_rec_id and account_rec_id[0] or False                                        account_pay_id = account.search(cr, uid, domain_pay + [('currency_id','in', [currency_id])])                    account_pay_id = account_pay_id and account_pay_id[0] or False                                    if not account_rec_id:                    account_rec_id = account.search(cr, uid, domain_rec)                    account_rec_id = account_rec_id and account_rec_id[0] or False                                if not account_pay_id:                    account_pay_id = account.search(cr, uid, domain_pay)                    account_pay_id = account_pay_id and account_pay_id[0] or False                value.update({'property_account_receivable': account_rec_id,                              'property_account_payable': account_pay_id,})        return {'value':value}        def onchange_state(self, cr, uid, ids, state_id, context=None):        return {'value':{'city':False,'zip':False}}        def onchange_city(self, cr, uid, ids, city, context=None):        return {'value':{'zip':False}}        def create(self, cr, uid, vals, context=None):        country_pool = self.pool.get('res.country')        if vals.get('country_id',False):            vals.update({'image':country_pool.read(cr, uid, vals['country_id'], ['flag'])['flag']})        return super(res_partner, self).create(cr, uid, vals, context=context)        def write(self, cr, uid, ids, vals, context=None):        country_pool = self.pool.get('res.country')        if vals.get('country_id',False):            vals.update({'image':country_pool.read(cr, uid, vals['country_id'], ['flag'])['flag']})        return super(res_partner, self).write(cr, uid, ids, vals, context=context)        def address_get(self, cr, uid, ids, adr_pref=None, context=None):        """ Find contacts/addresses of the right type(s) by doing a depth-first-search        through descendants within company boundaries (stop at entities flagged ``is_company``)        then continuing the search at the ancestors that are within the same company boundaries.        Defaults to partners of type ``'default'`` when the exact type is not found, or to the        provided partner itself if no type ``'default'`` is found either. """        adr_pref = set(adr_pref or [])        if 'default' not in adr_pref:            adr_pref.add('default')        result = {}        visited = set()        for partner in self.browse(cr, uid, filter(None, ids), context=context):            current_partner = partner            while current_partner:                to_scan = [current_partner]                # Scan descendants, DFS                while to_scan:                    record = to_scan.pop(0)                    visited.add(record)                    if record.type in adr_pref and not result.get(record.type):                        result[record.type] = record.id                    #Thanh: Get default for contact instead of company                    if record.type == 'default' and record.id != partner.id:                        result[record.type] = record.id                    if len(result) == len(adr_pref):                        return result                    to_scan = [c for c in record.child_ids                                 if c not in visited                                 if not c.is_company] + to_scan                # Continue scanning at ancestor if current_partner is not a commercial entity                if current_partner.is_company or not current_partner.parent_id:                    break                current_partner = current_partner.parent_id        # default to type 'default' or the partner itself        default = result.get('default', partner.id)        for adr_type in adr_pref:            result[adr_type] = result.get(adr_type) or default         return result        def show_street_city(self, cr, uid, ids, context=None):        if context is None:            context = {}        if isinstance(ids, (int, long)):            ids = [ids]        res = []        for record in self.browse(cr, uid, ids, context=context):            name = record.parent_id and record.parent_id.name + ' / ' or ''            name += record.name + ' / '            name += record.street and record.street + ' / ' or ''            name += record.city and record.city.name + ' / ' or ''            if name:                name = name[:-3]            res.append((record.id, name))        return res        def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):        if not args:            args = []        if not context:            context = {}        contact_ids = []        if context.get('parent_company_id',False):            contact_ids = self.search(cr, uid, [('parent_id','=',context['parent_company_id'])], limit=limit, context=context)            args += [('parent_id','!=',context['parent_company_id'])]        if name:            # Be sure name_search is symetric to name_get            name = name.split(' / ')[-1]            ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)        else:            ids = self.search(cr, uid, args, limit=limit, context=context)                        ids = contact_ids + ids        if context.get('show_street_city',False):            return self.show_street_city(cr, uid, ids, context)        else:            return self.name_get(cr, uid, ids, context)        def name_get(self, cr, uid, ids, context=None):        if context is None:            context = {}        if isinstance(ids, (int, long)):            ids = [ids]        res = []        for record in self.browse(cr, uid, ids, context=context):            name = record.name#             if record.parent_id and not record.is_company:#                 name =  "%s, %s" % (record.parent_id.name, name)            if context.get('show_address'):                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)                name = name.replace('\n\n','\n')                name = name.replace('\n\n','\n')            if context.get('show_email') and record.email:                name = "%s <%s>" % (name, record.email)            res.append((record.id, name))        return res        #Thanh: Redisplay Address    def _display_address(self, cr, uid, address, without_company=False, context=None):        '''        The purpose of this function is to build and return an address formatted accordingly to the        standards of the country where it belongs.        :param address: browse record of the res.partner to format        :returns: the address formatted in a display that fit its country habits (or the default ones            if not country is specified)        :rtype: string        '''        # get the information that will be injected into the display format        # get the address format#         address_format = "%(street)s, %(street2)s, %(city_name)s, %(state_name)s, %(zip_name)s, %(country_name)s"        address_format = "%(company_name)s / %(street)s / %(street2)s / %(city_name)s"        args = {            'city_name': address.city.name or '',            'zip_name': address.zip.name or '',            'state_code': address.state_id and address.state_id.code or '',            'state_name': address.state_id and address.state_id.name or '',            'country_code': address.country_id and address.country_id.code or '',            'country_name': address.country_id and address.country_id.name or '',            'company_name': address.parent_id and address.parent_id.name or '',        }        for field in self._address_fields(cr, uid, context=context):            args[field] = getattr(address, field) or ''#         if without_company:#             args['company_name'] = ''#         elif address.parent_id:#             #Thanh: No need to show compnay name# #             address_format = '%(company_name)s\n' + address_format#             address_format = address_format        return address_format % args    res_partner()# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: