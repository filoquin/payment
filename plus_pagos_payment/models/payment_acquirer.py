from odoo import fields, models, _
from odoo.exceptions import UserError
import requests
from datetime import datetime,  timedelta
import logging
_logger = logging.getLogger(__name__)



TEST_PLUSPAGOS_URL = "https://sandboxpp.asjservicios.com.ar:8082/v1/"
PROD_PLUSPAGOS_URL = "https://botonpp.asjservicios.com.ar:8082/v1/"


class PaymentAcquirer(models.Model):

    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[('plus_pagos', 'plus pagos')])

    pp_frase = fields.Char(
        string='Plus pagos frase',
    )

    pp_guid = fields.Char(
        string='Plus Pagos guid',
    )

    pp_token = fields.Text(
        string='Plus pagos token',
    )

    pp_secretkey = fields.Char(
        string='Plus Pagos secret key',
    )

    pp_token_expires = fields.Datetime(
        string='Plus Pagos token expires',
    )

    def pp_get_base_url(self):
        self.ensure_one()

        if self.state == 'test':
            return TEST_PLUSPAGOS_URL
        elif self.state == 'enabled':
            return PROD_PLUSPAGOS_URL
        else:
            raise UserError(_("PLUS PAGOS is disabled"))

    def pp_get_token(self):
        self.ensure_one()

        if self.pp_token and fields.Datetime.from_string(self.pp_token_expires) > datetime.now():
            return self.siro_token
        else:
            api_url = self.pp_get_base_url() + "sesion"

            request_data = {
                "frase": self.pp_frase,
                "guid": self.pp_guid
            }
            _logger.info(request_data)
            _logger.info(api_url)
            response = requests.post(api_url, json=request_data)
            _logger.info(response.content)
            _logger.info(response.status_code)
            if response.status_code == 200: 
                res = response.json()
                self.pp_secretkey = res['secretkey']
                self.pp_token = res['data']
                self.pp_token_expires = datetime.now(
                ) + timedelta(seconds=3600)
                return res['access_token']
            else:
                raise UserError(_("Plus pagos can't login"))

    def pp_add_cashbox(self, code, name, store, fixed_amount=True):

        access_token = self.pp_get_token()
        api_url = self.pp_get_base_url() + "caja"

        headers = {"Authorization": "Bearer %s" % access_token}
        request_data = {
            'Nombre': name,
            'Codigo': code,
            'NumeroSucursal': store,
            'Fixed_amount': fixed_amount,
        }
        response = requests.post(
            api_url, headers=headers, json=request_data)

        if response.status_code == 201:
            return response.json()['data']

        else:
            raise UserError(response.json()["message"])

    def pp_unlink_cashbox(self, code):

        access_token = self.pp_get_token()
        api_url = self.pp_get_base_url() + "caja?codigo=%s" % code
        headers = {"Authorization": "Bearer %s" % access_token}
        response = requests.delete(api_url, headers=headers)

        if response.status_code == 200:
            return True
        else:
            return False

    def pp_get_cashbox(self, code):

        access_token = self.pp_get_token()
        api_url = self.pp_get_base_url() + "caja?codigo=%s" % code
        headers = {"Authorization": "Bearer %s" % access_token}
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            return response.json()['data']
        else:
            return False

    def pp_create_order(self, cashbox_code, amount, reference, name, url='', timeout=120):

        access_token = self.pp_get_token()
        api_url = self.pp_get_base_url() + "order/%s" % cashbox_code

        headers = {"Authorization": "Bearer %s" % access_token, 'X-Ttl-Preference:': timeout}
        request_data = {
            'MontoTotal': str(int(amount * 10)),
            'IdTransaccionInterno': reference,
            'Productos': name,
            'UrlNotificacion': url,
        }
        response = requests.post(
            api_url, headers=headers, json=request_data)

        if response.status_code == 201:
            return response.json()['data']

        else:
            raise UserError(response.json()["message"])
