from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class MercadopagoQrPaymemnt(http.Controller):
    @http.route("/mercadopago_qr_payment/ipn", auth="public", type="json")
    def ipn(self, **kw):
        params = request.httprequest.full_path.split("?")[1].split("&")
        data = {}
        # TODO esto es feo pero por ahora resuelvo asi
        # el problema envian variables por GET
        # mediante un POST de JSON
        for p in params:
            i = p.split("=")
            data[i[0]] = i[1]
        request.env["payment.transaction"].sudo()._handle_notification_data(
            "mercado_pago_qr", data
        )
        return ""
