from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

MAX_INSTALMENT = 24

class PosPaymentMethod(models.Model):

    _inherit = 'pos.payment.method'

    card_type = fields.Selection(
        [('credit', 'credit'), ('debit', 'debit')],
    )

    card_partner_id = fields.Many2one(
        'res.partner',
        string='Card Partner',
    )
    instalment_ids = fields.One2many(
        'account.card.instalment',
        'method_id',
        string='Instalments',
    )

    instalment_product_id = fields.Many2one(
        'product.product',
        string='instalment Product'
    )

    def create_instalment_plan(self):
        self.ensure_one()
        if self.card_type=='debit':
            self.env['account.card.instalment'].create({
                'name':'1',
                'instalment':1,
                'method_id':self.id,
                'product_id':self.instalment_product_id.id

            })
        elif self.card_type=='credit':
            for i in range(1,MAX_INSTALMENT):
                self.env['account.card.instalment'].create({
                    'name':str(i),
                    'instalment':i,
                    'method_id':self.id,
                    'product_id':self.instalment_product_id.id

                })


class AccountCardInstalment(models.Model):
    _inherit = 'account.card.instalment'
    _order = "method_id , instalment asc"

    @api.depends('name', 'method_id', 'instalment')
    def _compute_name(self):
        for record in self:
            if record.name == '/' and len(record.method_id) and record.instalment:
                record.name = "%s-%s" % (record.method_id.name, record.instalment)

    @api.onchange('method_id')
    def _onchange_method_id(self):
        self.product_id = self.method_id.product_id.id

    method_id = fields.Many2one(
        'pos.payment.method',
        string='method',
        domain=[('is_cash_count', '=', False)]
    )
    card_type = fields.Selection(
        [('credit', 'credit'), ('debit', 'debit')],
        related="method_id.card_type"
    )    
    @api.constrains('method_id', 'instalment')
    def _check_instalment(self):
        for record in self:
            if record.method_id.card_type == 'debit' and record.instalment > 1:
                raise ValidationError("Debit card has only 1 instalment plan")
            instalment = self.search([
                ('id','!=', record.id),
                ('method_id', '=', record.method_id.id),
                ('instalment', '=', record.instalment)
            ])
            if len(instalment):
                raise ValidationError("Instalment exist for this Journal")

