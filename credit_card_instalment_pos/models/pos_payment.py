from odoo import api, fields, models, _
from odoo.tools import formatLang


class PosPayment(models.Model):
 
    _inherit = "pos.payment"

    instalment_id = fields.Many2one(
        'account.card.instalment',
        string='Instalment plan'
    )

    card_type = fields.Selection(
        [('credit', 'credit'), ('debit', 'debit')],
        related="payment_method_id.card_type"
    )

    magnet_bar = fields.Char(
        'magnet bar'
    )
    card_number = fields.Char(
        'Card number'
    )
    tiket_number = fields.Char(
        'Tiket number'
    )
    lot_number = fields.Char(
        'Lot number'
    )
    fee = fields.Float(
        string='Fee',
        default=0,
    )
    total_amount = fields.Float(
        string='total amount',
        default=0,
    )
