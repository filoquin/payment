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
      this._super.apply(this, arguments);
      return this._qr_start(cid);
    },
    send_payment_cancel: function (order, cid) {
      this._super.apply(this, arguments);
      clearTimeout(this.polling);
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
          let configId = line.pos.pos_session.config_id[0]
          let sessionId = line.pos.pos_session.id
          let data = [{
              configId:configId, 
              sessionId:sessionId, 
              name: line.order.name, 
              reference:line.cid, 
              paymentMethod : line.payment_method.id, 
              amount: line.amount
           }]
        return rpc.query({
            model: 'pos.payment.method',
            method: 'start_qr_transaction',
            args: data,
        }).then(function (data) {
          //$(ev.currentTarget).hide();
          return self._qr_handle_response(data);
          return true;
        });



    },
    _qr_handle_response: function (response) {
        var line = this.pos.get_order().selected_paymentline;

        line.set_payment_status('waitingCard');
        this.pos.chrome.gui.current_screen.render_paymentlines();
        var self = this;
        var res = new Promise(function (resolve, reject) {
            // clear previous intervals just in case, otherwise
            // it'll run forever
            clearTimeout(self.polling);

            self.polling = setInterval(function () {
                self._poll_for_response(resolve, reject);
            }, 3000);
        });

        // make sure to stop polling when we're done
        res.finally(function () {
            self._reset_state();
        });

        return res;
    },
    // private methods
    _reset_state: function () {
        this.was_cancelled = false;
        this.last_diagnosis_service_id = false;
        this.remaining_polls = 2;
        clearTimeout(this.polling);
    },
    _poll_for_response: function (resolve, reject) {
       console.log(resolve);
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
