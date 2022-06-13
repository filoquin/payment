from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class PosPaymentMethod(models.Model):

    _inherit = "pos.payment.method"

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [
            ("qr", "QR")
        ]

    use_qr = fields.Boolean(
        string="Use Fixed QR",
    )

    qr_method = fields.Selection(
        [
            ("fix", "Offline QR image"),
            ("fix_by_config", "Offline QR config"),
            ("payment", "QR payment acquirer"),
        ],
        string="QR method",
    )
    qr_image = fields.Binary(
        string="qr image",
        attachment=True,
    )
    acquirer_id = fields.Many2one(
        "payment.acquirer",
        string="acquirer",
    )
    config_qr_ids = fields.One2many(
        "pos.payment.config_qr",
        "method_id",
        string="Config QR",
        auto_join=True,
    )

    pos_qr_image = fields.Binary(string="qr image", compute="_compute_pos_qr_image")

    def _compute_pos_qr_image(self):
        for record in self:
            if record.qr_method == "fix":
                record.pos_qr_image = record.qr_image
            elif record.qr_method == "fix_by_config":
                session_id = self.env["pos.session"].search(
                    [("user_id", "=", self.env.user.id), ("state", "=", "opened")],
                    limit=1,
                )
                if session_id:
                    qr_id = record.config_qr_ids.filtered(
                        lambda x: x.config_id.id == session_id.config_id.id
                    )
                    if qr_id:
                        record.pos_qr_image = qr_id[0].qr_image

                        continue
            record.pos_qr_image = False

    @api.model
    def cancel_qr(self, data={}):
        return True

    @api.model
    def start_qr_transaction(self, data):
        method = self.browse(data["paymentMethod"])
        if len(method.acquirer_id):
            cust_method_name = "%s_pos_transaction" % (method.acquirer_id.provider)
            if hasattr(method.acquirer_id, cust_method_name):
                method = getattr(method.acquirer_id, cust_method_name)
                return method(data)
        return False

    @api.model
    def check_qr_transaction(self, data):
        method = self.browse(data["paymentMethod"])
        data["config_id"] = self.env["pos.config"].browse(data["configId"])
        if len(method.acquirer_id):
            cust_method_name = "%s_pos_transaction_check" % (
                method.acquirer_id.provider
            )
            if hasattr(method.acquirer_id, cust_method_name):
                method = getattr(method.acquirer_id, cust_method_name)
                return method(data)
        return False

    @api.model
    def get_qr_transactions(self, data):
        method = self.browse(data["paymentMethod"])
        data["config_id"] = self.env["pos.config"].browse(data["configId"])
        if len(method.acquirer_id):
            cust_method_name = "%s_get_qr_transactions" % (method.acquirer_id.provider)
            if hasattr(method.acquirer_id, cust_method_name):
                method = getattr(method.acquirer_id, cust_method_name)
                return method(data)
        return False

    @api.model
    def set_qr_manual_authorization(self, data):
        method = self.browse(data["paymentMethod"])
        data["config_id"] = self.env["pos.config"].browse(data["configId"])
        if len(method.acquirer_id):
            cust_method_name = "%s_set_qr_manual_authorization" % (
                method.acquirer_id.provider
            )
            if hasattr(method.acquirer_id, cust_method_name):
                method = getattr(method.acquirer_id, cust_method_name)
                return method(data)
        return False

    @api.model
    def get_qr_image(self, data):
        method = self.browse(data["paymentMethod"])

        if method.qr_method.startswith("fix"):
            return self.pos_qr_image
        elif method.qr_method == "payment":

            cust_method_name = "%s_get_qr_image" % (method.acquirer_id.provider)
            if hasattr(method.acquirer_id, cust_method_name):
                method = getattr(method.acquirer_id, cust_method_name)
                return method(data)
        return False

    class PosPaymentConfigQR(models.Model):
        _name = "pos.payment.config_qr"
        _description = "payment Config Qr"

        method_id = fields.Many2one(
            "pos.payment.method",
            string="method",
        )
        config_id = fields.Many2one(
            "pos.config",
            string="Field Label",
        )
        qr_image = fields.Binary(
            string="qr image",
            attachment=True,
        )
