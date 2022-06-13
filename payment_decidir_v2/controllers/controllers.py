# -*- coding: utf-8 -*-
from odoo import http

from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class PaymentDecidir(http.Controller):
    @http.route(
        ["/shop/cart/decidirv2_endop", "/shop/cart/decidirv2_endop/<string:ref>"],
        auth="public",
        website=True,
        csrf=False,
    )
    def decidirv2_endop(
        self,
        ref="",
        order_id=None,
        invoice_id=None,
        method=None,
        access_token=None,
        **kw
    ):
        transaction = (
            request.env["payment.transaction"]
            .sudo()
            .search(
                [
                    ("reference", "=", ref),
                ]
            )
        )
        values = {"transaction": transaction}
        if order_id:
            values["order"] = request.env["sale.order"].sudo().browse(order_id)
        if invoice_id:
            values["invoice"] = request.env["sale.order"].sudo().browse(order_id)
        return request.render("payment_decidir_v2.endop", values)

    @http.route(
        ["/shop/cart/decidirv2_make_payment"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def decidirv2_make_payment(self, acquirer_id, token, **kwargs):

        acquirer_id = request.env["payment.acquirer"].sudo().browse(acquirer_id)

        if "base_amount" in kwargs and "decidir_order_id" in kwargs:
            order = (
                request.env["sale.order"].sudo().browse(int(kwargs["decidir_order_id"]))
            )
            total = float(kwargs["base_amount"])
        else:
            order = request.website.sale_get_order(force_create=1)
            if order.state != "draft":
                request.website.sale_reset()
                return {}
            total = order.amount_total

        instalment_id = kwargs.get("instalment_id", 0)
        instalment_id = (
            request.env["account.card.instalment"]
            .sudo()
            .search([("id", "=", instalment_id)], limit=1)
        )
        decidir_bin = kwargs.get("bin", False)

        fees = instalment_id.get_fees(total)

        payment = acquirer_id.payment_decidir_create_payment(
            order, token, total, fees, instalment_id, decidir_bin
        )
        return payment

    """
    Codigo obsoleto
    @http.route(['/shop/cart/decidirv2_form'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def decidirv2_form(self, instalment_id, acquirer_id, amount=0):
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            return {}

        acquirer_id = request.env[
            'payment.acquirer'].sudo().browse(acquirer_id)
        instalment_id = request.env['account.card.instalment'].sudo().search(
            [('id', '=', instalment_id)], limit=1)
        fees = instalment_id.get_fees(order.amount_total)

        value = {}
        value['decidir_v2_form'] = request.env['ir.ui.view'].render_template(
            "payment_decidir_v2.decidir_v2_inline_form", {
                'website_sale_order': order,
                'instalment_id': instalment_id,
                'acquirer_id': acquirer_id,
                'amount': order.amount_total,
                'fees': fees,
            })
        return value

    @http.route(['/shop/cart/decidirv2_token_register'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def decidirv2_token_register(self, acquirer_id, instalment_id, token, end_string, **kwargs):

        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            return {}
        acquirer_id = request.env[
            'payment.acquirer'].sudo().browse(acquirer_id)
        acquirer_id = request.env[
            'payment.acquirer'].sudo().browse(acquirer_id)
        
        
        card_id = instalment_id.card_id
        token = acquirer_id.payment_decidir_make_token(card_id, end_string, order.partner_id, token)
        return token.id

        
    @http.route(['/shop/cart/back_instalment'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def back_instalment(self,  acquirer_id):

        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            return {}

        acquirer_id = request.env[
            'payment.acquirer'].sudo().browse(acquirer_id)
        value = {}
        value['decidir2_instalment_menu'] = request.env['ir.ui.view'].render_template(
            "payment_decidir_v2.decidir2_instalment_menu", {
                'order': order,
                'acq': acquirer_id,
            })
        return value
    """
