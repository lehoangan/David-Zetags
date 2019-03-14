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
            'get_address': self.get_address,
            'get_street': self.get_street,
            'get_street2': self.get_street2,
        })

    def get_address(self, partner):
        address = partner.street and partner.street + ' / ' or ''
        address += partner.street2 and partner.street2 + ' / ' or ''
        address += partner.city and partner.city.name + ' / ' or ''
        address += partner.state_id and partner.state_id.name + ' / ' or ''
        address += partner.zip and partner.zip.name + ' / ' or ''
        address += partner.country_id and partner.country_id.name + ' / ' or ''
        if address:
            address = address[:-3]
        return address

    def get_street(self, partner):
        return partner.street or ''

    def get_street2(self, partner):
        return partner.street2 or ''

    def get_address02(self, partner):
        address = partner.city and partner.city.name + ', ' or ''
        address += partner.state_id and partner.state_id.name + ', ' or ''
        address += partner.zip and partner.zip.name or ''
        return address

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

