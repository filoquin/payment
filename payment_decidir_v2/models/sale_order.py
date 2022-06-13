from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def add_fee_line(self, fees, instalment_id):
        self.ensure_one()
        if fees <= 0:
            return

        if instalment_id.product_id.taxes_id:
            tax_amount = instalment_id.product_id.taxes_id.compute_all(fees)

            # esto lo hago para restar el iva si no esta incluido
            # en el precio
            if tax_amount["total_included"] > fees:
                tax_amount = instalment_id.product_id.taxes_id.with_context(
                    force_price_include=True
                ).compute_all(fees)
                amount = tax_amount["total_excluded"]
            else:
                amount = tax_amount["total_included"]
            line_vals = []
            line_vals.append(
                {
                    "order_id": self.id,
                    "product_id": instalment_id.product_id.id,
                    "name": instalment_id.product_id.display_name,
                    "product_uom_qty": 1,
                    "price_unit": amount,
                    "is_financial_line": True,
                    "tax_id": [(6, 0, instalment_id.product_id.taxes_id.ids)],
                    "sequence": 999,
                }
            )
