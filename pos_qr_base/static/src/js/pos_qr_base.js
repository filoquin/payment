odoo.define("pos_qr_base.payment", function (require) {
  "use strict";

  var core = require("web.core");
  var rpc = require("web.rpc");
  var PaymentInterface = require("point_of_sale.PaymentInterface");
  var screens = require("point_of_sale.screens");

  var _t = core._t;

  screens.PaymentScreenWidget.include({
    show: function (reset) {
      console.log("get QR");
      this.$(".qr_tr").click(function () {
        console.log("Hooo");
      });
      this._super();


    },
    render_paymentlines: function() {

        this._super();

        var self  = this;
        var order = this.pos.get_order();
        var partner = this.pos.get_client();
        if (!order) {
            return;
        }

       this.$(".get_payment_qr").click(function (ev) {
          var paymentMethod = $(ev.currentTarget).attr('data-method-id');
          var line = order.selected_paymentline;
          console.log(line);
          let data = [{paymentMethod : line.payment_method.id, amount: line.amount}]
        rpc.query({
            model: 'pos.payment.method',
            method: 'get_qr_image',
            args: data,
        }).then(function (data) {
          //$(ev.currentTarget).hide();
          line.set_payment_status('waiting');
          console.log(data);
        });

    });


  },
  })


  var PaymentQR = PaymentInterface.extend({
    send_payment_request: function (cid) {
      //this._super.apply(this, arguments);
      return this._qr_start(cid);
    },
    send_payment_cancel: function (order, cid) {
      this._super.apply(this, arguments);
      alert('order');
      // set only if we are polling
      //this.was_cancelled = !!this.polling;
      return this._qr_cancel();
    },
    close: function () {
      this._super.apply(this, arguments);
    },

    _qr_start: function(cid) {
        console.log(cid);
        var self  = this;
        var order = this.pos.get_order();
        var partner = this.pos.get_client();
        if (!order) {
            return;
        }

         var line = order.selected_paymentline;
          console.log(line);
          let data = [{paymentMethod : line.payment_method.id, amount: line.amount}]
        return rpc.query({
            model: 'pos.payment.method',
            method: 'get_qr_image',
            args: data,
        }).then(function (data) {
          //$(ev.currentTarget).hide();
          line.set_payment_status('waiting');
          console.log(data);
        });



    },
    _qr_cancel: function () {
      return rpc
        .query(
          {
            model: "pos.payment.method",
            method: "cancel_qr",
            args: [],
          },
          {
            timeout: 5000,
            shadow: true,
          }
        )
        .catch(function (data) {
          reject();
        })
        .then(function (data) {});
    },
  });

  return PaymentQR;
});
