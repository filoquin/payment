# -*- coding: utf-8 -*-
# from odoo import http


# class MercadopagoQrPaymemnt(http.Controller):
#     @http.route('/mercadopago_qr_paymemnt/mercadopago_qr_paymemnt/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mercadopago_qr_paymemnt/mercadopago_qr_paymemnt/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mercadopago_qr_paymemnt.listing', {
#             'root': '/mercadopago_qr_paymemnt/mercadopago_qr_paymemnt',
#             'objects': http.request.env['mercadopago_qr_paymemnt.mercadopago_qr_paymemnt'].search([]),
#         })

#     @http.route('/mercadopago_qr_paymemnt/mercadopago_qr_paymemnt/objects/<model("mercadopago_qr_paymemnt.mercadopago_qr_paymemnt"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mercadopago_qr_paymemnt.object', {
#             'object': obj
#         })
