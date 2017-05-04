// Validating Empty Field first and then start capture
function startUpload()
{
    if (document.getElementById('uploadpath').value == ""){
            alert("Fill All Fields !");
    } 
    else {        
            doUpload();
            $('#bgblur').css('opacity','1');
    }
}

function updateWlWizard() {
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
function getServerInfo() {
    $.getJSON('/admin/getServerInfo', function(response) {
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
        booklist = data;
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

function getBook(hglass, bpath)
{
    console.log("in getbook");
    if (hglass == true) {
        $(".hourglass").show();
    }
    var xhr = $.getJSON('/books/get?path='+bpath).success(function(data){
        console.log("in done");
        $('#bookdetails').val(JSON.stringify(data, null, 2));
        console.log(data);
        var html = [];
        var itemIdx = 0;
        data = data.result;
        html.push('<div id="item'+itemIdx+'" class="item active"> <div class="row-fluid">');
        data.children.forEach(function (pageNode, index) {
            var page = pageNode.content;
        	console.log(pageNode, page);
            var size = 0;
            var thumbpath = "";
            if (page.thumbpath !== undefined && page.thumbpath != null) {
                thumbpath = page.thumbpath;
            } else {
                thumbpath = page.path;
            }
            html[itemIdx] = html[itemIdx].concat(
            '<div data-target="#carousel" data-slide-to="'+index+'" class="col-sm-2">\
            <a href="#x" class="thumb">\
	            <img id="thumb'+index+'" \
	            src="/books/page/image/'+thumbpath+'" \
	            attr-display="/books/page/image/'+page.path+'" \
	            oid="'+index+'">\
            </a>\
            </div>');
    //            var html = '<tr><td onclick="setcurpage(this.id, this.innerHTML)" id="' + i + '">' + page['fname'] + '</td></tr>';
            if ((index>1) && ((index+1)%6 == 0) && (index != (pages.length-1))) {
                html[itemIdx] = html[itemIdx].concat('</div> </div>');
                itemIdx++;
                html.push('<div id="item'+itemIdx+'" class="item">');
            }
	        html[itemIdx] = html[itemIdx].concat('</div>');
        });
		console.log('HTML: ', html);

        $('#bookidx').empty();
        $('#bookidx').append(html);
    }).fail(function (jqXHR, textStatus, errorThrown) {
        console.log("Fie! something went wrong. ", textStatus, errorThrown, jqXHR)
    }).complete(function () {
        console.log("in complete")
        if (hglass == true) {
            $(".hourglass").hide();
        }
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
        var formparams = getWlForm(wlparams.wlnames, 'wlactions');
        console.log("Command is :"+cmd+"wlname is:"+wlparams.wlnames);
        console.log(serialize(formparams));
        window.open('/books/' + cmd + '?' +serialize(formparams), '_blank');
        //window.open('/books/' + cmd + '?' +formparams, '_blank');

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
            getBooks(true)
        },1000);
        
    });
}


function getSelBooks(table, isAll)
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
