'use strict';
function updateWlWizard() {
    var $consolediv = $('#console');
    $consolediv.html("updating wlwizard...");
    $.get('/admin/update', function(response) {
        console.log(response);
        $consolediv.html(response);
    });
}

function getBooks(hglass)
{
    if (hglass == true)
        $(".hourglass").show();
    var $selbooks = $('#selbooks');
    $selbooks.empty();
    var html ='';
    html += '<option value="" >'+'</option>';
    $selbooks.append(html);
    var $select = $('#book_table');
    $select.empty();
    var pattern=document.getElementById('wload_filter').value;
    $.getJSON('/api_v1/books?pattern='+pattern, function(data){
        if (! processStatus(data))
            return;
        data = data['result'];
        $select.append('<table class="wltabclass" id="wltable">'+
            '</table>');
        var table= $select.children();
        table.empty();
        table.append('<tr>'+
            '<th>Select</th>'+
            '<th>Book Path</th>'+
            '<th>Controls</th>'+
            '</tr>');
        var booklist = data;
        $.each(booklist, function(key, binfo) {
            var size = 0
            var bpath = binfo['path']
            var bookId = binfo._id
            html = '<option value="'+bpath+'">'+bpath+'</option>';
            $selbooks.append(html);
            var book_entry = '<tr>'+
                '<td>' +'<input type="checkbox" value=\"' +
                bpath + '\"/>'+ '</td>'+
                '<td>' + get_anchor_tag("/ui/viewbook.html?_id=" + bookId, bpath) + '</td>'+
                '<td>' +
                '<button onclick="browse(\''+bpath+'\');">Details</button>' +
                '<button onclick="docmd(\'' +bpath+ '\',\'delete\');">Delete</button>'+
                '</td>'+
                '</tr>';
            table.append(book_entry);
        });
        if (hglass == true)
            $(".hourglass").hide();
    });
}

function getSelBooks(table, isAll)
{
    var selbooks = [];
    var idx = {};
    var $seltable = $('#' + table);
    var isAll = (typeof(isAll)=="undefined")?false:isAll;
    var check = ":checked";
    if(isAll) {
        check = "";
    }
    $seltable.find('input[type="checkbox"]'+check).each(function(){
        //$seltable.find('input[type="checkbox"]:checked').each(function(){
        var wlname = $(this).val();
        idx[wlname] = "$"+this.name+"$";
        selbooks.push(wlname);
    });
    var wlparams = { "books" : selbooks,"idx":idx };
    //console.log(wlparams);
    return wlparams;
}

function doexplore(wlparams, cmd)
{
    var formparams = getWlForm(wlparams.wlnames, 'wlactions');
    console.log("Command is :"+cmd+"wlname is:"+wlparams.wlnames);
    console.log(serialize(formparams));
    window.open('/api_v1/' + cmd + '?' +serialize(formparams), '_blank');
    //window.open('/api_v1/' + cmd + '?' +formparams, '_blank');

}

function getWlForm(wlnames, formname) {
    document.getElementById('wlnames').value=wlnames;
    var formparams = getFormParams(formname);
    //console.log(formparams);
    //var formparams = $('#'+formname).serialize();
    return formparams;
}

function docmd(wlname, cmd)
{
    var formparams = getWlForm(wlname, 'wlactions');
    bookProcess(formparams, cmd);
    //bookProcess({ "wlnames": wlname }, cmd);
}


function bookProcess(wlparams, cmd)
{
    $(".hourglass").show();
    //console.log(wlparams);
    var $consolediv = $('#console');
    $.getJSON('/api_v1/'+cmd+'?' + serialize(wlparams), function(data){
        if (! processStatus(data))
            return;
        data = data['result'];
        $('#book_table').empty();
        var $resp = "Response for " + cmd + ":<p>\n";;
        $.each(data, function(ind, book) {
            $resp += book.wlname + ": " + book.status + "<br>\n";
        });
        $consolediv.html($resp);
        $(".hourglass").hide();
        setTimeout(function(){
            getBooks(true)
        },1000);

    });
}

function browse(bname){
    var newwin="target=\"_blank\"";
    window.open('/api_v1/path/' + encodeURIComponent(bname));
}



$(document).ready(function () {
    console.log("In ready function.");
     $(window).load(function() {
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
            var cmd = this.value;
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
