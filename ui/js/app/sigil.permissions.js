"use strict"
var Need = function (ctx, scope){
    var self = this;
    self.ctx = ctx;
    self.scope = scope;
    self.active = ko.observable();
    self.permission = scope.join(".");
}
