from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero

import logging

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):

    _inherit = ["pos.config", "mp.pos"]
    _name = "pos.config"

    def action_add_mp(self):
        self.ensure_one()
        acquirer = self.mp_store_id.acquirer_id
        if acquirer:
            vals = {
                "name": self.name,
                "fixed_amount": self.mp_fixed,
            }
            if self.mp_id:
                vals["mp_id"] = self.mp_id
                res = acquirer.mp_update_pos(vals)
            else:
                vals["store_id"] = self.mp_store_id.mp_id
                vals["external_store_id"] = self.mp_store_id.external_id
                vals["external_id"] = self.mp_external_id
                res = acquirer.mp_register_pos(vals)
            if res:
                vals = {
                    "mp_id": res["id"],
                    "mp_qr_url": res["qr"]["image"],
                    "mp_uuid": res["uuid"],
                    "mp_active": True if res["status"] == "active" else False,
                }
                self.write(vals)
                self.action_url2base64()
