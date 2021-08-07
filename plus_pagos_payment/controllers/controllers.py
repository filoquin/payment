# -*- coding: utf-8 -*-
# from odoo import http


# class PlusPagosPayment(http.Controller):
#     @http.route('/plus_pagos_payment/plus_pagos_payment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/plus_pagos_payment/plus_pagos_payment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('plus_pagos_payment.listing', {
#             'root': '/plus_pagos_payment/plus_pagos_payment',
#             'objects': http.request.env['plus_pagos_payment.plus_pagos_payment'].search([]),
#         })

#     @http.route('/plus_pagos_payment/plus_pagos_payment/objects/<model("plus_pagos_payment.plus_pagos_payment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('plus_pagos_payment.object', {
#             'object': obj
#         })
