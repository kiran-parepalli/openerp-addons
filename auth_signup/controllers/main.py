# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
import logging
import urllib

import werkzeug

import openerp
from openerp.modules.registry import RegistryManager
from ..res_users import SignupError

_logger = logging.getLogger(__name__)

class Controller(openerp.addons.web.http.Controller):
    _cp_path = '/auth_signup'

    @openerp.addons.web.http.jsonrequest
    def retrieve(self, req, dbname, token):
        """ retrieve the user info (name, login or email) corresponding to a signup token """
        registry = RegistryManager.get(dbname)
        with registry.cursor() as cr:
            res_partner = registry.get('res.partner')
            user_info = res_partner.signup_retrieve_info(cr, openerp.SUPERUSER_ID, token)
        return user_info

    @openerp.addons.web.http.jsonrequest
    def signup(self, req, dbname, token, name, login, password):
        """ sign up a user (new or existing)"""
        values = {'name': name, 'login': login, 'password': password}
        return self._signup_with_values(req, dbname, token, values)

    def _signup_with_values(self, req, dbname, token, values):
        registry = RegistryManager.get(dbname)
        with registry.cursor() as cr:
            res_users = registry.get('res.users')
            try:
                res_users.signup(cr, openerp.SUPERUSER_ID, values, token)
            except SignupError, e:
                return {'error': openerp.tools.exception_to_unicode(e)}
            cr.commit()
        return {}

    @openerp.addons.web.http.httprequest
    def reset_password(self, req, dbname, login):
        """ retrieve user, and perform reset password """
        registry = RegistryManager.get(dbname)
        with registry.cursor() as cr:
            try:
                res_users = registry.get('res.users')
                res_users.reset_password(cr, openerp.SUPERUSER_ID, login)
                cr.commit()
                message = 'An email has been sent with credentials to reset your password'
            except Exception as e:
                # signup error
                _logger.exception('error when resetting password')
                message = e.message
        params = [('action', 'login'), ('error_message', message)]
        return werkzeug.utils.redirect("/#" + urllib.urlencode(params))

# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:
