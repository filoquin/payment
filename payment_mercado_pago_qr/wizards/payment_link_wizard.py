# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields


class PaymentLinkWizard(models.TransientModel):
    _inherit = "payment.link.wizard"

    is_qr_provider = fields.Boolean(compute="_compute_is_qr_provider")

    @api.depends("payment_provider_selection")
    def _compute_is_qr_provider(self):
        for rec in self:
            if isinstance(rec.payment_provider_selection, int):
                provider = (
                    self.env["payment.provider"]
                    .sudo()
                    .browse(rec.payment_provider_selection)
                )
                rec.is_qr_provider = provider.code == "mercado_pago_qr"
            else:
                rec.is_qr_provider = False

    def action_create_payment(self):
        wizard_sudo = self.sudo()
        transaction_vals = wizard_sudo._prepare_payment_transaction_vals()
        transaction = wizard_sudo.env["payment.transaction"].create(transaction_vals)
        transaction.mp_payment_order_create()
        transaction.mp_payment_order_get()
        return transaction.action_mp_open_qr()

    def _prepare_payment_transaction_vals(self):
        self.ensure_one()
        provider = (
            self.env["payment.provider"]
            .sudo()
            .browse(int(self.payment_provider_selection))
        )
        res = {
            "provider_id": int(self.payment_provider_selection),
            "reference": self.env["payment.transaction"]._compute_reference(
                provider.code, prefix=self.description
            ),
            "amount": self.amount,
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.id,
        }
        if self.res_model == "account.move":
            res["invoice_ids"] = [(6, 0, [self.res_id])]
        elif self.res_model == "sale.order":
            res["sale_order_ids"] = [(6, 0, [self.res_id])]

        return res
