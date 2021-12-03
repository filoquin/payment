odoo.define('pos_card_instalment.models', function (require) {
var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var time = require('web.time');

// Agrego los campos en la tarjeta
models.load_fields('pos.payment.method', ['card_id','instalment_ids', 'instalment_product_id']);

//Agrego los campos referidos a la tarjeta en el pago
//models.load_fields('pos.payment', ['card_id','instalment_id', 'card_number', 'tiket_number', 'lot_number', 'fee']);

// Obtengo las cuotas y las asifno a sus metodos de pago
models.load_models([{
    model: 'account.card.instalment',
    fields: ['card_id','name','instalment','product_id','amount','coefficient','discount','bank_discount','active','card_type'],
    domain: function(self){ return [['card_id', '!=', false]]; },
    loaded: function(self, instalment_ids) {
        let instalment_by_card = {}
        _.each(instalment_ids, function(instalment_id,index) {
            instalment_by_card[instalment_id.card_id[0]] = instalment_by_card[instalment_id.card_id[0]] || [] ;
            instalment_by_card[instalment_id.card_id[0]].push(instalment_id);
        })

        _.each(self.payment_methods_by_id, function(payment_method,index) {
            if (payment_method.card_id){
                self.payment_methods_by_id[index].instalments = instalment_by_card[payment_method.card_id[0]]
            }
        });
    }
},
]);

var _super_Paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        /*
    TODO: esta funcion tambien deberia agregar los campos
    init_from_JSON: function(json){
        this.amount = json.amount;
        this.payment_method = this.pos.payment_methods_by_id[json.payment_method_id];
        this.payment_status = json.payment_status;
        this.ticket = json.ticket;
        this.card_type = json.card_type;
        this.transaction_id = json.transaction_id;
    },
        */
        export_as_JSON: function(){
            return {
                name: time.datetime_to_str(new Date()),
                payment_method_id: this.payment_method.id,
                amount: this.get_amount(),
                payment_status: this.payment_status,
                ticket: this.ticket,
                card_type: this.card_type,
                instalment_id: this.instalment_id,
                card_number: this.card_number,
                tiket_number: this.tiket_number,
                lot_number: this.lot_number,
                fee: this.fee,
            };
        }
      
    });

var gui = require('point_of_sale.gui');
var PopupWidget = require('point_of_sale.popups');

var PaymentCardsPopupWidget = PopupWidget.extend({
    template: 'PaymentCardsPopupWidget',
    show: function (options) {
        var self = this;
        this._super(options);
        
        if (options) {
			if (options.auto_close) {
				setTimeout(function () {self.gui.close_popup();}, 2000);
			} else {
				self.close();
				self.$el.find('.popup').append('<div class="footer"><button class="button accept" id="btn-accept">Continuar</button><button class="button cancel">Cerrar</button></div>');
			}
			
			if (options.line) {
				var line = options.line;
				var amount = line.get_amount();
				var instalments = line.payment_method.instalments;
				var selected = line.payment_method.selected;
				
				for (obj in instalments){
					var amountCof = amount * instalments[obj]['coefficient'];
					var fee = amountCof - amount;
					self.$el.find("#selectPopupInstalments").append('<option value="' + instalments[obj]['id'] + '" coef="' + fee + '" amount="' + amountCof + '">' + instalments[obj]['name'] + '</option>');
				}
				
				if (selected) {
					self.$el.find('#selectPopupInstalments').val(selected);
				} else {
					self.$el.find('#selectPopupInstalments').val(1);
				}
				var amount = self.$el.find('#selectPopupInstalments option:selected').attr('amount');
				self.$el.find('#amount').empty().text(amount);
			}
        }
        
        self.$el.find('#selectPopupInstalments').change(function(){
    		var amount = self.$el.find('#selectPopupInstalments option:selected').attr('amount');
			self.$el.find('#amount').empty().text(amount);
    	})
    	
        self.$el.find('#btn-accept').click(function(){
        	var myformData = {};
        	var form = $(".checkout_form");

        	if ($(form)[0].checkValidity() === false) {
        		self.$el.find('.message-error').removeClass('hidden');
            } else {
            	let fd = new FormData(form[0]);
        	    for (var pair of fd.entries()) {
        	    	myformData[pair[0]] = pair[1]; 
        	    }
        	    
        	    let payment_method = options.line.payment_method;
        	    let fee = self.$el.find('#selectPopupInstalments option:selected').attr('coef');
                let amountCof = self.$el.find('#selectPopupInstalments option:selected').attr('amount');

        	    let instalment_id = self.$el.find('#selectPopupInstalments option:selected').val();
                let order = options.obj.pos.get_order();

                let line = order.selected_paymentline;

        	    line['instalment_id'] = parseInt(instalment_id);
        	    line['card_number'] = self.$el.find('#cc-number').val();
        	    line['tiket_number'] = self.$el.find('#ticket-number').val();
        	    line['lot_number'] = self.$el.find('#lot-number').val();
        	    line['fee'] = fee;

                let product = options.obj.pos.db.get_product_by_id(payment_method.id);
                order.add_product(product, {extras:{name: 'Cargo Tarjeta'}, price:fee,quantity:1, merge: false});
           	    line.set_amount(amountCof) ;

        	    line.set_payment_status('done');
        	    options.obj.render_paymentlines();
        	    self.gui.close_popup();
            }
    	})
    }
});

