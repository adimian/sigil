var User = function() {
    var self = this;
    self.user_id = ko.observable();
    self.first_name = ko.observable();
    self.last_name = ko.observable();
    self.display_name = ko.observable();
    self.username = ko.observable();
    self.mobile_number = ko.observable();
    self.email = ko.observable();
    self.active = ko.observable();

    self.groups = ko.observableArray();

    self.reset_password = function() {
        // call sigil to reset password
    };

    self.reset_totp = function() {
        // call sigil to reset totp
    };

    self.load = function(item) {
        self.user_id(item.id);
        self.first_name(item.firstname);
        self.last_name(item.lastname);
        self.display_name(item.displayname);
        self.username(item.username);
        self.email(item.email);
        self.active(item.active);
        self.mobile_number(item.mobile);
    };

    self.persist = function() {
        var update = {
            username: self.username(),
            active: self.active(),
            display: self.display_name(),
            email: self.email(),
            firstname: self.first_name(),
            mobile_number: self.mobile_number(),
            surname: self.last_name()
        };
        authed_request('POST', '/user/details', update, function(data) {
            self.load(data);
            $("#user_edit_modal").modal('hide');
            location.reload(false);
        });

    };

    self.register = function() {
        var update = {
            username: self.username(),
            email: self.email(),
            mobile_number: self.mobile_number()
        };
        authed_request('POST', '/user/register', update, function(data) {
            alert('New user created');
        });
        $("#user_add_modal").modal('hide');
    };

};

var LoggedInUser = function() {
    var self = this;
    self.password = ko.observable();
    self.totp = ko.observable();

    self.auth_token = ko.observable("placeholder");

    self.get_info = function() {
        authed_request('GET', '/user/details', null, function(data) {
            self.load(data);
        });
    };
};
LoggedInUser.prototype = new User();
