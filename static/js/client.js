// Validating Empty Field first and then start capture
function startupload() 
{
    if (document.getElementById('uploadpath').value == ""){
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
        $.getJSON('/books/get?path='+bpath, function(data){
        document.getElementById('bookdetails').value = JSON.stringify(data, null, 4); 
        var html = [];
        var itemIdx = 0;
        $bookidx.empty();
        data = data['result'];
        html.push('<div id="item'+itemIdx+'" class="item active"> <div class="row-fluid">');
        var pages = data['pages'];
        for (i = 0; i < pages.length; i++) {
            var page = pages[i];
            var size = 0;
            var pagepath = bpath + "/" + page['fname'];
            var thumbpath = "";
            if (page['tname'] !== undefined && page['tname'] != null) {
                thumbpath = bpath + "/" + page['tname'];
            } else {
                thumbpath = bpath + "/" + page['fname'];
            }
            html[itemIdx] = html[itemIdx].concat('<div data-target="#carousel" data-slide-to="'+i+'" class="col-sm-2"><a href="#x" class="thumb"><img id="thumb'+i+'" src="/books/page/image/'+thumbpath+'" attr-display="/books/page/image/'+pagepath+'" oid="'+i+'"></a></div>');
//            var html = '<tr><td onclick="setcurpage(this.id, this.innerHTML)" id="' + i + '">' + page['fname'] + '</td></tr>'; 
            if ((i>1) && ((i+1)%6 == 0) && (i != (pages.length-1))) {
                html[itemIdx] = html[itemIdx].concat('</div> </div>');
                itemIdx++;
                html.push('<div id="item'+itemIdx+'" class="item">');
            }
        }
        html[itemIdx] = html[itemIdx].concat('</div>');
        for (i=0; i< html.length; i++) {
            console.log('HTML: '+html[i]);
        }
        $bookidx.append(html);
        if (hglass == true)
            $(".hourglass").hide();
    });
}

function setcurpage(idx, value)
{
    //console.log("Selected page: " + idx + ", value: " + value);
    var oldval = $('#curpage').val();
    var newval = idx;

    if (newval != oldval) {
        console.log("Changed cur page from "+oldval+" to " + newval);
        $('#curpage').val(newval).trigger('change');
    }
}

function browse(bname){
    var newwin="target=\"_blank\"";
    window.open('/books/browse/' + encodeURIComponent(bname));
}

function doexplore(wlparams, cmd)
{   
        var formparams = get_wlform(wlparams.wlnames, 'wlactions');
        console.log("Command is :"+cmd+"wlname is:"+wlparams.wlnames);
        console.log(serialize(formparams));
        window.open('/books/' + cmd + '?' +serialize(formparams), '_blank');
        //window.open('/books/' + cmd + '?' +formparams, '_blank');

}

function get_wlform(wlnames, formname) {
    document.getElementById('wlnames').value=wlnames;
    var formparams = get_formparams(formname);
    //console.log(formparams);
    //var formparams = $('#'+formname).serialize();
    return formparams;
}

function docmd(wlname, cmd)
{
        var formparams = get_wlform(wlname, 'wlactions');
        book_process(formparams, cmd);
      //book_process({ "wlnames": wlname }, cmd);
}


function book_process(wlparams, cmd)
{
    $(".hourglass").show();
    //console.log(wlparams);
    var $consolediv = $('#console');
    $.getJSON('/books/'+cmd+'?' + serialize(wlparams), function(data){
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
    var wlparams = { "books" : selbooks,"idx":idx };
    //console.log(wlparams);
    return wlparams;
}
