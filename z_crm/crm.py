# -*- coding: utf-8 -*-################################################################################    OpenERP, Open Source Management Solution#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).##    This program is free software: you can redistribute it and/or modify#    it under the terms of the GNU Affero General Public License as#    published by the Free Software Foundation, either version 3 of the#    License, or (at your option) any later version.##    This program is distributed in the hope that it will be useful,#    but WITHOUT ANY WARRANTY; without even the implied warranty of#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the#    GNU Affero General Public License for more details.##    You should have received a copy of the GNU Affero General Public License#    along with this program.  If not, see <http://www.gnu.org/licenses/>.###############################################################################import timefrom openerp.osv import fields, osvfrom openerp.tools.translate import _from datetime import datetimeimport openerp.addons.decimal_precision as dpclass crm_lead(osv.osv):    _inherit = "crm.lead"    _order = "partner_name asc, priority,date_action,id desc"            _columns = {        'image': fields.binary("Image",            help="This field holds the image used as avatar for this contact, limited to 1024x1024px"),                        'country_id': fields.many2one('res.country', 'Country'),        'state_id': fields.many2one("res.country.state", 'State', domain="[('country_id','=',country_id)]"),        'city': fields.many2one('res.city', 'City', domain="[('state_id','=',state_id)]"),        'zip': fields.many2one('postal.code', 'Zip', change_default=True, domain="[('city_id','=',city)]"),            }        _defaults = {    }        #Thanh: Change the way get Address from Customer (City, Zip, ...)    def on_change_partner(self, cr, uid, ids, partner_id, context=None):        context = context or {}        context.update({'onchange_partner':True})                values = {}        if partner_id:            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)            values = {                'partner_name' : partner.name,                'street' : partner.street,                'street2' : partner.street2,                'city' : partner.city.id or False,                'state_id' : partner.state_id and partner.state_id.id or False,                'country_id' : partner.country_id and partner.country_id.id or False,                'email_from' : partner.email,                'phone' : partner.phone,                'mobile' : partner.mobile,                'fax' : partner.fax,                'zip': partner.zip.id or False,            }        return {'value' : values}        def check_state_id(self, cr, uid, country_id, state_id):        cr.execute('SELECT id FROM res_country_state WHERE id=%s and country_id=%s'%(state_id, country_id))        res = cr.fetchone()        if res and res[0]:            return True        return False        def check_city_id(self, cr, uid, state_id, city):        cr.execute('SELECT id FROM res_city WHERE id=%s and state_id=%s'%(city, state_id))        res = cr.fetchone()        if res and res[0]:            return True        return False        def check_zip_id(self, cr, uid, city, zip):        cr.execute('SELECT id FROM postal_code WHERE id=%s and city_id=%s'%(zip, city))        res = cr.fetchone()        if res and res[0]:            return True        return False        def onchange_country_id(self, cr, uid, ids, country_id, state_id, city, zip, context=None):        value = {'state_id':False,'city':False,'zip':False}        if country_id:            country = self.pool.get('res.country').browse(cr, uid, country_id)            phone_code = country.phone_code            company_id = country.company_id.id            value.update({'phone':phone_code,'company_id':company_id})            if state_id and self.check_state_id(cr, uid, country_id, state_id):                value.update({'state_id':state_id})                if city and self.check_city_id(cr, uid, state_id, city):                    value.update({'city':city})                    if zip and self.check_zip_id(cr, uid, city, zip):                        value.update({'zip':zip})        return {'value':value}        def onchange_state(self, cr, uid, ids, state_id, city, zip, context=None):        value = {'city':False,'zip':False}        if state_id:            if city and self.check_city_id(cr, uid, state_id, city):                value.update({'city':city})                if zip and self.check_zip_id(cr, uid, city, zip):                    value.update({'zip':zip})        return {'value':value}        def onchange_city(self, cr, uid, ids, city, zip, context=None):        value = {'zip':False}        if city:            if zip and self.check_zip_id(cr, uid, city, zip):                value.update({'zip':zip})        return {'value':value}        def create(self, cr, uid, vals, context=None):        country_pool = self.pool.get('res.country')        if vals.get('country_id',False):            vals.update({'image':country_pool.read(cr, uid, vals['country_id'], ['flag'])['flag']})        return super(crm_lead, self).create(cr, uid, vals, context=context)        def write(self, cr, uid, ids, vals, context=None):        country_pool = self.pool.get('res.country')        if vals.get('country_id',False):            vals.update({'image':country_pool.read(cr, uid, vals['country_id'], ['flag'])['flag']})        return super(crm_lead, self).write(cr, uid, ids, vals, context=context)    crm_lead()# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: