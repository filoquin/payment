from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class PosPaymentMethod(models.Model):

    _inherit = "pos.payment.method"

    def _compute_pos_qr_image(self):
        mp_method_ids = self.filtered(lambda m: m.acquirer_id.provider == "mp_qr")
        other_methods = self - mp_method_ids
        super(PosPaymentMethod, other_methods)._compute_pos_qr_image()
        for method_id in mp_method_ids:
            session_id = self.env["pos.session"].search(
                [("user_id", "=", self.env.user.id), ("state", "=", "opened")], limit=1
            )
            if session_id:
                method_id.pos_qr_image = session_id.config_id.mp_qr
                continue
            else:
                method_id.pos_qr_image = False
