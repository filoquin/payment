from odoo import fields, models
import requests
import base64


class MpPosMixin(models.AbstractModel):
    _name = "mp.pos"
    _description = "Mercado pago Pos mixin"

    mp_active = fields.Boolean(
        string="QR mercadopago",
    )
    mp_id = fields.Integer(
        string="Mp id",
    )
    mp_uuid = fields.Char(
        string="uuid",
    )
    mp_store_id = fields.Many2one(
        "mp.store",
        string="Store",
    )
    mp_external_id = fields.Char(
        string="external id",
    )
    mp_fixed = fields.Boolean(
        string="Fixed Amount",
        default=True,
    )
    mp_category = fields.Char(
        string="Category",
    )
    mp_qr_url = fields.Char(
        string="QR URL",
    )
    mp_qr = fields.Binary(
        string="QR",
        attachment=True,
    )
    mp_qr_code = fields.Text(
        string="QR code",
    )

    def action_url2base64(self):
        response = requests.get(self.mp_qr_url)
        data = base64.b64encode(response.content)
        self.mp_qr = data
