
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero

import logging
_logger = logging.getLogger(__name__)


class PosConfig(models.Model):

    _inherit = 'pos.config'

    pp_active = fields.Boolean(
        string='plus pagos',
    )

    pp_cashbox_code = fields.Char(
        string='plus pagos cashbox',
    )

    pp_store_code = fields.Char(
        string='plus pagos code',
    )
    pp_fixed = fields.Boolean(
        string='Fixed_Amount',
    )
    pp_qr = fields.Char(
        string='qr URL',
    )
    pp_guid = fields.Char(
        string='GUID',
    )
    pp_cashbox_id = fields.Integer(
         string='cashbox id',
     ) 

    def action_pp_add_cashbox(self):
        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'plus_pagos')], limit=1)
        if acquirer:
            res = acquirer.pp_add_cashbox(self.pp_cashbox_code, self.name, self.pp_store_code, self.pp_fixed)
            if res['status']:
                self.pp_active = True
                self.pp_qr = res['data']['qr']['imagen']
                self.pp_guid = res['data']['guid']
                self.pp_cashbox_id = res['data']['cajaId']      

    def action_pp_unlink_cashbox(self):
        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'plus_pagos')], limit=1)
        if acquirer:
            res = acquirer.pp_unlink_cashbox(self.pp_cashbox_code)
            if res['status']:
                self.pp_active = False
                self.pp_qr = ''
                self.pp_guid = ''
                self.pp_cashbox_id = 0

