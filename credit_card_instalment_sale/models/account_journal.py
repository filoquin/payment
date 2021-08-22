# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

MAX_INSTALMENT = 24


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    account_card_ids = fields.Many2many(
        'account.card',
        string='Cards',
    )

    """card_type = fields.Selection(
        [('credit', 'credit'), ('debit', 'debit')],
    )

    card_partner_id = fields.Many2one(
        'res.partner',
        string='Card Partner',
    )
    instalment_ids = fields.One2many(
        'account.card.instalment',
        'journal_id',
        string='Instalments',
    )

    instalment_product_id = fields.Many2one(
        'product.product',
        string='Product to invoice'
    )

    def create_instalment_plan(self):
        self.ensure_one()
        if self.card_type == 'debit':
            self.env['account.card.instalment'].create({
                'name': '1',
                'instalment': 1,
                'journal_id': self.id,
                'product_id': self.instalment_product_id.id

            })
        elif self.card_type == 'credit':
            for i in range(1, MAX_INSTALMENT):
                self.env['account.card.instalment'].create({
                    'name': str(i),
                    'instalment': i,
                    'journal_id': self.id,
                    'product_id': self.instalment_product_id.id

                })

    """
