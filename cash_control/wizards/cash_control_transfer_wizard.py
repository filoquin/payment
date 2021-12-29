# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
from datetime import datetime


class CashControlTransferWizard(models.TransientModel):
    _name = 'cash.control.transfer.wizard'
    _description = 'Cash Control Transfer Wizard'

    orig_journal_id = fields.Many2one(
        'account.journal',
        string='Origin journal',
        domain=[('type', '=', 'cash')],
        required=True,
    )
    dest_cash_control_id = fields.Many2one(
        'cash.control.config',
        string='Dest journal',
        #domain=[('session_state', '=', 'opened'), ],
        required=False,
    )
    amount = fields.Float(
        string='Amount',
        required=True,
        digits=dp.get_precision('adela dp')

    )
    is_acum_cash_control = fields.Boolean(
        'Es Caja Acumuladora'
    )
    operation = fields.Selection(
        [
         ('transfer_to_cash', 'Transferencia a Caja'),
         ('transfer_to_bank', 'Transferencia a Banco'),
        ],
        default="transfer_to_cash",
        string="Operación"
    )
    bank_journal_id = fields.Many2one(
        'account.journal',
        string='Transferir a',
        domain=[('type', '=', 'bank')],
        required=False,
    )

    @api.onchange('dest_cash_control_id')
    def onchange_dest_cash_control_id(self):
        ret = []
        if not self.is_acum_cash_control:
            ret = [('is_acum_cash_control','!=',self.is_acum_cash_control)]
        return {
        'domain' : {
            'dest_cash_control_id' : ret,
            }
        }

    def transfer_cash(self):
        if self.operation == 'transfer_to_cash':
            vals = {
                'name': 'Destino: %s'%(self.dest_cash_control_id.name),
                'orig_journal_id': self.orig_journal_id.id,
                'dest_cash_control_id': self.dest_cash_control_id.id,
                'amount': self.amount,
            }
            transfer = self.env['cash.control.transfer.cash'].create(vals)
            transfer.action_transfer()
            # transfer.action_receipt()
        elif self.operation == 'transfer_to_bank':
            payment_type = 'outbound'
            payment_methods = self.bank_journal_id.outbound_payment_method_ids
            payment_method = payment_methods.filtered(
                    lambda x: x.code == 'manual')
            if not payment_method:
                raise ValidationError(_(
                    'Pay now journal must have manual method!'))
            vals = {
                'journal_id': self.orig_journal_id.id,
                'destination_journal_id': self.bank_journal_id.id,
                'amount': self.amount,
                'payment_date': datetime.today().strftime('%Y-%m-%d'),
                'payment_type': 'transfer',
                'payment_method_id': payment_method.id,
            }
            transfer = self.env['account.payment'].create(vals)
            transfer.post()

