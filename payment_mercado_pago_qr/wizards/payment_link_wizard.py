# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields


class PaymentLinkWizard(models.TransientModel):
    _inherit = "payment.link.wizard"

    available_qr_provider_ids = fields.Many2many(
        comodel_name="payment.provider", compute="_compute_available_qr_provider_ids"
    )
    qr_provider_id = fields.Many2one("payment.provider")

    @api.depends("res_model", "res_id")
    def _compute_available_qr_provider_ids(self):
        for rec in self:
            related_document = self.env[rec.res_model].browse(rec.res_id)
            company_id = related_document.company_id
            partner_id = related_document.partner_id
            currency_id = related_document.currency_id
            rec.available_qr_provider_ids = (
                self.env["payment.provider"]
                ._get_compatible_providers(
                    company_id=company_id.id,
                    partner_id=partner_id.id,
                    amount=related_document.amount_total,
                    currency_id=currency_id.id,
                )
                .filtered(lambda x: x.code == "mercado_pago_qr")
            )

    def action_create_payment(self):
        wizard_sudo = self.sudo()
        transaction_vals = wizard_sudo._prepare_payment_transaction_vals()
        transaction = wizard_sudo.env["payment.transaction"].create(transaction_vals)
        transaction.mp_payment_order_create()
        transaction.mp_payment_order_get()
        return transaction.action_mp_open_qr()

    def _prepare_payment_transaction_vals(self):
        self.ensure_one()
        related_document = self.env[self.res_model].browse(self.res_id)
        partner_id = related_document.partner_id.id
        currency_id = related_document.currency_id.id
        payment_method_id = (
            self.env["payment.method"]
            .sudo()
            ._get_compatible_payment_methods(
                self.qr_provider_id.ids,
                partner_id,
                currency_id=currency_id,
            )
        )
        res = {
            "provider_id": self.qr_provider_id.id,
            "payment_method_id": payment_method_id.id,
            "reference": self.env["payment.transaction"]._compute_reference(
                self.qr_provider_id.code, prefix=related_document.display_name
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
