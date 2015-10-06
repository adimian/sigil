var FEEDBACK_TEMPLATE =  '<div class="pwf-tooltip" style="display: none;" id="pwf-tooltip">'+
						 '  <div class="pwf-tooltip-block"></div>'+
						 '  <div class="pwf-tooltip-content"><div><b>Password suggestions</b></div>:CONTENT:</div>'+
						 '</div>'
var LINE_TEMPLATE = "<div data-bind='visible: $root.:IS_ACTIVE_METHOD:()'>:CONTENT:<span>:EXTRA:</span><span data-bind='css:$root.:CSS_METHOD:()'></span></div>"
var YES = "glyphicon glyphicon-ok pwf-color_green"	
var NO = "glyphicon glyphicon-remove pwf-color_red"	

var has_regex = function(value, regex){
	if(value.match(regex)){
		return true;}
	return false;
}

var FeedbackViewModel = function(options){
	var self = this;
	self.options = options;
	
	self.password_field = ko.computed(function(){
		var val = window.app.user_account.password()
		if(val){
			return val
		}
		return "";
	});
	
	self.enforce_capitals = ko.observable(options.enforce_capitals)
	self.has_capitals = ko.computed(function(){
		return has_regex(self.password_field(), /[A-Z]/) ? YES : NO
	}, this);
	
	self.enforce_length = ko.observable(options.enforce_length)
	self.has_length = ko.computed(function(){
		if(self.password_field().length >= self.options.min_length){
			return YES;}
		return NO;
	}, this);
	
	self.enforce_special_characters = ko.observable(options.enforce_special_characters)
	self.has_characters = ko.computed(function(){
		var has_chars = jQuery.map(self.options.special_characters.split(''), function(n) {
				return has_regex(self.password_field(), new RegExp("\\"+ n ))
			})
		if(has_chars.indexOf(true) > -1){
			return YES;
		}
		return NO;
	}, this);
	
	self.enforce_numbers = ko.observable(options.enforce_numbers)
	self.has_numbers = ko.computed(function(){
		return has_regex(self.password_field(), /[0-9]/) ? YES : NO
	}, this);
}

var build_line = function(description, extra_info, is_active_method, css_method){
	if(extra_info){
		extra_info = ": "+extra_info
	}
	return LINE_TEMPLATE.replace(":CONTENT:", description).replace(":EXTRA:", extra_info).replace(":IS_ACTIVE_METHOD:", is_active_method).replace(":CSS_METHOD:", css_method);
	
}

jQuery.fn.pwfeedback = function (options) {
	options = $.extend({enforce_capitals: true,
						enforce_length: true,
						enforce_special_characters: true,
						enforce_numbers: true,
						min_length: 10,
						special_characters: '_.'}, options);
	var feedback_text = [build_line("Contains capital letters", "", "enforce_capitals", "has_capitals"),
	                     build_line("Appropriate length", options.min_length, "enforce_length", "has_length"),
	                     build_line("Contains special characters", options.special_characters, "enforce_special_characters", "has_characters"),
	                     build_line("Contains numbers", "", "enforce_numbers", "has_numbers")]
	var fvm = new FeedbackViewModel(options)
	var filled_template = FEEDBACK_TEMPLATE.replace(":CONTENT:", feedback_text.join(""));
	var el;
	
	$(this).on('focus', function(){
		el = $(filled_template);
		el.appendTo("body")
		
		var rect = $(this)[0].getBoundingClientRect();
		el.show();
		height = $(this).outerHeight();
		el_height = el.outerHeight();
		pos_height = rect.top
		pos_width = rect.right + 10
		el.css({"top": pos_height, "left": pos_width})
		
		ko.applyBindings(fvm, $("#pwf-tooltip")[0]);	
	})
	$(this).on('blur', function(){
		el.remove();
	})
	
};