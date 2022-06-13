from odoo import fields, models


class PosPayment(models.Model):

    _inherit = "pos.payment"

    tx_ids = fields.One2many(
        "payment.transaction",
        "pos_payment_id",
        string="Electronic Transactions",
    )
    tx_manual_aprove = fields.Boolean(
        string="manual aprove",
    )
    tx_manual_authorization = fields.Char(
        string="Authorization",
    )
