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
    else url = "/relpath/" + lpath;
    return '<a href="' + url + '" ' + newwin + '>' + text + '</a>';
}

//this method is for getting  serverinfo using api
function getserverinfo() {
    $.getJSON('/admin/getserverinfo', function(response) { 
    });    
}

function getbooks(hglass)
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
        booklist = data['books'];
        $.each(booklist, function(key, binfo) {
            var size = 0
            var bpath = binfo['path']
            html = '<option value="'+bpath+'">'+bpath+'</option>';
            $selbooks.append(html);
            var book_entry = '<tr>'+
            '<td>' +'<input type="checkbox" value=\"' + 
                bpath + '\"/>'+ '</td>'+
            '<td>' + urlize("/books/view?path=" + bpath, bpath) + '</td>'+
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

function getbook(hglass, bpath)
{
    if (hglass == true)
        $(".hourglass").show();
    var $bookidx = $('#bookidx');
    $bookidx.empty();
    $.getJSON('/books/get?path='+bpath, function(data){
        document.getElementById('bookdetails').value = JSON.stringify(data, null, 4);
        var pages = data['pages'];
        $bookidx.append('<table borderwidth="1" class="wltabclass" id="wltable">');
        for (i = 0; i < pages.length; ++ i) {
            var page = pages[i];
            var size = 0;
            var pagepath = bpath + "/" + page['fname'];
            var html = '<tr><td onclick="setcurpage(this.id, this.innerHTML)" id="' + i + '">' + page['fname'] + '</td></tr>';
            $bookidx.append(html);
        }
        $bookidx.append('</table>');
        if (hglass == true)
            $(".hourglass").hide();
    });
}

function setcurpage(idx, value)
{
    //console.log("Selected page: " + idx + ", value: " + value);
    var oldval = $('#curpage').val();
    var newval = idx + ":" + value;

    if (newval != oldval) {
        console.log("Changed cur page to " + newval);
        $('#curpage').val(newval).trigger('change');
    }
    // document.getElementById('curpage').value = idx + ":" + value;
    // console.log("Book details + " + $("#bookdetails").val());
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
    var selbooks = [];
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
        selbooks.push(wlname);
    });
    var wlparms = { "books" : selbooks,"idx":idx };
    //console.log(wlparms);
    return wlparms;
}
