from odoo import fields, models, _


class PaymentAcquirer(models.Model):

    _inherit = "payment.acquirer"

    def mp_qr_pos_transaction(self, data):
        if data["configId"]:
            config_id = self.env["pos.config"].browse(data["configId"])
            data["store_external_id"] = config_id.mp_store_id.external_id
            data["pos_external_id"] = config_id.mp_external_id
        return self.create_order(data)

    def mp_qr_pos_transaction_check(self, data):
        if "transaction_id" in data:
            tx = self.env["payment.transaction"].sudo().browse(data["transaction_id"])
            return {
                "state": tx.state,
                "transaction_id": tx.id,
                "reference": tx.reference,
                "amount": tx.amount,
            }
        return {}

    def mp_qr_set_qr_manual_authorization(self, data):
        if "transaction_id" in data:
            tx = self.env["payment.transaction"].sudo().browse(data["transaction_id"])
            tx.merchant_order_id = data["tx_manual_authorization"]
            tx._set_transaction_authorized()

    def get_qr_transactions(self, data):
        if data["configId"]:
            config_id = self.env["pos.config"].browse(data["configId"])
            data["store_external_id"] = config_id.mp_store_id.external_id
            data["pos_external_id"] = config_id.mp_external_id
