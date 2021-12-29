from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CashControlDetails(models.TransientModel):
    _name = 'sale.order.add_credit_note'
    _description = 'Sale order add credit note'

    order_id = fields.Many2one(
        'sale.order',
        string='Sale order',
        required=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        related='order_id.partner_id'
    )

    move_line_id = fields.Many2one(
        'account.move.line',
        string='refund',
        required=True,
    )

    def action_add_credit_note(self):
        self.order_id.refund_move_lines_ids=[(4, self.move_line_id.id)]