gui.define_popup({name:'payment-card', widget: PaymentCardsPopupWidget});

// Modifico la pantalla de pago
screens.PaymentScreenWidget.include({
    start:function(){
        this._super();
        var self = this;
        console.log('start');            
    },
    show: function(){
        this._super();
        console.log('show');
    },
    render_payment_terminal: function() {
    	var self = this;
    	var order = this.pos.get_order();
    	if (!order) {
            return;
        }
    	
    	var paymentline = order.selected_paymentline
    	
    	if (paymentline) {
    		var line = order.get_paymentline(paymentline.cid);
    		this.$el.find('.instalment').change(function(){
        		if (line.payment_method) {
        		    var payment_method = line.payment_method;
        			payment_method['selected'] = $(this).val();
        		}
        	});
    		this.$el.find('#btnData').click(function(){
    			self.gui.show_popup('payment-card',{
            		'title': 'texto de prueba',
            		'body':  'cuerpo de prueba',
            		'line': line,
            		'obj': self,
            		'auto_close': false
            	})
    		})
    		
            if (line.payment_method.selected){
                var payment_selected = line.payment_method.selected;
            	self.$el.find('.instalment').val(payment_selected);
            }
    	}
        
        console.log('Render');
    },
    init: function(parent,options){
    	var self = this;
        this._super(parent, options);
        
    	this.keyboard_keydown_handler = function(event){
            if (event.keyCode === 8 || event.keyCode === 46) { // Backspace and Delete
               event.preventDefault();
               self.keyboard_handler(event);
            }
        };

        this.keyboard_handler = function(event){
           var key = '';

           if (event.type === "keypress") {
                if (event.keyCode === 13) { // Enter
                    self.validate_order();
                } else if ( event.keyCode === 190 || // Dot
                            event.keyCode === 110 ||  // Decimal point (numpad)
                            event.keyCode === 188 ||  // Comma
                            event.keyCode === 46 ) {  // Numpad dot
                    key = self.decimal_point;
                } else if (event.keyCode >= 48 && event.keyCode <= 57) { // Numbers
                    key = '' + (event.keyCode - 48);
                } else if (event.keyCode === 45) { // Minus
                    key = '-';
                } else if (event.keyCode === 43) { // Plus
                    key = '+';
                }else{
                 return ;
                }
            } else { // keyup/keydown
                if (event.keyCode === 46) { // Delete
                    key = 'CLEAR';
                } else if (event.keyCode === 8) { // Backspace
                    key = 'BACKSPACE';
                }
            }

            self.payment_input(key);
        };
    },
});

});
