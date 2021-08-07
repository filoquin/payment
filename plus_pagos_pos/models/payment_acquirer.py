from odoo import fields, models, _
from odoo.exceptions import UserError
import requests
from datetime import datetime,  timedelta
import logging
_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):

    _inherit = 'payment.acquirer'

    def plus_pagos_get_qr_image(self, data):
        return 'xzxx'
        #self.pp_create_order(self, cashbox_code, amount, reference, name, url='', timeout=120):
