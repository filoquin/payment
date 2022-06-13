from odoo import fields, models, _
from odoo.exceptions import UserError
import requests
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class MpStore(models.Model):
    _name = "mp.store"
    _description = "Mercado pago store"

    mp_id = fields.Integer(
        string="MP id",
    )
    acquirer_id = fields.Many2one(
        "payment.acquirer",
        string="acquirer",
        default=lambda self: self.env.ref(
            "mercadopago_qr_payment.payment_acquirer_mp_qr"
        ).id,
    )
    name = fields.Char(
        string="Name",
        size=64,
        required=True,
    )
    external_id = fields.Char(
        string="Store external id",
    )
    business_hours_ids = fields.Many2many(
        "mp.store.business_hours",
        string="business hours",
    )
    country_name = fields.Char(
        string="country",
    )
    state_name = fields.Char(
        string="state",
    )
    city_name = fields.Char(
        string="city",
    )
    street_name = fields.Char(
        string="street name",
    )
    street_number = fields.Char(
        string="street number",
    )
    latitude = fields.Float(
        string="latitude",
    )
    longitude = fields.Float(
        string="longitude",
    )
    reference = fields.Char(
        string="reference",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("active", "active"), ("drop", "Dropped")],
        string="State",
        default="draft",
    )

    def prepare_request_data(self):
        self.ensure_one()
        request_data = {}
        request_data["name"] = self.name
        if self.mp_id == 0:
            request_data["external_id"] = self.external_id
        request_data["location"] = {}
        request_data["location"]["street_number"] = self.street_number
        request_data["location"]["street_name"] = self.street_name
        request_data["location"]["state_name"] = self.state_name
        request_data["location"]["city_name"] = self.city_name
        request_data["location"]["latitude"] = self.latitude
        request_data["location"]["longitude"] = self.longitude
        request_data["business_hours"] = {}
        for business_hours in self.business_hours_ids:
            if business_hours.day not in request_data["business_hours"]:
                request_data["business_hours"][business_hours.day] = []
            request_data["business_hours"][business_hours.day].append(
                {
                    "open": "%02d:%02d"
                    % (
                        int(business_hours.open_time),
                        business_hours.open_time % 1 * 60,
                    ),
                    "close": "%02d:%02d"
                    % (
                        int(business_hours.close_time),
                        business_hours.close_time % 1 * 60,
                    ),
                }
            )

        return request_data

    def action_update_mp(self):
        self.acquirer_id.action_mp_update_store(self.mp_id)

    def unlink(self):
        for record in self.filtered(lambda s: s.mp_id != 0):
            record.acquirer_id.action_mp_unlink_store(self.mp_id)
        return super().unlink()

    def action_force_active(self):
        self.state = "active"


class MpStoreBusinessHours(models.Model):
    _name = "mp.store.business_hours"
    _description = "Mercado pago store business hours"

    name = fields.Char(string="name", compute="_compute_name")

    day = fields.Selection(
        [
            ("monday", "Monday"),
            ("tuesday", "Tuesday"),
            ("wednesday", "Wednesday"),
            ("thursday", "Thursday"),
            ("friday", "Friday"),
            ("saturday", "Saturday"),
            ("sunday", "Sunday"),
        ],
        string="Filed Label",
    )
    open_time = fields.Float(
        string="open",
    )
    close_time = fields.Float(
        string="close",
    )

    def _compute_name(self):
        for record in self:
            open_time = (
                "%02d:%02d" % (int(record.open_time), record.open_time % 1 * 60),
            )
            close_time = (
                "%02d:%02d" % (int(record.close_time), record.close_time % 1 * 60),
            )
            record.name = _("%s from %s to %s" % (record.day, open_time, close_time))
