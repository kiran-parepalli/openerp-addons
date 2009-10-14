# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

from osv import fields, osv
from tools.translate import _

class account_move_line(osv.osv):
    _inherit = "account.move.line"

    def amount_to_pay(self, cr, uid, ids, name, arg={}, context={}):
        """ Return the amount still to pay regarding all the payemnt orders
        (excepting cancelled orders)"""
        if not ids:
            return {}
        cr.execute("""SELECT ml.id,
                    CASE WHEN ml.amount_currency < 0
                        THEN - ml.amount_currency
                        ELSE ml.credit
                    END -
                    (SELECT coalesce(sum(amount_currency),0)
                        FROM payment_line pl
                            INNER JOIN payment_order po
                                ON (pl.order_id = po.id)
                        WHERE move_line_id = ml.id
                        AND po.state != 'cancel') as amount
                    FROM account_move_line ml
                    WHERE id in (%s)""" % (",".join(map(str, ids))))
        r=dict(cr.fetchall())
        return r

    def _to_pay_search(self, cr, uid, obj, name, args):
        if not len(args):
            return []
        line_obj = self.pool.get('account.move.line')
        query = line_obj._query_get(cr, uid, context={})
        where = ' and '.join(map(lambda x: '''(SELECT
        CASE WHEN l.amount_currency < 0
            THEN - l.amount_currency
            ELSE l.credit
        END - coalesce(sum(pl.amount_currency), 0)
        FROM payment_line pl
        INNER JOIN payment_order po ON (pl.order_id = po.id)
        WHERE move_line_id = l.id AND po.state != 'cancel')''' \
        + x[1] + str(x[2])+' ',args))

        cr.execute(('''select id
            from account_move_line l
            where account_id in (select id
                from account_account
                where type=%s and active)
            and reconcile_id is null
            and credit > 0
            and ''' + where + ' and ' + query), ('payable',) )

        res = cr.fetchall()
        if not len(res):
            return [('id','=','0')]
        return [('id','in',map(lambda x:x[0], res))]

    def line2bank(self, cr, uid, ids, payment_type=None, context=None):
        """
        Try to return for each account move line a corresponding bank
        account according to the payment type.  This work using one of
        the bank of the partner defined on the invoice eventually
        associated to the line.
        Return the first suitable bank for the corresponding partner.
        """
        payment_mode_obj = self.pool.get('payment.mode')
        line2bank = {}
        if not ids:
            return {}
        bank_type = payment_mode_obj.suitable_bank_types(cr, uid, payment_type,
                context=context)
        for line in self.browse(cr, uid, ids, context=context):
            line2bank[line.id] = False
            if line.invoice and line.invoice.partner_bank:
                line2bank[line.id] = line.invoice.partner_bank.id
            elif line.partner_id:
                if not line.partner_id.bank_ids:
                    #raise osv.except_osv(_('Error !'), _('Partner '+ line.partner_id.name+ ' has no bank account defined'))
                    line2bank[line.id] = False
                else:
                    for bank in line.partner_id.bank_ids:
                        if bank.state in bank_type:
                            line2bank[line.id] = bank.id
                            break
                if line.id not in line2bank and line.partner_id.bank_ids:
                    line2bank[line.id] = line.partner_id.bank_ids[0].id
            else:
                raise osv.except_osv(_('Error !'), _('No partner defined on entry line'))
        return line2bank

    _columns = {
        'amount_to_pay' : fields.function(amount_to_pay, method=True,
            type='float', string='Amount to pay', fnct_search=_to_pay_search),
    }

account_move_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

