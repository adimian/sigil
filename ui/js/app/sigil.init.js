"use strict"
var init = function() {
    var app = new SigilApplication();
    ko.applyBindings(app);
    window.app = app;

    Sammy(function() {
        this.get('/', function() {});
        this.get('#users', function() {
            authed_request('GET', '/user', null, function(data) {
                app.data_view.collection(data['users']);
                app.data_view.columns([
                    new DataColumn('id', 'ID'),
                    new DataColumn('username', 'Username'),
                    new DataColumn('displayname', 'Display Name'),
                    new DataColumn('email', 'E-mail'),
                    new DataColumn('active', 'Active')
                ]);
            });
        });

        this.get('#overview', function() {
            app.data_view.collection(null);
        });
        this.get('#teams', function() {
            authed_request('GET', '/team', null, function(data) {
                app.data_view.collection(data['groups']);
                app.data_view.columns([
                    new DataColumn('id', 'ID'),
                    new DataColumn('name', 'Name'),
                    new DataColumn('active', 'Active')
                ]);
            });
        });
        this.get('#groups', function() {
            authed_request('GET', '/group', null, function(data) {
                app.data_view.collection(data['groups']);
                app.data_view.columns([
                    new DataColumn('id', 'ID'),
                    new DataColumn('name', 'Name'),
                    new DataColumn('active', 'Active')
                ]);
            });
        });
        this.get('#permissions', function() {
            app.data_view.collection(null);
        });
        this.get('#import', function() {
            app.data_view.collection(null);
        });
        this.get('#export', function() {
            app.data_view.collection(null);
        });
        this.get('#applications', function() {
            authed_request('GET', '/app', null, function(data) {
                app.data_view.collection(data['apps']);
                app.data_view.columns([
                    new DataColumn('id', 'ID'),
                    new DataColumn('name', 'Name'),
                ]);
            });
        });

    }).run();

    app.current_user.get_info();

    // dropzone setup
    Dropzone.options.importFileDropzone = {
        url: SIGIL_API + "/import/excel",
        paramName: "file",
        headers: get_auth_headers(),
        uploadMultiple: false,
        maxFiles: 1,
        addRemoveLinks: false,
        acceptedFiles: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel.sheet.macroEnabled.12",
        init: function() {
            this.on("error", function(file, response) {
                $(".dz-error-message>span").text(response.message);
            });
        }
    };

};

$(init);
