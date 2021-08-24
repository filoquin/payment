# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_is_zero

from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    card_id = fields.Many2one(
        'account.card',
        string='Card',
        related="payment_method_id.card_id"
    )
    instalment_id = fields.Many2one(
        'account.card.instalment',
        string='Instalment plan'
    )
    card_type = fields.Selection(
        [('credit', 'credit'), ('debit', 'debit')],
        related="card_id.card_type"
    )

    magnet_bar = fields.Char(
        'magnet bar'
    )
    card_number = fields.Char(
        'Card number'
    )
    tiket_number = fields.Char(
        'Tiket number'
    )
    lot_number = fields.Char(
        'Lot number'
    )
    fee = fields.Float(
        string='Fee',
        default=0,
    )
    total_amount = fields.Float(
        string='total amount',
        default=0,
    )

    @api.onchange('magnet_bar')
    def _onchange_magnet_bar(self):
        if self.magnet_bar:
            try:
                track1, track2 = self.magnet_bar.split(';')
                cardnumber, name, data = track1.split('^')
                # to-do: add chksum
                self.card_number = cardnumber
            except ValueError:
                raise ValidationError(_('Could not parse track'))

    def check(self):
        self.ensure_one()
        if self.card_type in ['credit', 'debit']:
            order = self.env['pos.order'].browse(
                self.env.context.get('active_id', False))
            currency = order.currency_id

            init_data = self.read()[0]
            if not float_is_zero(init_data['amount'], precision_rounding=currency.rounding):
                if self.fee:
                    untax_amount = self.fee
                    if len(self.instalment_id.product_id.taxes_id):
                        tax_computed = self.instalment_id.product_id.taxes_id.compute_all(
                            self.fee)
                        #tax_amount = sum(tax_computed.mapped('taxes'))

                        _logger.info('tax_computed %r' % tax_computed)
                        untax_amount = sum(tax_computed.mapped('amount'))

                    order.write({'lines': [(0, 0, {
                        'product_id': self.instalment_id.product_id.id,
                        'qty': 1,
                        'company_id': order.company_id.id,
                        'tax_ids_after_fiscal_position': self.instalment_id.product_id.taxes_id.ids,
                        'price_unit': untax_amount,
                        'price_subtotal': untax_amount,
                        'price_subtotal_incl': untax_amount,
                        'name': _("%s %s") % (self.instalment_id.product_id.display_name,  self.instalment_id.name)
                    }
                    )]})
                order._onchange_amount_all()
                order.add_payment({
                    'pos_order_id': order.id,
                    'amount': currency.round(init_data['amount'] + init_data['fee']) if currency else init_data['amount'] + init_data['fee'],
                    'name': init_data['payment_name'],
                    'payment_method_id': init_data['payment_method_id'][0],
                    'instalment_id': init_data['instalment_id'][0],
                    'card_type': init_data['card_type'],
                    'card_number': init_data['card_number'],
                    'tiket_number': init_data['tiket_number'],
                    'lot_number': init_data['lot_number'],
                })

            if float_is_zero(order.amount_total - order.amount_paid, precision_rounding=currency.rounding):
                order.action_pos_order_paid()
                return {'type': 'ir.actions.act_window_close'}

            return self.launch_payment()

        return super(PosMakePayment, self).check()

    @api.onchange('instalment_id')
    def change_instalment_id(self):
        self.ensure_one()
        if len(self.instalment_id):
            if self.instalment_id.coefficient != 1:
                fee = self.amount * self.instalment_id.coefficient
                self.fee = fee
                self.total_amount = self.amount + fee
            else:
                self.fee = 0
                self.total_amount = self.amount
        else:
            self.fee = 0
            self.total_amount = self.amount
