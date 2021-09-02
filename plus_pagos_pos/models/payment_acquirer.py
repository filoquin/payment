from odoo import fields, models, _
from odoo.exceptions import UserError
import requests
from datetime import datetime,  timedelta
import logging
_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):

    _inherit = 'payment.acquirer'

    def plus_pagos_pos_transaction(self, data):
        if data['configId']:
            config_id = self.env['pos.config'].browse(data['configId'])

            return self.pp_create_order(config_id.cashbox_code, data['amount'], data['reference'], data['reference'])

    def plus_pagos_pos_transaction_check(self, data):
        if 'transaction_id' in data:
            tx = self.env['payment.transaction'].sudo().browse(data['transaction_id'])
            return {
                'state': tx.state,
                'transaction_id': tx.id,
                'reference': tx.reference,
                'amount': tx.amount,
            }            
        return {} 