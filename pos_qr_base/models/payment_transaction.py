from odoo import fields, models


class PaymentTransaction(models.Model):

    _inherit = 'payment.transaction'

    pos_payment_id = fields.Many2one(
        'pos.payment',
        string='Pos payment',
    )

