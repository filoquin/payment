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
    mp_qr_title = fields.Char(
        string='Order title',
        default='My MP Odoo Order'
    )
    mp_qr_description = fields.Char(
        string='Order description',
        default='My MP Odoo Order'
    )
    mp_default_partner_id = fields.Many2one(
        'res.partner',
        string='Default partner',
    )

    def _get_feature_support(self):
        feature_support = super()._get_feature_support()
        feature_support['authorize'].append('mp_qr')
        return feature_support

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
            response = requests.post(
                api_url, headers=headers, json=request_data)
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
        headers = {"Authorization": "Bearer %s" %
                   self.mp_access_token, "Content-Type": "application/json"}
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
        response = requests.post(api_url, headers=headers, json=request_data)
        res = response.json()

        if response.status_code == 201:
            return res
        else:
            raise UserError(response.content)

    def mp_update_pos(self, vals):
        api_url = MP_URL + "pos/%s" % vals['mp_id']
        del vals['mp_id']
        headers = {"Authorization": "Bearer %s" %
                   self.mp_access_token, "Content-Type": "application/json"}
        request_data = vals
        response = requests.put(api_url, headers=headers, json=request_data)

        if response.status_code == 200:
            res = response.json()
            return res
        else:
            raise UserError(response.content)

    def create_order(self, data):
        values = self.qr_prepare_transaction(data)
        tx_obj = self.env['payment.transaction']
        tx = tx_obj.sudo().create(values)
        tx.sudo().s2s_do_transaction()
        return True
    
    def xcreate_order(self, data):

        user_id = self.mp_get_user_id()
        api_url = MP_URL + "instore/qr/seller/collectors/%s/stores/%s/pos/%s/orders" % (
            user_id, data['store_external_id'], data['pos_external_id'])
        headers = {"Authorization": "Bearer %s" %
                   self.mp_access_token, "Content-Type": "application/json"}

        base_url = self.get_base_url()
        base_url = "https://hormigag.ar/"
        base_url = "http://181.171.155.178:8013/"

        external_reference = "%s-%s-%s" % (data['pos_external_id'], data[
                                           'reference'], fields.Datetime.now())
        request_data = {
            "external_reference": external_reference,
            "title": data['name'],
            "description": "Odoo QR",
            "notification_url":  base_url + 'mercadopago_qr_payment/ipn',
            "total_amount": data['amount'],
            "items": [
                {
                    "sku_number": "odoo",
                    "category": "general",
                    "title": "Pos sale",
                    "description": "odoo sale",
                    "unit_price": data['amount'],
                    "quantity": 1,
                    "unit_measure": "unit",
                    "total_amount": data['amount'],
                }
            ],
        }
        _logger.info(request_data)

        response = requests.put(api_url, headers=headers, json=request_data)
        if response.status_code == 204:
            return True
        else:
            raise UserError(response.content)

    def mp_qr_pos_transaction_check(self, external_reference):

        api_url = MP_URL + \
            "merchant_orders?external_reference=%s" % (
                external_reference)
        api_url = MP_URL + \
            "merchant_orders"

        headers = {"Authorization": "Bearer %s" % self.mp_access_token}
        response = requests.get(api_url, headers=headers)
        _logger.info(response.status_code)
        _logger.info(response.content)
        if response.status_code == 200:
            return True
        else:
            raise UserError(response.content)

        _logger.info(api_url)

        return True

    def qr_prepare_transaction(self, data):
        external_reference = "%s-%s-%s" % (data['pos_external_id'], data[
                                           'reference'], fields.Datetime.now())
        if 'partner_id' in data:
            partner_id = self.env['res.partner'].browse(data['partner_id'])
        else:
            partner_id = self.mp_default_partner_id

        values = {
            'amount': data['amount'],
            'acquirer_id': self.id,
            'type': 'server2server',
            'currency_id': self.env.user.company_id.currency_id.id,
            'reference': external_reference,
            'partner_id': partner_id.id,
            'partner_country_id': partner_id.country_id.id,
            'store_external_id': str(data['store_external_id']),
            'pos_external_id': str(data['pos_external_id']),
        }
        return values


