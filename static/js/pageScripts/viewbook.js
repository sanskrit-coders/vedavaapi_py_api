//var canvas = document.getElementById('pageCanvas');
var container = document.getElementById('container');
//container.appendChild(canvas);
//var context = canvas.getContext('2d');

window.cState = undefined;
var curpage_annotations = {};
var curpage_sections = {};
var viewBookState = {};
viewBookState.curpage = 1;

getBook(true, bpath);
console.log("Get Book Returned");

pramukhIME.addLanguage(PramukhIndic,"sanskrit");
pramukhIME.enable();

function changeMode(mode='Edit') {
    document.getElementById("modeButton").innerHTML = '<b><u>'+mode+' </u></b><span class="caret"></span>';
    if (mode == 'Edit') {
        document.getElementById("modeButton").flag = "E";
    } else if (mode == 'Review') {
        document.getElementById("modeButton").flag = "R";
    } else if (mode == 'Section') {
        document.getElementById("modeButton").flag = "S";
    } else {
        document.getElementById("modeButton").flag = "N";
    }
	window.cState.changeMode(document.getElementById("modeButton").flag);
}

function segmentPage() {
    window.cState.segmentPage();
}

function saveData() {
    window.cState.saveShapes();
}

function accept() {
    window.cState.accept();
}

function zoomIn() {
    window.cState.zoomIn();
    document.getElementById("scale").innerHTML = parseFloat(window.cState.scale).toFixed(1);
}

function zoomOut() {
    window.cState.zoomOut();
    document.getElementById("scale").innerHTML = parseFloat(window.cState.scale).toFixed(1);
}

function reparse_page() {
    loadpage(true);
}

function segment_page() {

    var curpage = viewBookState.curpage;
    if (curpage == undefined)
        return;
    var bookdetails = viewBookState.bookdetails;
    var pagedetails = bookdetails.result.children[curpage].content;
    var anno_id = pagedetails['anno'];
    var sec_id = pagedetails['sections'];

    $.getJSON('/books/page/anno/segment/'+anno_id, function(data){
        if (! processStatus(data))
            return;
//        console.log("Page Anno: " + JSON.stringify(data.result));
        curpage_annotations = data.result['anno'];
    });
    loadpage(true);
}

function getBook(hglass, bpath)
{
    console.log("in getbook");
    if (hglass == true) {
        $(".hourglass").show();
    }
    var xhr = $.getJSON('/books/get?path='+bpath).success(function(data){
        console.log("in done");
        viewBookState.bookdetails = data;
        viewBookState.curpage = 0;
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
//            TODO: Separate out the below.
    //            var html = '<tr><td onclick="setcurpage(this.id, this.innerHTML)" id="' + i + '">' + page['fname'] + '</td></tr>';
            if ((index>1) && ((index+1)%6 == 0) && (index != (data.children.length-1))) {
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
    var oldval = viewBookState.curpage;
    var newval = idx;

    if (newval != oldval) {
        console.log("Changed cur page from "+oldval+" to " + newval);
        viewBookState.curpage = newval;
    }
}

function loadpage(reparse = false) {
    var curpage = viewBookState.curpage;
    if (curpage == undefined)
        return;
    console.log("Loading page " + curpage);
    var bookdetails = viewBookState.bookdetails;
    console.log("Book Details: " + JSON.stringify(bookdetails));
    var pagedetails = bookdetails.result.children[curpage].content;
    console.log(pagedetails);
    pgname = pagedetails['fname'];
    var fpath = bpath + "/" + pgname;
    console.log("Loading page path: " + fpath);
    var anno_id = pagedetails['anno'];
    var sec_id = pagedetails['sections'];
    window.cState = canvasStateList.get('pageCanvas',"",curpage);
    window.cState.anno_id = anno_id;

    params = { 'reparse' : reparse };
    $.getJSON('/books/page/anno/'+anno_id+'?' + serialize(params), function(data){
        if (! processStatus(data))
            return;
//        console.log("Page Anno: " + JSON.stringify(data.result));
        curpage_annotations = data.result['anno'];
        window.cState = init('pageCanvas','/books/page/image/'+fpath,
            curpage_annotations, curpage);
        console.log(window.cState);
    });

    $.getJSON('/books/page/sections?id='+sec_id, function(data){
        if (! processStatus(data))
            return;
        curpage_sections = data;
    });
}

function slideTo(where) {
    var curpage = viewBookState.curpage;
    if (curpage == undefined) {
        console.log("curpage not defined. returning");
        return;
    }
    if (where.toLowerCase() == 'next') {
        console.log("Curpage = "+curpage);
        var newpage = parseInt(curpage) + 1;
        console.log("Nextpage = "+newpage);
        console.log("Next called is "+$('#thumb'+newpage).parent().html());
    } else {
        console.log("Curpage = "+curpage);
        var newpage = parseInt(curpage) - 1;
        console.log("Prevpage = "+newpage);
        console.log("Prev called is "+$('#thumb'+newpage).parent().html());
    }
    var attrDisplay = $('#thumb'+newpage).attr("attr-display");
    var oid = $('#thumb'+newpage).attr("oid");
    if (attrDisplay == undefined || oid == undefined) {
        console.log("Reached the end or start");
        return;
    }
    window.cState = canvasStateList.add('pageCanvas', attrDisplay, oid);
    window.cState = canvasStateList.moveTo(window.cState.name);
    setcurpage(oid, attrDisplay);
    loadpage();
}

var canvasStateList = new CanvasStateList();

$(document).ready(function () {
    console.log("In ready function.");
    $('#thumbcarousel').carousel({
        interval: false
    });

    $('body').on('click','img',function(){
        console.log("Click called on "+$(this).parent().html());
        var attrDisplay = $(this).attr("attr-display");
        var oid = $(this).attr("oid");
        window.cState = canvasStateList.add('pageCanvas', attrDisplay, oid);
        window.cState = canvasStateList.moveTo(window.cState.name);
        setcurpage(oid, attrDisplay);
        loadpage();
    });
});

document.onkeypress = function (e) {
//        e = e || window.event;//Get event
    if (e.ctrlKey && e.shiftKey) {
        var c = e.which || e.keyCode;//Get key code
        console.log("You pressed Ctrl+Shift+"+c);
        switch (c) {
            case 80://Block Ctrl+Shift+'S'
                reparse_page();
                e.preventDefault();
                e.stopPropagation();
                break;
            case 83://Block Ctrl+Shift+'S'
                saveData();
                e.preventDefault();
                e.stopPropagation();
                break;
            case 187://Block Ctrl+Shift+'+'
                zoomIn();
                e.preventDefault();
                e.stopPropagation();
                break;
            case 189://Block Ctrl+Shift+'-'
                zoomOut();
                e.preventDefault();
                e.stopPropagation();
                break;
        }
    }
};


