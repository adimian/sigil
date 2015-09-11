"use strict"
var AppContext = function()  {
    var self = this;
    self.name = ko.observable(undefined);
    self.appkey = ko.observable(undefined);
    self.blank = ko.observable(true);

    self.needs = ko.observableArray([]);

    self.register = function() {
        authed_request('POST', '/app/register', {
            name: self.name()
        }, function(data) {
            self.appkey(data["application-key"]);
            self.blank(false);
        });
    };
};
