import logging
import requests
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


REQUEST_TIMEOUT = 10
MERCADO_PAGO_API_ENDPOINT = "https://api.mercadopago.com"


class MercadoPagoRequest:
    def __init__(self, mp_bearer_token):
        self.mercado_pago_bearer_token = mp_bearer_token

    def call_mercado_pago(self, method, endpoint, payload, test_scope=False):
        """Make a request to Mercado Pago API.

        :param method: "GET", "POST", ...
        :param endpoint: The endpoint to be reached by the request.
        :param payload: The payload of the request.
        :return The JSON-formatted content of the response.
        """
        endpoint = MERCADO_PAGO_API_ENDPOINT + endpoint
        header = {"Authorization": f"Bearer {self.mercado_pago_bearer_token}"}
        if test_scope:
            header["x-test-scope"] = "sandbox"
        try:
            response = requests.request(
                method, endpoint, headers=header, json=payload, timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 204:
                return response.ok
            elif response.ok:
                return response.json()

        except requests.exceptions.RequestException as error:
            _logger.warning("Cannot connect with Mercado Pago. Error: %s", error)
            return {"errorMessage": str(error)}
        except ValueError as error:
            _logger.warning("Cannot decode response json. Error: %s", error)
            return {
                "errorMessage": f"Cannot decode Mercado Pago response. Error: {error}"
            }
        raise UserError(response.text)
