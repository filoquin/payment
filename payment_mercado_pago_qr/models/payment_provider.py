import requests
import logging
import base64


from odoo import fields, models
from .mercado_pago_request import MercadoPagoRequest
from odoo.exceptions import UserError

from ..const import MP_URL


_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("mercado_pago_qr", "Mercado Pago")],
        ondelete={"mercado_pago_qr": "set default"},
    )
    mercado_pago_qr_access_token = fields.Char(
        string="Mercado Pago Access Token",
        required_if_provider="mercado_pago_qr",
        groups="base.group_system",
    )
    mp_user_id = fields.Char()
    store_id = fields.Char()
    pos_id = fields.Char(copy=False)
    mp_external_store_id = fields.Char(copy=False)
    mp_external_pos_id = fields.Char(copy=False)
    mp_qr_url = fields.Char(string="QR URL", copy=False)
    mp_qr_image = fields.Binary(
        string="QR",
        attachment=True,
        copy=False,
    )

    def set_qr_info(self):
        self.ensure_one()
        mercado_pago = MercadoPagoRequest(self.mercado_pago_qr_access_token)
        data = mercado_pago.call_mercado_pago("get", f"/stores/{self.store_id}", {})
        if data.get("external_id"):
            self.mp_external_store_id = data["external_id"]
        else:
            body = {"external_id": f"store{self.id}"}
            mercado_pago.call_mercado_pago(
                "put", f"/users/{self.mp_user_id}/stores/{self.store_id}", body
            )
            self.mp_external_store_id = f"store{self.id}"

        if self.pos_id:
            data = mercado_pago.call_mercado_pago("get", f"/pos/{self.pos_id}", {})
            self.mp_qr_url = data["qr"]["template_document"]
            response = requests.get(data["qr"]["image"])
            image = base64.b64encode(response.content)
            self.mp_qr_image = image
            if data.get("external_id"):
                self.mp_external_pos_id = data["external_id"]
            else:
                raise UserError("El pos no tiene external_id")
        else:
            body = {
                "external_id": f"pos{self.id}",
                "external_store_id": self.mp_external_store_id,
                "fixed_amount": True,
                "name": self.name,
                "store_id": self.store_id,
            }
            data = mercado_pago.call_mercado_pago("post", "/pos", body)
            response = requests.get(data["qr"]["image"])
            image = base64.b64encode(response.content)
            self.write(
                {
                    "mp_external_pos_id": data["external_id"],
                    "pos_id": str(data["id"]),
                    "mp_qr_url": data["qr"]["template_document"],
                    "mp_qr_image": image,
                }
            )

    def mp_payment_get(self, payment_id):
        mercado_pago = MercadoPagoRequest(self.mercado_pago_qr_access_token)
        resp = mercado_pago.call_mercado_pago(
            "get", f"/v1/payments/{payment_id}", {}, self.mp_test_scope
        )
        _logger.info("mp_payment_get(), response from Mercado Pago: %s", resp)
        return resp

    def find_more_pos(self):
        self.ensure_one()
        mercado_pago = MercadoPagoRequest(self.mercado_pago_qr_access_token)
        data = mercado_pago.call_mercado_pago("get", "/pos", {})
        existing_qr = self.search([("code", "=", "mercado_pago_qr")]).mapped("pos_id")
        if "results" in data:
            for pos in data["results"]:
                if str(pos["id"]) not in existing_qr and pos.get("external_id"):
                    new_provider = self.copy(
                        default={
                            "name": pos.get("name") or pos.get("id"),
                            "mp_user_id": pos.get("user_id"),
                            "store_id": pos.get("store_id"),
                            "pos_id": str(pos.get("id")),
                        }
                    )
                    new_provider.set_qr_info()
