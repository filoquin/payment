from odoo import fields, models
from odoo.addons.payment_decidir_v2.models.account_card import DECIDIR_METHODS
from datetime import datetime
import requests
import json

import logging
_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    sps_payment_method = fields.Selection(
        DECIDIR_METHODS, string='Decidir payment method')

    sps_payment_instalment = fields.Integer(
        string='Decidir instalment'
    )

    sps_ticket = fields.Char(
        string='ticket',
    )
    sps_card_authorization_code = fields.Char(
        string='card_authorization_code',
    )
    sps_address_validation_code = fields.Char(
        string='address_validation_code',
    )

    def payment_decidir_send_payment(self, token, card_bin):
        self.reference = "TX%s-%s" % (self.id,
                                      datetime.now().strftime('%y%m%d_%H%M%S'))
        payload = {
            #'id': self.env.user.display_name,
            'site_transaction_id': self.reference[:40],
            'token': token,
            'payment_method_id': int(self.sps_payment_method),
            'bin': card_bin,
            'amount': int(self.amount * 100) + int(self.fees * 100),
            'currency': 'ARS',
            'installments': self.sps_payment_instalment,
            'payment_type': 'single',
            'establishment_name': self.env.user.company_id.name,
            'email': self.partner_id.email,
            'sub_payments': [],

        }
        _logger.info(payload)
        payload = json.dumps(payload, indent=None)
        api_url = self.acquirer_id.decidir_get_base_url() + '/payments'

        headers = {
            'apikey': self.acquirer_id.decidir_secret_key,
            'content-type': "application/json",
            'cache-control': "no-cache"
        }

        response = requests.post(api_url, data=payload, headers=headers)
        if response.status_code == 200:
            return response.json()

        else:
            return response.json()
