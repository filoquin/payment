from werkzeug import urls

from odoo import _, fields, models


class PaymentQrWizard(models.TransientModel):
    _name = "payment.qr.wizard"
    _description = "Payment QR"

    tx_id = fields.Many2one("payment.transaction")
    state = fields.Selection(
        string="Status",
        selection=[
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("authorized", "Authorized"),
            ("done", "Confirmed"),
            ("cancel", "Canceled"),
            ("error", "Error"),
        ],
        related="tx_id.state",
    )
    amount = fields.Monetary(
        string="Amount", currency_field="currency_id", related="tx_id.amount"
    )
    currency_id = fields.Many2one(
        string="Currency", comodel_name="res.currency", related="tx_id.currency_id"
    )

    provider_id = fields.Many2one("payment.provider", related="tx_id.provider_id")
    mp_qr_image = fields.Binary(
        string="QR", attachment=True, related="provider_id.mp_qr_image"
    )

    def action_check_status(self):
        self.tx_id.sudo().mp_payment_order_get()
        if self.state != "done":
            return self.tx_id.sudo().action_mp_open_qr()

    def action_cancel_order(self):
        self.tx_id.sudo().mp_payment_order_cancel()
        self.tx_id.sudo()._set_canceled(f"Canceled by user {self.env.user.name}")
