from odoo import api, fields, models, tools, _


import logging
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def create_from_ui(self, orders, draft=False):

        _logger.info(orders)
        return super().create_from_ui(orders, draft) 

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        payment = super()._payment_fields(order, ui_paymentline)
        payment['instalment_id'] = ui_paymentline.get('instalment_id', False)
        payment['card_number'] = ui_paymentline.get('card_number', False)
        payment['tiket_number'] = ui_paymentline.get('tiket_number', False)
        payment['lot_number'] = ui_paymentline.get('lot_number', False)
        payment['fee'] = ui_paymentline.get('fee', False)

        return payment
