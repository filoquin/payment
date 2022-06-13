# -*- coding: utf-8 -*-
from odoo import http
from openerp.http import request
import logging

_logger = logging.getLogger(__name__)


class MercadopagoQrPaymemnt(http.Controller):
    @http.route("/mercadopago_qr_payment/ipn/<int:aquirer>", auth="public", type="json")
    def ipn(self, aquirer, **kw):
        params = request.httprequest.full_path.split("?")[1].split("&")
        mp = {"acquirer_id": aquirer}
        # TODO esto es feo pero por ahora resuelvo asi
        # el problema envian variables por GET
        # mediante un POST de JSON
        for p in params:
            i = p.split("=")
            mp[i[0]] = i[1]

        request.env["payment.transaction"].sudo().mp_qr_process_ipn(mp)

        return ""
