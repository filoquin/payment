from odoo import fields, models, _
from odoo.exceptions import UserError
import requests
from datetime import datetime,  timedelta
import logging
_logger = logging.getLogger(__name__)


MP_URL = "https://api.mercadopago.com/"


class PaymentAcquirer(models.Model):

    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[('mp_qr', 'QR Mercado Pago')])

    mp_public_key = fields.Char(
        string='Public Key',
    )

    mp_access_token = fields.Char(
        string='Access Token',
    )
    store_ids = fields.One2many(
        'mp.store',
        'acquirer_id',
        string='Stores',
    )

    def mp_get_user_id(self):
        self.ensure_one()
        return self.mp_access_token.split('-')[-1]

    def action_mp_create_stores(self):
        user_id = self.mp_get_user_id()
        api_url = MP_URL + "users/%s/stores" % user_id
        headers = {"Authorization": "Bearer %s" % self.mp_access_token}
        store_ids = self.store_ids.filtered(lambda s: s.state == 'draft')
        _logger.info(api_url)
        _logger.info(headers)
        for store_id in store_ids:
            request_data = store_id.prepare_request_data()
            _logger.info(request_data)
            response = requests.post(api_url, headers=headers, json=request_data)
            _logger.info(response.content)
            if response.status_code == 200:
                res = response.json()
                store_id.state = 'active'
                store_id.mp_id = res.id

    def action_mp_unlink_store(self, mp_id):
        user_id = self.mp_get_user_id()
        api_url = MP_URL + "users/%s/stores" % user_id
        headers = {"Authorization": "Bearer %s" % self.mp_access_token}
        store_id = self.store_ids.filtered(lambda s: s.state == 'active' and s.mp_id == mp_id)
        request_data = {'id': mp_id}
        response = requests.delete(api_url, headers=headers, data=request_data)
        if response.status_code == 200:
            store_id.state = 'drop'

    def action_mp_update_store(self, mp_id):
        user_id = self.mp_get_user_id()
        api_url = MP_URL + "users/%s/stores" % user_id
        headers = {"Authorization": "Bearer %s" % self.mp_access_token}
        store_id = self.store_ids.filtered(lambda s: s.state == 'active' and s.mp_id == mp_id)
        request_data = store_id.prepare_request_data()
        response = requests.put(api_url, headers=headers, data=request_data)
        if response.status_code == 200:
            store_id.state = 'active'
