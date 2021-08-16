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
        for store_id in store_ids:
            request_data = store_id.prepare_request_data()
            response = requests.post(api_url, headers=headers, json=request_data)
            res = response.json()
            if response.status_code == 201:
                store_id.state = 'active'
                store_id.mp_id = int(res['id'])
            else: 
                raise UserError(res['message'])

    def action_mp_unlink_store(self, mp_id):
        user_id = self.mp_get_user_id()
        api_url = MP_URL + "users/%s/stores/%s" % (user_id, mp_id)
        headers = {"Authorization": "Bearer %s" % self.mp_access_token}
        response = requests.delete(api_url, headers=headers)
        if response.status_code == 200:
            return True
        else: 
            raise UserError(response.content)

    def action_mp_update_store(self, mp_id):
        user_id = self.mp_get_user_id()

        api_url = MP_URL + "users/%s/stores/%s" % (user_id, mp_id)
        _logger.info(api_url)
        headers = {"Authorization": "Bearer %s" % self.mp_access_token, "Content-Type": "application/json"}
        store_id = self.store_ids.filtered(lambda s:  s.mp_id == mp_id)
        request_data = store_id.prepare_request_data()
        response = requests.put(api_url, headers=headers, json=request_data)
        if response.status_code == 200:
            store_id.state = 'active'
        else: 
            raise UserError(response.content)

    def mp_register_pos(self, vals):
        api_url = MP_URL + "pos"
        headers = {"Authorization": "Bearer %s" % self.mp_access_token}
        request_data = {
              "name": vals['name'],
              "fixed_amount": vals['fixed_amount'],
              "store_id": vals['store_id'],
              "external_store_id": vals['external_store_id'],
              "external_id": vals['external_id'],
        }
        _logger.info(request_data)
        response = requests.post(api_url, headers=headers, json=request_data)
        res = response.json()

        if response.status_code == 201:
            return res
        else:
            raise UserError(response.content)

    def mp_update_pos(self, vals):
        api_url = MP_URL + "pos/%s" % vals['mp_id']
        headers = {"Authorization": "Bearer %s" % self.mp_access_token, "Content-Type": "application/json"}
        _logger.info(api_url)
        _logger.info(headers)

        request_data = {
              "name": vals['name'],
              "fixed_amount": vals['fixed_amount'],
              "store_id": vals['store_id'],
              "external_store_id": vals['external_store_id'],
              "external_id": vals['external_id'],
        }
        _logger.info(request_data)

        response = requests.put(api_url, headers=headers, json=request_data)
        _logger.info(response.content)
        
        if response.status_code == 201:
            res = response.json()
            return res
        else:
            raise UserError(response.content)

    def mp_qr_pos_transaction(self, data):
        if data['config_id']:
            data['store_external_id'] = data['config_id'].mp_store_id.mp_id
            data['pos_external_id'] = data['config_id'].mp_id
        user_id = self.mp_get_user_id()
        api_url = MP_URL + "instore/qr/seller/collectors/%s/stores/%s/pos/%s/orders" % (user_id, data['store_external_id'], data['pos_external_id'])
        headers = {"Authorization": "Bearer %s" % self.mp_access_token, "Content-Type": "application/json"}

        request_data = {
              "external_reference": data['reference'],
              "title": data['name'],
              #"notification_url": data['store_id'],
              "total_amount": data['amount'],
              "items": [],
        }

        _logger.info(request_data)

        response = requests.put(api_url, headers=headers, json=request_data)

        _logger.info(response)
