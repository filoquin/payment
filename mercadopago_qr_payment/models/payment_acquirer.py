from odoo import fields, models, _
from odoo.exceptions import UserError
import requests
from datetime import datetime, timedelta
import logging
from odoo.http import request

_logger = logging.getLogger(__name__)


MP_URL = "https://api.mercadopago.com/"


class PaymentAcquirer(models.Model):

    _inherit = "payment.acquirer"

    provider = fields.Selection(selection_add=[("mp_qr", "QR Mercado Pago")])

    mp_public_key = fields.Char(
        string="Public Key",
    )

    mp_access_token = fields.Char(
        string="Access Token",
    )
    store_ids = fields.One2many(
        "mp.store",
        "acquirer_id",
        string="Stores",
    )
    mp_qr_title = fields.Char(string="Order title", default="My MP Odoo Order")
    mp_qr_description = fields.Char(
        string="Order description", default="My MP Odoo Order"
    )
    mp_default_partner_id = fields.Many2one(
        "res.partner",
        string="Default partner",
    )
    mp_ipn_url = fields.Char(
        string="IPN base URL", default=lambda self: self.mp_base_url()
    )

    def mp_base_url(self):
        url = ""
        if request:
            url = request.httprequest.url_root

        return url or self.env["ir.config_parameter"].sudo().get_param("web.base.url")

    def _get_feature_support(self):
        feature_support = super()._get_feature_support()
        feature_support["authorize"].append("mp_qr")
        return feature_support

    def mp_get_user_id(self):
        self.ensure_one()
        return self.mp_access_token.split("-")[-1]

    def action_mp_create_stores(self):
        user_id = self.mp_get_user_id()
        api_url = MP_URL + "users/%s/stores" % user_id
        headers = {"Authorization": "Bearer %s" % self.mp_access_token}
        store_ids = self.store_ids.filtered(lambda s: s.state == "draft")
        for store_id in store_ids:
            request_data = store_id.prepare_request_data()
            response = requests.post(api_url, headers=headers, json=request_data)
            res = response.json()
            if response.status_code == 201:
                store_id.state = "active"
                store_id.mp_id = int(res["id"])
            else:
                raise UserError(res["message"])

    def action_mp_unlink_store(self, mp_id):
        user_id = self.mp_get_user_id()
        api_url = MP_URL + "users/%s/stores/%s" % (user_id, mp_id)
        headers = {"Authorization": "Bearer %s" % self.mp_access_token}
        response = requests.delete(api_url, headers=headers)
        if response.status_code == 200:
            return True
        else:
            raise UserError(response.content)

    def action_mp_update_store(self, mp_id):
        user_id = self.mp_get_user_id()

        api_url = MP_URL + "users/%s/stores/%s" % (user_id, mp_id)
        _logger.info(api_url)
        headers = {
            "Authorization": "Bearer %s" % self.mp_access_token,
            "Content-Type": "application/json",
        }
        store_id = self.store_ids.filtered(lambda s: s.mp_id == mp_id)
        request_data = store_id.prepare_request_data()
        response = requests.put(api_url, headers=headers, json=request_data)
        if response.status_code == 200:
            store_id.state = "active"
        else:
            raise UserError(response.content)

    def mp_register_pos(self, vals):
        api_url = MP_URL + "pos"
        headers = {"Authorization": "Bearer %s" % self.mp_access_token}
        request_data = {
            "name": vals["name"],
            "fixed_amount": vals["fixed_amount"],
            "store_id": vals["store_id"],
            "external_store_id": vals["external_store_id"],
            "external_id": vals["external_id"],
        }
        response = requests.post(api_url, headers=headers, json=request_data)
        res = response.json()

        if response.status_code == 201:
            return res
        else:
            raise UserError(response.content)

    def mp_update_pos(self, vals):
        api_url = MP_URL + "pos/%s" % vals["mp_id"]
        del vals["mp_id"]
        headers = {
            "Authorization": "Bearer %s" % self.mp_access_token,
            "Content-Type": "application/json",
        }
        request_data = vals
        response = requests.put(api_url, headers=headers, json=request_data)

        if response.status_code == 200:
            res = response.json()
            return res
        else:
            raise UserError(response.content)

    def create_order(self, data):
        values = self.qr_prepare_transaction(data)
        tx_obj = self.env["payment.transaction"]
        tx = tx_obj.sudo().create(values)
        tx.sudo().s2s_do_transaction()
        # tx.sudo()._set_transaction_authorized()

        return {
            "state": tx.state,
            "transaction_id": tx.id,
            "reference": tx.reference,
            "amount": tx.amount,
        }

    def xcreate_order(self, data):

        user_id = self.mp_get_user_id()
        api_url = MP_URL + "instore/qr/seller/collectors/%s/stores/%s/pos/%s/orders" % (
            user_id,
            data["store_external_id"],
            data["pos_external_id"],
        )
        headers = {
            "Authorization": "Bearer %s" % self.mp_access_token,
            "Content-Type": "application/json",
        }

        base_url = self.get_base_url()

        external_reference = "%s-%s-%s" % (
            data["pos_external_id"],
            data["reference"],
            fields.Datetime.now(),
        )
        request_data = {
            "external_reference": external_reference,
            "title": data["name"],
            "description": "Odoo QR",
            "notification_url": base_url + "mercadopago_qr_payment/ipn/%s" % self.id,
            "total_amount": data["amount"],
            "items": [
                {
                    "sku_number": "odoo",
                    "category": "general",
                    "title": "Pos sale",
                    "description": "odoo sale",
                    "unit_price": data["amount"],
                    "quantity": 1,
                    "unit_measure": "unit",
                    "total_amount": data["amount"],
                }
            ],
        }
        _logger.info(request_data)

        response = requests.put(api_url, headers=headers, json=request_data)
        if response.status_code == 204:
            return True
        else:
            raise UserError(response.content)

    def mp_qr_pos_transaction_check(self, external_reference):

        api_url = MP_URL + "merchant_orders?external_reference=%s" % (
            external_reference
        )
        api_url = MP_URL + "merchant_orders"

        headers = {"Authorization": "Bearer %s" % self.mp_access_token}
        response = requests.get(api_url, headers=headers)
        _logger.info(response.status_code)
        _logger.info(response.content)
        if response.status_code == 200:
            return True
        else:
            raise UserError(response.content)

        _logger.info(api_url)

        return True

    def qr_prepare_transaction(self, data):
        external_reference = data["reference"]

        if "partner_id" in data:
            partner_id = self.env["res.partner"].browse(data["partner_id"])
        else:
            partner_id = self.mp_default_partner_id

        values = {
            "amount": data["amount"],
            "acquirer_id": self.id,
            "type": "server2server",
            "currency_id": self.env.user.company_id.currency_id.id,
            "reference": external_reference,
            "partner_id": partner_id.id,
            "partner_country_id": partner_id.country_id.id,
            "store_external_id": str(data["store_external_id"]),
            "pos_external_id": str(data["pos_external_id"]),
        }
        _logger.info(values)
        return values

    # Para obtener el estado del pago de manera proactiva
    """
        curl -X GET \
       -H 'Authorization: Bearer $ACCESS_TOKEN' \
       https://api.mercadopago.com/merchant_orders?external_reference=$EXTERNAL_REFERENCE 
        """
    """
        Obtener un pago por id que figura en el cliente 
        https://www.mercadopago.com.ar/developers/es/reference/payments/_payments_id/get
    """
    """
    Manejo oauth
    https://www.mercadopago.com.ar/developers/es/guides/security/oauth
    """

    def mp_get_lost_transaction(self, **kwargs):

        api_url = MP_URL + "merchant_orders/search"
        payload = {
            "date_created_from": "2021-08-04T10:55:21.254-04:00",
            "date_created_to": "2021-09-10T10:55:21.254-04:00",
            "order_status": "paid",
        }
        headers = {
            "Authorization": "Bearer %s" % self.mp_access_token,
            "Content-Type": "application/json",
        }
        response = requests.get(api_url, headers=headers, params=payload)
        _logger.info(response.content)
        if response.status_code == 200:
            data = response.json()
            if not data["elements"]:
                return
            for order in data["elements"]:
                if order["external_reference"] and len(order["payments"]):
                    tx = (
                        self.env["payment.transaction"]
                        .sudo()
                        .search(
                            [
                                ("reference", "=", order["external_reference"]),
                                # ('acquirer_id', '=', self.id)
                            ],
                        )
                    )
                    _logger.info(order)
                    _logger.info(tx)
                    if not len(tx):
                        values = {
                            "amount": order["total_amount"],
                            "acquirer_id": self.id,
                            "type": "server2server",
                            "currency_id": self.env.user.company_id.currency_id.id,
                            "reference": order["external_reference"],
                            "partner_id": self.mp_default_partner_id.id,
                            "partner_country_id": self.mp_default_partner_id.country_id.id,
                            #'store_external_id': str(data['store_external_id']),
                            #'pos_external_id': str(data['pos_external_id']),
                        }
                        tx_obj = self.env["payment.transaction"]
                        tx = tx_obj.sudo().create(values)


