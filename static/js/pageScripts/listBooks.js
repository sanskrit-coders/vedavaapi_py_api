$(document).ready(function () {
    console.log("In ready function.");
     $(window).load(function() {
        getServerInfo();
        getBooks(true);
    });
    var myurl = window.location.href;
    $('#server').html("Server Running on: "+myurl);
    $('#getbooks').click(function(){
        getBooks(true);
    });

    $('#file-picker').on("change", function() {
        handleFiles(this.files);
    });

    //code for workload upload
    $('#upload-button').click(function(){
        startUpload();

    });

    $('#wlupload').click(function () {
        //$('#bgblur').css('-webkit-filter','blur(0.8px)');
        $('#bgblur').css('opacity','0.5');
        $('#upload_popup').fadeIn("slow");

        //select workload for file uploading
        $('#selbooks').on('change', function(e) {
            $('#uploadpath').val($(this).val());
        });
    });

    $('#capture_popup_close').click(function(){
        $('#capture_popup').fadeOut("slow");
        $('#bgblur').css('opacity','1');
        //$('#bgblur').css('-webkit-filter','none');
    });

    $('#upload_popup_close').click(function(){
        $('#upload_popup').fadeOut("slow");
        $('#bgblur').css('opacity','1');
        //$('#bgblur').css('-webkit-filter','none');
        //location.reload();
    });


    var cmds = ['delete'];
    for (var i = 0; i < cmds.length; ++i) {
        var $cmd_button = $('#wl' + cmds[i]);
        $cmd_button.click(function() {
            cmd = this.value;
            var names = getSelBooks('wltable');
            var formdata = getWlForm(names.books, 'wlactions');
            bookProcess(formdata, cmd);
        });
    }

    $('#refresh').click(function () {
        window.location.reload(true);
    });

    $('#upgrade_wlwizard').click(function () {
        updateWlWizard();
    });
	$('#reportbug').click(function () {
		var newwin="target=\"_blank\"";
        window.open('/bugzilla/enter_bug.cgi',newwin);
    });


    $('#selectall').click(function () {
        $('#wltable').find('input[type="checkbox"]').each(function (){
            this.checked =true;
        });
    });

    $('#clearall').click(function (){
        $('#wltable').find('input[type="checkbox"]').each(function (){
            this.checked =false;
        });
    });
});