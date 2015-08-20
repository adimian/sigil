"use strict"

var SIGIL_API = '/api'
	
var postJSON = function(url, data){
	return $.post(url, data)
};

var ServerOptions = function() {
	var self = this;
	self.use_totp = ko.observable();
	$.getJSON(SIGIL_API+'/options', function(data){
		self.use_totp(data.use_totp == "1");
	});
};

var SigilUser = function(){
	var self = this;
	self.username = ko.observable();
	self.password = ko.observable();
	self.totp = ko.observable();
	
	self.auth_token = ko.observable("placeholder");
};

var SigilApplication = function() {
    var self = this;
    self.login_error_message = ko.observable();
    self.error_message = ko.observable();
    
    self.server_options = new ServerOptions();
    self.current_user = new SigilUser()
    
    self.authenticated = ko.computed(function(){
    	return !!self.current_user.auth_token();
    }, this);
    
    self.authenticated.subscribe(function(new_value) {
    	if (!new_value){
    		$("#login_modal").modal({
    			show: true,
    			backdrop: 'static'
    		})
    	} else {
    		$("#login_modal").modal('hide');
    	};
    });
    
    self.current_user.auth_token(null);
};

SigilApplication.prototype.login = function(){
	var self = this;
	$.post(SIGIL_API+'/login', {
		username: this.current_user.username(),
		password: this.current_user.password(),
		totp: this.current_user.totp()}, 
		function(data){
			self.current_user.auth_token(data.token);
		}).error(function(data){
			self.login_error_message(data.responseJSON.message);
		});
};


var init = function(){
	var app = new SigilApplication();
	ko.applyBindings(app);
	window.app = app;
};

$(init)