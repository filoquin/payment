from odoo import api, fields, models, _
import requests
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
import base64

import logging
_logger = logging.getLogger(__name__)


class PosConfig(models.Model):

    _inherit = 'pos.config'

    mp_active = fields.Boolean(
        string='QR mercadopago',
    )
    mp_id = fields.Integer(
        string='Mp id',
    )
    mp_uuid = fields.Char(
        string='uuid',
    )
    mp_store_id = fields.Many2one(
        'mp.store',
        string='Store',
    )
    mp_external_id = fields.Char(
        string='external id',
    )
    mp_fixed = fields.Boolean(
        string='Fixed Amount',
        default=True,
    )
    mp_category = fields.Char(
        string='Category',
    )
    mp_qr_url = fields.Char(
        string='QR URL',
    )
    mp_qr = fields.Binary(
        string='QR',
        attachment=True,
    )
    mp_qr_code = fields.Text(
        string='QR code',
    )

    def action_add_mp(self):
        self.ensure_one()
        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'mp_qr')], limit=1)
        if acquirer:
            vals = {
              "name": self.name,
              "fixed_amount": self.mp_fixed,
              "store_id": self.mp_store_id.mp_id,
              "external_store_id": self.mp_store_id.external_id,
              "external_id": self.mp_external_id,
            }
            if self.mp_id:
                vals['mp_id'] = self.mp_id

                res = acquirer.mp_update_pos(vals)
            else:
                res = acquirer.mp_register_pos(vals)
            if res:
                vals = {
                    'mp_id': res['id'],
                    'mp_qr_url': res['qr']['image'],
                    'mp_uuid': res['uuid'],
                    'mp_active': True if res['status'] == 'active' else False
                }
                self.write(vals)
                self.action_url2base64()
                    
    def action_url2base64(self):
        response = requests.get(self.mp_qr_url)
        data = base64.b64encode(response.content)
        self.mp_qr = data 