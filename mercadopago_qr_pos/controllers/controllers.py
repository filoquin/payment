# -*- coding: utf-8 -*-
# from odoo import http


# class MercadopagoQrPos(http.Controller):
#     @http.route('/mercadopago_qr_pos/mercadopago_qr_pos/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mercadopago_qr_pos/mercadopago_qr_pos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mercadopago_qr_pos.listing', {
#             'root': '/mercadopago_qr_pos/mercadopago_qr_pos',
#             'objects': http.request.env['mercadopago_qr_pos.mercadopago_qr_pos'].search([]),
#         })

#     @http.route('/mercadopago_qr_pos/mercadopago_qr_pos/objects/<model("mercadopago_qr_pos.mercadopago_qr_pos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mercadopago_qr_pos.object', {
#             'object': obj
#         })