class PaymentTransaction(models.Model):

    _inherit = 'payment.transaction'

    merchant_order_id = fields.Integer(
        string='merchant order',
    )
    store_external_id = fields.Char(
        string='store',
    )
    pos_external_id = fields.Char(
        string='pos',
    )

    def mp_qr_s2s_do_transaction(self, **kwargs):

        acquirer_id = self.acquirer_id
        user_id = acquirer_id.mp_get_user_id()

        api_url = MP_URL + "instore/qr/seller/collectors/%s/stores/%s/pos/%s/orders" % (
            user_id, self.store_external_id, self.pos_external_id)

        headers = {"Authorization": "Bearer %s" %
                   acquirer_id.mp_access_token, "Content-Type": "application/json"}

        base_url = acquirer_id.get_base_url()
        base_url = "https://hormigag.ar/"
        base_url = "http://181.171.155.178:8013/"

        request_data = {
            "external_reference": self.reference,
            "title": acquirer_id.mp_qr_title,
            "description": acquirer_id.mp_qr_description,
            "notification_url":  base_url + 'mercadopago_qr_payment/ipn',
            "total_amount": self.amount,
            "items": [
                {
                    "sku_number": "odoo",
                    "category": "general",
                    "title": "Pos sale",
                    "description": "odoo sale",
                    "unit_price": self.amount,
                    "quantity": 1,
                    "unit_measure": "unit",
                    "total_amount": self.amount,
                }
            ],
        }
        _logger.info(request_data)
        _logger.info(api_url)
        response = requests.put(api_url, headers=headers, json=request_data)

        _logger.info(response.status_code)
        if response.status_code == 204:
            self._set_transaction_pending()

            return True
        else:
            raise UserError(response.content)

    def mp_qr_process_ipn(self, kwargs):
        acquirer_id = self.env['payment.acquirer'].search([('provider', '=', 'mp_qr')], limit=1)
        _logger.info(kwargs)

        if kwargs['topic'] == 'merchant_order':
            api_url = MP_URL + "merchant_orders/%s" % kwargs['id']
            headers = {"Authorization": "Bearer %s" %
                       acquirer_id.mp_access_token, "Content-Type": "application/json"}

            response = requests.get(api_url, headers=headers)
            _logger.info(response.content)
            _logger.info(response.status_code)

            if response.status_code == 200:
                data = response.json()
                _logger.info(data)
                if data['status'] == 'opened':
                    tx = self.search([
                        ('reference', '=', data['external_reference']),
                        #('acquirer_id.provider', '=', 'mp_qr')
                    ])
                    if len(tx):
                        _logger.info(tx)

                        tx.merchant_order_id = str(kwargs['id'])
                        tx._set_transaction_authorized()
            else:
                _logger.error(response.content)

    def mp_qr_s2s_capture_transaction(self, kwargs):
        acquirer_id = self.acquirer_id

        api_url = MP_URL + "merchant_orders/search/?external_reference=%s" % self.reference
        headers = {"Authorization": "Bearer %s" %
                   acquirer_id.mp_access_token, "Content-Type": "application/json"}

        response = requests.get(api_url, headers=headers)
        if response.status_code == 200: 
            data = response.json()
            order = data['elements'][0]
            if order['status'] == 'pending' and self.status != 'pending':
                self._set_transaction_pending()
            if order['status'] in ['opened', 'authorized'] and self.status != 'authorized':
                self._set_transaction_authorized()
            if order['status'] == 'cancel' and self.status != 'cancel':
                self._set_transaction_cancel()
            if order['status'] == 'approved' and self.status != 'done':
                self._set_transaction_done()

        else:
            _logger.error(response.content)

    """
    pending: El usuario no completó el proceso de pago todavía.
approved: El pago fue aprobado y acreditado.
authorized: El pago fue autorizado pero no capturado todavía.
in_process: El pago está en revisión.
in_mediation: El usuario inició una disputa.
rejected: El pago fue rechazado. El usuario podría reintentar el pago.
cancelled: El pago fue cancelado por una de las partes o el pago expiró.
refunded: El pago fue devuelto al usuario.
charged_back: Se ha realizado uncontracargo en la tarjeta de crédito del comprador.



    def mp_qr_s2s_void_transaction(self, **kwargs):

    def _mp_qr_s2s_get_tx_status(self):"""
