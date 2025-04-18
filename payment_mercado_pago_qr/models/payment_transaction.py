import logging

from odoo import models, _
from odoo.tools.float_utils import json_float_round
from odoo.exceptions import ValidationError
from .mercado_pago_request import MercadoPagoRequest

from ..const import MP_URL


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):

    _inherit = "payment.transaction"

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of payment to find the transaction based on mercado_pago_qr data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "mercado_pago_qr":
            return tx
        merchand_id = notification_data.get("id")
        tx = self.search(
            [
                ("provider_reference", "=", str(merchand_id)),
                ("provider_code", "=", "mercado_pago_qr"),
            ]
        )
        if not tx:
            raise ValidationError(
                _(
                    "No transaction found matching reference %s.",
                    notification_data.get("id"),
                )
            )
        return tx

    def _process_notification_data(self, notification_data):
        """Override of payment to process the transaction based on mercado_pago_qr data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != "mercado_pago_qr":
            return
        self.mp_payment_order_get()

    def mp_payment_order_create(self):
        self.ensure_one()
        base_url = self.get_base_url()
        base_url = "https://hormiga.ar/"
        data = {
            "title": self.reference,
            "notification_url": f"{base_url}/pos_mercado_pago/notification",
            "description": self.company_id.display_name,
            "total_amount": json_float_round(self.amount, 2),
            "items": [
                {
                    "sku_number": _("0001"),
                    "category": _("general"),
                    "title": self.reference + " sale",
                    "description": _("odoo sale"),
                    "unit_price": json_float_round(self.amount, 2),
                    "quantity": 1,
                    "unit_measure": "unit",
                    "total_amount": json_float_round(self.amount, 2),
                }
            ],
            "external_reference": self.reference,
        }

        mercado_pago = MercadoPagoRequest(self.provider_id.mercado_pago_qr_access_token)
        resp = mercado_pago.call_mercado_pago(
            "put",
            f"/instore/qr/seller/collectors/{self.provider_id.mp_user_id}/stores/{self.provider_id.mp_external_store_id}/pos/{self.provider_id.mp_external_pos_id}/orders",
            data,
        )
        _logger.debug("mp_payment_order_create(), response from Mercado Pago: %s", resp)
        return resp

    def mp_payment_order_get(self):
        self.ensure_one()
        mercado_pago = MercadoPagoRequest(self.provider_id.mercado_pago_qr_access_token)

        resp = mercado_pago.call_mercado_pago(
            "get", f"/merchant_orders/?external_reference={self.reference}", {}
        )
        _logger.info("mp_payment_order_get(), response from Mercado Pago: %s", resp)
        if "elements" in resp and resp["elements"]:
            for merchand_order in resp["elements"]:
                if merchand_order["status"] in ["pending", "opened"]:
                    self.provider_reference = merchand_order["id"]
                    self._set_pending()
                elif merchand_order["status"] == "expired":
                    self._set_canceled("The order is expired")
                elif merchand_order["status"] == "closed":
                    # TODO: payment as child_transaction_ids ?
                    self.provider_reference = merchand_order["id"]
                    self.amount = merchand_order["paid_amount"]
                    self._set_done()

    def mp_payment_order_cancel(self):
        mercado_pago = MercadoPagoRequest(self.provider_id.mercado_pago_qr_access_token)
        resp = mercado_pago.call_mercado_pago(
            "delete",
            f"/instore/qr/seller/collectors/{self.provider_id.mp_user_id}/pos/{self.provider_id.mp_external_pos_id}/orders",
            {},
        )
        _logger.info("mp_payment_order_cancel(), response from Mercado Pago: %s", resp)
        return resp

    def action_mp_open_qr(self):
        view_id = self.env.ref("payment_mercado_pago_qr.payment_qr_wizard_view_form").id
        view = {
            "name": self.provider_id.display_name,
            "view_mode": "form",
            "view_id": view_id,
            "view_type": "form",
            "res_model": "payment.qr.wizard",
            "res_id": False,
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {"default_tx_id": self.id},
        }
        return view
