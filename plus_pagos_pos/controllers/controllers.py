# -*- coding: utf-8 -*-
# from odoo import http


# class PlusPagosPos(http.Controller):
#     @http.route('/plus_pagos_pos/plus_pagos_pos/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/plus_pagos_pos/plus_pagos_pos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('plus_pagos_pos.listing', {
#             'root': '/plus_pagos_pos/plus_pagos_pos',
#             'objects': http.request.env['plus_pagos_pos.plus_pagos_pos'].search([]),
#         })

#     @http.route('/plus_pagos_pos/plus_pagos_pos/objects/<model("plus_pagos_pos.plus_pagos_pos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('plus_pagos_pos.object', {
#             'object': obj
#         })
