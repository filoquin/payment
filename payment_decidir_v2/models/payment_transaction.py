from odoo import fields, models
from odoo.addons.payment_decidir_v2.models.account_card import DECIDIR_METHODS
from odoo.exceptions import UserError

from datetime import datetime
import requests
import json

import logging
_logger = logging.getLogger(__name__)


class PaymentTransactionParcialRefund(models.TransientModel):
    _name = 'payment.transaction.parcial.refund'
    _description = 'decidir parcial refund'

    payment_id = fields.Many2one(
        'payment.transaction',
        string='Payment',
        domain=[('state', '=', 'done'),
                ('acquirer_id.provider', '=', 'decidir_v2')],
        required=True
    )
    amount = fields.Float(
        string='Amount',
        required=True
    )

    def action_refund(self):
        self.payment_id.decidir_refunds_partial_payment(self.amount)

class PaymentTransactionSpsRefund(models.Model):
    _name = 'payment.transaction.decidir.refund'
    _description = 'decidir refund'

    payment_id = fields.Many2one(
        'payment.transaction',
        string='Payment',
        required=True
    )
    amount = fields.Float(
        string='Amount',
        required=True
    )
    sps_payment_id = fields.Integer(
        string='Decidir id',
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


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    sps_payment_id = fields.Integer(
        string='Decidir id',
    )
    sps_payment_refund_id = fields.Integer(
        string='Decidir refund id',
    )
    sps_refund_ids = fields.One2many(
        'payment.transaction.decidir.refund',
        'payment_id',
        string='refund',
    )

    """sps_refund_ids = fields.Many2many(
        comodel_name='payment.transaction',
        relation='sps_refund',
        column1='parent',
        column2='chils',
        string='Refund op',
    )"""
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

    def set_decidir_data(self, sps_send):
        self.ensure_one()
        if 'id' in sps_send:
            self.sps_payment_id = sps_send['id']
        if 'status_details' in sps_send:
            self.sps_ticket = sps_send['status_details']['ticket']
            self.sps_card_authorization_code = sps_send['status_details']['card_authorization_code']
            self.sps_address_validation_code = sps_send['status_details']['address_validation_code']

    def decidir_get_payment_info(self):
        rtn_txt = ''
        for transaction in self.filtered(lambda t: t.acquirer_id.provider == 'decidir_v2'):
            if transaction.sps_payment_id:
                transaction_info = transaction.acquirer_id.decidir_get_payment_info(
                    transaction.sps_payment_id)
            elif transaction.reference:
                transaction_info = transaction.acquirer_id.decidir_get_payments(
                    siteOperationId=transaction.reference)
                transaction_info = transaction_info['results'][0]

            if 'only_show_data' in self.env.context:
                for item in transaction_info:
                    rtn_txt += "%s: %s\n" % (item, transaction_info[item])
            else:
                transaction.set_decidir_data(transaction_info)
                if transaction_info['status'] == 'annulled' \
                   and transaction.state in ['draft', 'authorized', 'done']:
                    transaction.mapped('payment_id').cancel()
                    transaction.write(
                        {'state': 'cancel', 'date': fields.Datetime.now()})
                    transaction._log_payment_transaction_received()

        if 'only_show_data' in self.env.context:
            raise UserError(rtn_txt)

    def action_open_refund(self):
        view_id = self.env.ref('payment_decidir_v2.parcial_refund_form')
        view = {
            'name': "Refund",
            'view_mode': 'form',
            'view_id': view_id.id,
            'view_type': 'form',
            'res_model': 'payment.transaction.parcial.refund',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_payment_id': self.id}
        }
        return view

    def decidir_refunds_partial_payment(self, amount):
        for transaction in self:
            transaction_info = transaction.acquirer_id.decidir_refund_payment(
                transaction.sps_payment_id, amount)
            _logger.info(transaction_info)
            # {"id":442203,"amount":1000,"sub_payments":null,"error":null,"status":"approved","status_details":{"ticket":"3786","card_authorization_code":"234126","address_validation_code":"VTE0011","error":null}}

            new_transation = {
                'payment_id': transaction.id,
                'sps_payment_id': transaction_info['id'],
                'sps_ticket': transaction_info['status_details']['ticket'],
                'amount': transaction_info['amount'] / 100 * -1,
                'sps_card_authorization_code': transaction_info['status_details']['card_authorization_code'],
                'sps_address_validation_code': transaction_info['status_details']['address_validation_code']
            }
            self.env['payment.transaction.decidir.refund'].create(new_transation)
            transaction.payment_id.action_draft()
            refund_amount = sum(transaction.mapped('sps_refund_ids.amount'))
            transaction.payment_id.amount = transaction.amount + transaction.fees + refund_amount
            transaction.payment_id.post()

    def decidir_cancel_refund(self):
        for transaction in self:
            if transaction.state == 'cancel' and transaction.sps_payment_refund_id:
                transaction_info = transaction.acquirer_id.decidir_refund_payment(
                    transaction.sps_payment_id, transaction.sps_payment_refund_id)
                if transaction_info:
                    transaction.state = 'done'
                    if transaction.payment_id:
                        transaction.payment_id.action_draft()
                        transaction.payment_id.post()
                    else:
                        transaction._post_process_after_done()

    # devolucion total de un pago
    def decidir_refunds_total_payment(self):
        for transaction in self:
            transaction_info = transaction.acquirer_id.decidir_refund_payment(
                transaction.sps_payment_id)
            if not transaction_info['error']:
                transaction.mapped('payment_id').cancel()
                transaction.write({
                    'sps_payment_refund_id': transaction_info['id'],
                    'state': 'cancel',
                    'date': fields.Datetime.now()}
                )
                transaction._log_payment_transaction_received()

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
            #'establishment_name': self.env.user.company_id.name,
            #'email': self.partner_id.email,
            'sub_payments': [],

        }
        payload = json.dumps(payload, indent=None)
        api_url = self.acquirer_id.decidir_get_base_url() + '/payments'

        headers = self.acquirer_id.decidir_get_headers()
        print (payload)
        response = requests.post(api_url, data=payload, headers=headers)
        if response.status_code == 200:
            return response.json()

        else:
            return response.json()

    def _prepare_account_payment_vals(self):
        vals = super()._prepare_account_payment_vals()
        if vals['amount'] < 0:
            vals['amount'] = vals['amount'] * -1
        return vals
