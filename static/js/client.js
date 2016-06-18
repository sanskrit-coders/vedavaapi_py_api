// Validating Empty Field first and then start capture
function startupload() 
{
    if (document.getElementById('uploadwlname').value == ""){
            alert("Fill All Fields !");
    } 
    else {        
            doUpload();
            $('#bgblur').css('opacity','1');
    }
}

function update_wlwizard() {
    var $consolediv = $('#console');
    $consolediv.html("updating wlwizard...");
    $.get('/admin/update', function(response) { 
        console.log(response);
        $consolediv.html(response);
    });    
}

function urlize(lpath, text, newwin)
{
    if (typeof text == "undefined")
        text = lpath;
    if (typeof newwin == "undefined")
        newwin = true
    if (newwin == true)
        newwin = "target=\"_blank\"";
    var url = "";
    if (lpath.startsWith('http') || lpath.startsWith('/'))
        url = lpath;
    else url = "/books/relpath/" + lpath;
    return '<a href="' + url + '" ' + newwin + '>' + text + '</a>';
}

//this method is for getting  serverinfo using api
function getserverinfo() {
    $.getJSON('/admin/getserverinfo', function(response) { 
        var resp = (response['splunkurl']) 
                ? "Splunk Running at: "+ urlize(response['splunkurl'])
                : "Splunk is not running."

            $('#splunk').html(resp);
    });    
}

function settext(id)
{
    var text = $('#ipaddr1_'+id).val();
    $('#ipaddr2_'+id).val(text);  
}

function getbooks(hglass)
{
    if (hglass == true)
        $(".hourglass").show();
    var $selwloads = $('#selwloads');
    $selwloads.empty();
    var html ='';
    html += '<option value="" >'+'</option>';
    $selwloads.append(html);
    var $select = $('#book_table');
    $select.empty(); 
    var pattern=document.getElementById('wload_filter').value;
    $.getJSON('/books/list?pattern='+pattern, function(data){
        $select.append('<table class="wltabclass" id="wltable">'+
                        '</table>');
        var table= $select.children();
        table.empty();
        table.append('<tr>'+
                '<th>Select</th>'+
                '<th>Book Path</th>'+
                '<th>Controls</th>'+
                '</tr>');
        $.each(data, function(key, winfo) {
            var size = 0
            html = '<option value="'+winfo["name"]+'">'+winfo["name"]+'</option>';
            $selwloads.append(html);
            var wlinfo = '<tr>'+
            '<td>' +'<input type="checkbox" value=\"' + 
                winfo["name"] + '\"/>'+ '</td>'+
            '<td>' + 
                urlize("/file/view?path=" + winfo["name"], winfo["name"]) 
                + '</td>'+
            '<td>' + winfo["title"] + '</td>'+
            '<td>' +
            '<button onclick="browse(\''+winfo["name"]+'\');">Details</button>' +
            '<button onclick="docmd(\'' +winfo["name"]+ 
                    '\',\'delete\');">Delete</button>'+
                +'</td>'+
            '</tr>'
                table.append(wlinfo);
        });
        if (hglass == true)
            $(".hourglass").hide();
    });
}

function browse(bname){
    var newwin="target=\"_blank\"";
    window.open('/books/browse/' + encodeURIComponent(bname));
}

function doexplore(wlparms, cmd)
{   
        var formparms = get_wlform(wlparms.wlnames, 'wlactions');
        console.log("Command is :"+cmd+"wlname is:"+wlparms.wlnames);
        console.log(serialize(formparms));
        window.open('/books/' + cmd + '?' +serialize(formparms), '_blank');
        //window.open('/books/' + cmd + '?' +formparms, '_blank');

}

function get_wlform(wlnames, formname) {
    document.getElementById('wlnames').value=wlnames;
    var formparms = get_formparms(formname);
    //console.log(formparms);
    //var formparms = $('#'+formname).serialize();
    return formparms;
}

function docmd(wlname, cmd)
{
        var formparms = get_wlform(wlname, 'wlactions');
        book_process(formparms, cmd);
      //book_process({ "wlnames": wlname }, cmd);
}


function book_process(wlparms, cmd)
{
    $(".hourglass").show();
    //console.log(wlparms);
    var $consolediv = $('#console');
    $.getJSON('/books/'+cmd+'?' + serialize(wlparms), function(data){
        $('#book_table').empty();
        var $resp = "Response for " + cmd + ":<p>\n";;
        $.each(data, function(ind, book) {
            $resp += book.wlname + ": " + book.status + "<br>\n";
        });
        $consolediv.html($resp);
        $(".hourglass").hide();
        setTimeout(function(){
            getbooks(true)
        },1000);
        
    });
}


function get_selbooks(table,isAll)
{
    var selwloads = [];
	var idx = {};
    $seltable = $('#' + table);
	var isAll = (typeof(isAll)=="undefined")?false:isAll;
	var check = ":checked";
	if(isAll) {
		check = "";
	}
    $seltable.find('input[type="checkbox"]'+check).each(function(){
      //$seltable.find('input[type="checkbox"]:checked').each(function(){  
		var wlname = $(this).val();
		idx[wlname] = "$"+this.name+"$";
        selwloads.push(wlname);
    });
    var wlparms = { "books" : selwloads,"idx":idx };
    //console.log(wlparms);
    return wlparms;
}
