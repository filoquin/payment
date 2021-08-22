# -*- coding: utf-8 -*-
from odoo import models, fields

MAX_INSTALMENT = 24


class AccountCard(models.Model):
    _name = 'account.card'
    _description = 'Card instalment'

    name = fields.Char(
        'name',
        required=True,
     )
    card_logo = fields.Binary(
        string='Card logo',
        attachment=True,
    )
    card_type = fields.Selection(
        [('credit', 'credit'), ('debit', 'debit')],
        required=True,
    )
    instalment_product_id = fields.Many2one(
        'product.product',
        string='Product to invoice'
    )
    instalment_ids = fields.One2many(
        'account.card.instalment',
        'card_id',
        string='Instalments',
    )

    def create_instalment_plan(self):
        self.ensure_one()
        if self.card_type == 'debit':
            self.env['account.card.instalment'].create({
                'name': '1',
                'instalment': 1,
                'card_id': self.id,
                'product_id': self.instalment_product_id.id

            })
        elif self.card_type == 'credit':
            for i in range(1, MAX_INSTALMENT):
                self.env['account.card.instalment'].create({
                    'name': str(i),
                    'instalment': i,
                    'card_id': self.id,
                    'product_id': self.instalment_product_id.id

                })
