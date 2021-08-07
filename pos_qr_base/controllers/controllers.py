# -*- coding: utf-8 -*-
# from odoo import http


# class PosQrBase(http.Controller):
#     @http.route('/pos_qr_base/pos_qr_base/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_qr_base/pos_qr_base/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_qr_base.listing', {
#             'root': '/pos_qr_base/pos_qr_base',
#             'objects': http.request.env['pos_qr_base.pos_qr_base'].search([]),
#         })

#     @http.route('/pos_qr_base/pos_qr_base/objects/<model("pos_qr_base.pos_qr_base"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_qr_base.object', {
#             'object': obj
#         })
