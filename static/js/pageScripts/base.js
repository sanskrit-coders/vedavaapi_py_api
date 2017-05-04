$(document).ready(function () {

     $(window).load(function() {
        //$('.hourglass').show();
        //getServerInfo();
    });
    var myurl = window.location.href;
    $('#server').html("Server Running on: "+myurl);

    $('#upgrade_wlwizard').click(function () {
        updateWlWizard();
    });
    $('#reportbug').click(function () {
        var newwin="target=\"_blank\"";
        window.open('/bugzilla/enter_bug.cgi',newwin);
    });
    $('.hourglass').hide();

});