class PaymentTransaction(models.Model):

    _inherit = "payment.transaction"

    merchant_order_id = fields.Char(
        string="merchant order",
    )
    store_external_id = fields.Char(
        string="store",
    )
    pos_external_id = fields.Char(
        string="pos",
    )

    def mp_qr_s2s_do_transaction(self, **kwargs):

        acquirer_id = self.acquirer_id
        user_id = acquirer_id.mp_get_user_id()

        api_url = MP_URL + "instore/qr/seller/collectors/%s/stores/%s/pos/%s/orders" % (
            user_id,
            self.store_external_id,
            self.pos_external_id,
        )

        headers = {
            "Authorization": "Bearer %s" % acquirer_id.mp_access_token,
            "Content-Type": "application/json",
        }

        base_url = self.acquirer_id.mp_ipn_url

        request_data = {
            "external_reference": self.reference,
            "title": acquirer_id.mp_qr_title,
            "description": acquirer_id.mp_qr_description,
            "notification_url": base_url
            + "mercadopago_qr_payment/ipn/%s" % self.acquirer_id.id,
            "total_amount": self.amount,
            "items": [
                {
                    "sku_number": "odoo",
                    "category": "general",
                    "title": "Pos sale",
                    "description": "odoo sale",
                    "unit_price": self.amount,
                    "quantity": 1,
                    "unit_measure": "unit",
                    "total_amount": self.amount,
                }
            ],
        }
        _logger.info(request_data)
        _logger.info(api_url)
        response = requests.put(api_url, headers=headers, json=request_data)

        _logger.info(response.status_code)
        if response.status_code == 204:
            self._set_transaction_pending()

            return True
        else:
            raise UserError(response.content)

    def mp_qr_process_ipn(self, kwargs):
        acquirer_id = self.env["payment.acquirer"].search(
            [("provider", "=", "mp_qr"), ("id", "=", kwargs["acquirer_id"])], limit=1
        )

        if kwargs["topic"] == "merchant_order":
            api_url = MP_URL + "merchant_orders/%s" % kwargs["id"]
            headers = {
                "Authorization": "Bearer %s" % acquirer_id.mp_access_token,
                "Content-Type": "application/json",
            }

            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                data = response.json()

                if data["status"] == "opened":
                    tx = self.search(
                        [
                            ("reference", "=", data["external_reference"]),
                            # ('acquirer_id.provider', '=', 'mp_qr')
                        ]
                    )
                    if len(tx):

                        tx.amount = data["total_amount"]
                        tx.merchant_order_id = str(kwargs["id"])
                        tx._set_transaction_authorized()
            else:
                _logger.error(response.content)

    def mp_qr_transaction_check(self):
        for tx in self:
            api_url = MP_URL + "merchant_orders?external_reference=%s" % (tx.reference)
            headers = {"Authorization": "Bearer %s" % tx.acquirer_id.mp_access_token}
            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                data = response.json()["elements"]
                if data:
                    data = data[0]
                    tx.merchant_order_id = str(data["id"])
                    has_payment = False
                    total_amount = 0.0
                    for payment in data["payments"]:
                        if payment["status"] == "approved":
                            has_payment = True
                            total_amount += payment["total_paid_amount"]
                    if has_payment:
                        tx.amount = total_amount
                        tx._set_transaction_authorized()
                else:
                    tx._set_transaction_error("No existe la transaccion")
            else:
                raise UserError(response.content)
        return True

    def mp_qr_s2s_capture_transaction(self, **kwargs):
        acquirer_id = self.acquirer_id
        api_url = MP_URL + "merchant_orders/?external_reference=%s" % self.reference
        headers = {
            "Authorization": "Bearer %s" % acquirer_id.mp_access_token,
            "Content-Type": "application/json",
        }

        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            self.amount = data["elements"][0]["total_amount"]
            order = data["elements"][0]
            if order["status"] == "pending" and self.state != "pending":
                self._set_transaction_pending()
            if (
                order["status"] in ["opened", "authorized"]
                and self.state != "authorized"
            ):
                self._set_transaction_authorized()
            if order["status"] == "cancel" and self.state != "cancel":
                self._set_transaction_cancel()
            if order["status"] in ["approved", "closed"] and self.state != "done":
                self._set_transaction_done()

        else:
            _logger.error(response.content)

    def mp_qr_s2s_void_transaction(self, **kwargs):
        # TODO Solo si es la ultima
        if len(self.merchant_order_id):
            acquirer_id = self.acquirer_id
            user_id = acquirer_id.mp_get_user_id()
            api_url = MP_URL + "instore/qr/seller/collectors/%s/pos/%s" % (
                user_id,
                self.pos_external_id,
            )
            headers = {
                "Authorization": "Bearer %s" % acquirer_id.mp_access_token,
                "Content-Type": "application/json",
            }

            requests.delete(api_url, headers=headers)
        self.state = "cancel"

    """
    pending: El usuario no completó el proceso de pago todavía.
approved: El pago fue aprobado y acreditado.
authorized: El pago fue autorizado pero no capturado todavía.
in_process: El pago está en revisión.
in_mediation: El usuario inició una disputa.
rejected: El pago fue rechazado. El usuario podría reintentar el pago.
cancelled: El pago fue cancelado por una de las partes o el pago expiró.
refunded: El pago fue devuelto al usuario.
charged_back: Se ha realizado uncontracargo en la tarjeta de crédito del comprador.




    def _mp_qr_s2s_get_tx_status(self):"""
