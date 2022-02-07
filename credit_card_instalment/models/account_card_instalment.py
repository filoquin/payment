# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

MAX_INSTALMENT = 24


class AccountCardInstalment(models.Model):
    _name = 'account.card.instalment'
    _description = 'amount to add for collection in installments'

    card_id = fields.Many2one(
        'account.card',
        string='Card',
    )
    name = fields.Char(
        'Fantasy name',
        default='/'
    )
    instalment = fields.Integer(
        string='instalment plan',
        min=1,
        max=MAX_INSTALMENT,
        help='Number of instalment, less than %s' % str(MAX_INSTALMENT + 1)
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product to invoice'
    )
    amount = fields.Float(
        string='Fix amount'
    )
    coefficient = fields.Float(
        string='coefficient',
        help='Value to multiply the amount',
        default=1.0
    )
    discount = fields.Float(
        string='discount',
        help='discount in amount'
    )
    bank_discount = fields.Float(
        string='bank discount',
        help='Bank discount'
    )
    active = fields.Boolean(
        'Active',
        default=True
    )
    ctf = fields.Float(
        string='C.T.F.'
    )
    tea = fields.Float(
        string='TEA'
    )
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Accreditation method',
    )

    card_type = fields.Selection(
        [('credit', 'credit'), ('debit', 'debit')],
        related="card_id.card_type"
    )

    def get_fees(self, amount):
        self.ensure_one()
        discount = (100 - self.discount) / 100
        return (amount * self.coefficient * discount) - amount

    def get_real_total(self, amount):
        self.ensure_one()
        discount = (100 - self.discount) / 100
        return amount * self.coefficient * discount

    @api.depends('name', 'card_id', 'instalment')
    def _compute_name(self):
        for record in self:
            if record.name == '/' and len(record.card_id) and record.instalment:
                record.name = "%s-%s" % (record.card_id.name,
                                         record.instalment)

    @api.constrains('card_id', 'instalment')
    def _check_instalment(self):
        for record in self:
            if record.card_id.card_type == 'debit' and record.instalment > 1:
                raise ValidationError("Debit card has only 1 instalment plan")
            instalment = self.search([
                ('id', '!=', record.id),
                ('card_id', '=', record.card_id.id),
                ('instalment', '=', record.instalment)
            ])
            if len(instalment):
                raise ValidationError("Instalment exist for this Journal")


class AccountJournalInstalmentAccreditation(models.Model):
    _name = 'account.journal.instalment.accreditation'
    _description = 'bank accreditation method'

    name = fields.Char(
        string='Name',
    )
    accreditation_method = fields.Selection(
        [('after_days', 'after X days'),
         ('next_day_number', 'next day number'),
         ('first_dayweek', 'First day off next month')],
        string='Accreditation method',
    )
    accreditation_param = fields.Char(
        string='accreditation param',
    )
    accreditation_closing_param = fields.Char(
        string='accreditation closing param',
    )

    def compute_date(self, date_string):
        startdate = fields.Date.fromstring(date_string)
        res = startdate
        if self.accreditation_method == 'after_days':
            res = startdate + timedelta(days=int(self.accreditation_param))

        return fields.Date.tostring(res)
