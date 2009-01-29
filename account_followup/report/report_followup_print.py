# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
import ir

import pooler
from osv import osv
from report import report_sxw

class report_rappel(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_rappel, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time' : time,
            'ids_to_objects': self._ids_to_objects,
            'adr_get' : self._adr_get,
            'getLines' : self._lines_get,
            'get_text' : self._get_text
        })

    def _ids_to_objects(self, partners_ids):
        pool = pooler.get_pool(self.cr.dbname)
        all_partners = []
        for partner in partners_ids:
            partners = pool.get('account_followup.stat').browse(self.cr, self.uid, partner[2])
            for par in partners:
                all_partners.append(par.name)
        return all_partners

    def _adr_get(self, partner, type):
        res_partner = pooler.get_pool(self.cr.dbname).get('res.partner')
        res_partner_address = pooler.get_pool(self.cr.dbname).get('res.partner.address')
        adr = res_partner.address_get(self.cr, self.uid, [partner.id], [type])[type]
        return res_partner_address.read(self.cr, self.uid, [adr])

    def _lines_get(self, partner):
        moveline_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
        movelines = moveline_obj.search(self.cr, self.uid,
                [('partner_id', '=', partner.id),
                    ('account_id.type', '=', 'receivable'),
                    ('reconcile_id', '=', False), ('state', '<>', 'draft')])
        movelines = moveline_obj.read(self.cr, self.uid, movelines)
        return movelines

    def _get_text(self, partner):
        text = ""
        a = {}
        partner_line = pooler.get_pool(self.cr.dbname).get('account.move.line').search(self.cr, self.uid, [('partner_id','=',partner.id)])
        for i in pooler.get_pool(self.cr.dbname).get('account.move.line').browse(self.cr, self.uid, partner_line):
            if  i.followup_line_id and str(i.followup_line_id.delay)=='45':
                text = i.followup_line_id.description
                a['45'] = text
            elif i.followup_line_id and str(i.followup_line_id.delay)=='30':
                text = i.followup_line_id.description
                a['30'] = text
            elif i.followup_line_id and str(i.followup_line_id.delay)=='15':
                text = i.followup_line_id.description
                a['15'] = text
        text = (a.has_key('45') and a['45']) or (a.has_key('30') and a['30']) or (a.has_key('15') and a['15']) or ''
        text = text % {'partner_name':partner.name}
        return text


report_sxw.report_sxw('report.account_followup.followup.print',
        'res.partner', 'addons/account_followup/report/rappel.rml',
        parser=report_rappel)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

