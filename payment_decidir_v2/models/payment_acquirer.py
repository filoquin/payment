from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.addons.payment_decidir_v2.models.account_card import DECIDIR_METHODS
import logging
import requests

_logger = logging.getLogger(__name__)

PROD_BASE_API_URL = 'https://live.decidir.com/api/v2'
TEST_BASE_API_URL = 'https://developers.decidir.com/api/v2'


DECIDIR_URL = 'https://sps.decidir.com/sps-ar/Validar'


class PaymentAcquirer(models.Model):

    _inherit = "payment.acquirer"

    provider = fields.Selection(
        selection_add=[('decidir_v2', 'Decidir 2.0')],
    )

    card_ids = fields.Many2many(
        'account.card',
        string='Card',
    )
    instalment_ids = fields.Many2many(
        'account.card.instalment',
        string='Instalment',
    )
    decidir_commerce = fields.Char(
        string='N. commerce',
    )
    decidir_public_key = fields.Char(
        string='Public Api Key',
    )
    decidir_secret_key = fields.Char(
        string='Api Key',
    )
    device_unique_identifier = fields.Char(
        string='device unique identifier',
    )

    def decidir_get_base_url(self):
        self.ensure_one()

        if self.state == 'prod':
            return PROD_BASE_API_URL
        elif self.state == 'test':
            return TEST_BASE_API_URL
        else:
            raise UserError(_("Decidir is disabled"))

    def decidir_healthcheck(self):
        api_url = self. decidir_get_base_url() + 'healthcheck'
        response = requests.get(api_url, data={})
        if response.status_code == 200:
            res = response.json()
            # to do oki?
        else:
            raise UserError(_("Decidir healthcheck error"))

    def payment_decidir_make_token(self, card_id, end_string, partner_id, add_token, bin):
        token = {
            'name': "%s terminada en %s" % (card_id.name, end_string),
            'card_id': card_id.id,
            'partner_id': partner_id.id,
            'acquirer_id': self.id,
            'acquirer_ref': add_token,
            'decidir_bin': bin,
            'active': True,
        }
        return self.env['payment.token'].create(token)

    def payment_decidir_create_payment(self, order, token, amount, fees,  instalment, card_bin):
        values = {
            'amount': amount,
            'fees': fees,
            'acquirer_id': self.id,
            'type': 'server2server',
            'currency_id': self.env.ref('base.ARS').id,
            'reference': 'draft',
            'partner_id': order.partner_id.id,
            'partner_country_id': order.partner_id.country_id.id,
            'sps_payment_instalment': instalment.instalment,
            'sps_payment_method': instalment.card_id.decidir_method
            #'invoice_ids': [(6, 0, [self.id])],
            #'callback_model_id': self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1).id,
            #'callback_res_id': self.id,
            #'callback_method': 'reconcile_pending_transaction' if off_session else '_reconcile_and_send_mail',
            #'return_url': '/my/invoices/%s' % (self.id),
        }
        _logger.info(values)
        tx = self.env['payment.transaction'].sudo().create(values)
        sps_send = tx.payment_decidir_send_payment(token, card_bin)
        _logger.info(sps_send)
        if 'validation_errors' in sps_send and sps_send['validation_errors']:
            errors = [x['code'] for x in sps_send['validation_errors']]
            raise UserError('<br/>'.join(errors))

        if sps_send['status'] == "approved":
            if fees and order:
                order.add_fee_line(fees, instalment)
            tx._set_transaction_done()
            tx._post_process_after_done()
            tx.sps_ticket = sps_send['status_details']['ticket']
            tx.sps_card_authorization_code = sps_send['status_details']['card_authorization_code']
            tx.sps_address_validation_code = sps_send['status_details']['address_validation_code']

            order.with_context(send_email=True).action_confirm()
            portal_url = order.get_portal_url()
            return {'state': 'ok', 'tx': tx.id, 'portal_url': portal_url}
        elif sps_send['status'] == "Preapporved":
            if fees and order:
                order.add_fee_line(fees, instalment)

            order.with_context(send_email=True).action_confirm()
            portal_url = order.get_portal_url()
            tx._set_transaction_pending()
            return {'state': 'pending', 'tx': tx.id, 'portal_url': portal_url}
        elif sps_send['status'] == "Review":
            if fees and order:
                order.add_fee_line(fees, instalment)

            order.with_context(send_email=True).action_confirm()
            portal_url = order.get_portal_url()
            tx._set_transaction_pending()
            return {'state': 'pending', 'tx': tx.id, 'portal_url': portal_url}
        elif sps_send['status'] == "Rejected":
            return {'state': 'error', 'tx': tx.id}
            tx._set_transaction_error()

    def decidir2_instalment_tree(self, order=False, order_id=False, amount_total=0):

        self.ensure_one()
        if order: 
            amount_total = order.amount_total
        elif order_id: 
            if not amount_total:
                amount_total = self.env['sale.order'].sudo().browse(order_id).amount_total

        # to-do  los instaments debeen venir desde el payment (self)
        instalment_ids = self.env['account.card.instalment'].sudo().search(
            [('website_enabled', '=', True)]
        )

        cards = {}
        for card in instalment_ids.mapped('card_id'):
            cards[card.id] = {'name': card.name,
                              'id': card.id,  'instalments': []}

        tree = {}
        if amount_total:
            for instalment in instalment_ids:
                if instalment.card_id.id not in tree:
                    tree[instalment.card_id.id] = cards[
                        instalment.card_id.id]
                discount = (100 - instalment.discount) / 100
                amount = amount_total * instalment.coefficient * discount
                ins = {
                    'id': instalment.id,
                    'name': instalment.name,
                    'instalment': instalment.instalment,
                    'coefficient': instalment.coefficient,
                    'discount': instalment.discount,
                    'bank_discount': instalment.bank_discount,
                    'ctf': instalment.ctf,
                    'tea': instalment.tea,
                    'base_amount': amount_total,
                    'amount': amount, 
                    'fee': amount - amount_total,
                    'method': instalment.card_id.decidir_method
                }
                tree[instalment.card_id.id]['instalments'].append(ins)

        return tree


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    card_id = fields.Many2one(
        'account.card',
        string='Card',
    )

    sps_payment_method = fields.Selection(
        DECIDIR_METHODS,
        string='Decidir payment method',
        related='card_id.decidir_method'
    )
    decidir_bin = fields.Char(
        string='Bin',
    )
