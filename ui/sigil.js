"use strict"

var SIGIL_API = '/api'
	
var authed_request = function(verb, url, data){
	return $.ajax({
			method: verb,
			headers: {'Sigil-Token': ''}});
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
	
	self.first_name = ko.observable();
	self.last_name = ko.observable();
	self.display_name = ko.observable();
	self.user_id = ko.observable();
	
	self.auth_token = ko.observable("placeholder");
};

var TabItem = function(key, label){
	this.key = key;
	this.label = label;
};

var SigilApplication = function() {
    var self = this;
    
    self.tabs = [new TabItem('overview', 'Overview'),
                 new TabItem('users', 'Users')]
    
    self.login_error_message = ko.observable();
    self.error_message = ko.observable();
    
    self.server_options = new ServerOptions();
    self.current_user = new SigilUser();
    
    self.current_tab = ko.observable(self.tabs[0]);
    
    self.authenticated = ko.computed(function(){
    	// TODO: should check session validity against the API
    	return !!self.current_user.auth_token();
    }, this);
    
    self.authenticated.subscribe(function(new_value) {
    	if (!new_value){
    		$("#login_modal").modal({
    			show: true,
    			backdrop: 'static'
    		})
    	} else {
    		console.log('hiding');
    		$("#login_modal").modal('hide');
    	};
    });
    
    self.current_user.auth_token(Cookies.get('token'));
};

SigilApplication.prototype.login = function(){
	var self = this;
	$.post(SIGIL_API+'/login', {
		username: this.current_user.username(),
		password: this.current_user.password(),
		totp: this.current_user.totp()}, 
		function(data){
			self.current_user.auth_token(data.token);
			Cookies.set('token',data.token)
		}).error(function(data){
			self.login_error_message(data.responseJSON.message);
		});
};

SigilApplication.prototype.set_current_tab = function(data){
	app.current_tab(data);
};



var init = function(){
	var app = new SigilApplication();
	ko.applyBindings(app);
	window.app = app;
};

$(init)