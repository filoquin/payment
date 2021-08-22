# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class SaleOrderInstalmentTemplate(models.Model):
    _name = 'sale.order.payment.template'
    _description = 'sale order instalment template'

    name = fields.Char(
        string='Name',
        required=True,
    )
    instalment_ids = fields.Many2many(
        'account.card.instalment',
        string='Instalment',
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    instalment_count = fields.Integer(
        string='instalment count',
        compute='_compute_instalment_count'
    )

    payment_tmpl_id = fields.Many2one(
        'sale.order.payment.template',
        string='Payment method',
    )

    instalment_ids = fields.Many2many(
        'account.card.instalment',
        string='Instalment',
    )

    @api.onchange('payment_tmpl_id')
    def _onchange_payment_tmpl_id(self):
        self.instalment_ids = self.payment_tmpl_id.instalment_ids

    @api.depends('instalment_ids')
    def _compute_instalment_count(self):
        for res in self:
            res.instalment_count = len(res.instalment_ids)


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    price_1 = fields.Float(
        string='price 1',
        compute="compute_instalment"
    )
    price_2 = fields.Float(
        string='price 2',
        compute="compute_instalment"
    )
    price_3 = fields.Float(
        string='price 3',
        compute="compute_instalment"
    )
    price_4 = fields.Float(
        string='price 4',
        compute="compute_instalment"
    )

    @api.depends('price_total')
    def compute_instalment(self):
        for res in self:
            prices = {}
            for i in range(0, 4):
                if len(res.order_id.instalment_ids) > i:
                    prices['price_%s' % str(i + 1)] = res.price_total * res.order_id.instalment_ids[i].coefficient                        
                else:
                    prices['price_%s' % str(i + 1)] = 0.0

            res.write(prices)