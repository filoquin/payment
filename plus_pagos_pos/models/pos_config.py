from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
import requests
import base64
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
        default=True,
    )
    pp_qr_url = fields.Char(
        string='qr URL',
    )
    pp_guid = fields.Char(
        string='GUID',
    )
    pp_cashbox_id = fields.Integer(
         string='cashbox id',
    ) 

    pp_qr = fields.Binary(
        string='QR',
        attachment=True,
    )

    def action_pp_add_cashbox(self):
        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'plus_pagos')], limit=1)
        if acquirer:
            res = acquirer.pp_add_cashbox(self.pp_cashbox_code, self.name, self.pp_store_code, self.pp_fixed)
            if res['status']:
                self.pp_active = True
                self.pp_qr_url = res['data']['qr']['imagen']
                self.pp_guid = res['data']['guid']
                self.pp_cashbox_id = res['data']['cajaId']
                self.action_pp_url2base64()      

    def action_pp_unlink_cashbox(self):
        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'plus_pagos')], limit=1)
        if acquirer:
            res = acquirer.pp_unlink_cashbox(self.pp_cashbox_code)
            if res:
                self.pp_active = False
                self.pp_qr = ''
                self.pp_guid = ''
                self.pp_cashbox_id = 0

    def action_pp_get_cashbox(self):
        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'plus_pagos')], limit=1)
        if acquirer:
            res = acquirer.pp_get_cashbox(self.pp_cashbox_code)
            _logger.info(res)
            
    def action_pp_create_order(self):
        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'plus_pagos')], limit=1)
        if acquirer:
            res = acquirer.pp_create_order(self.pp_cashbox_code, 20, 'test', 'test')
            _logger.info(res)

    def action_pp_url2base64(self):
        response = requests.get(self.pp_qr_url)
        data = base64.b64encode(response.content)
        self.pp_qr = data 