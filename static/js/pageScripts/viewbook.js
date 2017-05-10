'use strict';

//var canvas = document.getElementById('pageCanvas');
var container = document.getElementById('container');
//container.appendChild(canvas);
//var context = canvas.getContext('2d');

var canvasStateList = new CanvasStateList();

var curpage_annotations = {};
var curpage_sections = {};
var viewBookState = {};
viewBookState.canvasState = undefined;
viewBookState.curpage = 1;

$(document).ready(function () {
    console.log("In ready function.");
    $('#thumbcarousel').carousel({
        interval: false
    });
    $('body').on('click','img',function(){
        console.log("Click called on "+$(this).parent().html());
        var attrDisplay = $(this).attr("attr-display");
        var oid = $(this).attr("oid");
        viewBookState.canvasState = canvasStateList.add('pageCanvas', attrDisplay, oid);
        viewBookState.canvasState = canvasStateList.moveTo(viewBookState.canvasState.name);
        setcurpage(oid, attrDisplay);
    });
    getBook(true, $.query.get('_id'));
    console.log("Get Book Returned");

    pramukhIME.addLanguage(PramukhIndic,"sanskrit");
    pramukhIME.enable();

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


function changeMode(mode) {
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
	viewBookState.canvasState.changeMode(document.getElementById("modeButton").flag);
}

function segmentPage() {
    viewBookState.canvasState.segmentPage();
}

function saveData() {
    viewBookState.canvasState.saveShapes();
}

function accept() {
    viewBookState.canvasState.accept();
}

function zoomIn() {
    viewBookState.canvasState.zoomIn();
    document.getElementById("scale").innerHTML = parseFloat(viewBookState.canvasState.scale).toFixed(1);
}

function zoomOut() {
    viewBookState.canvasState.zoomOut();
    document.getElementById("scale").innerHTML = parseFloat(viewBookState.canvasState.scale).toFixed(1);
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

    $.getJSON('/api_v1/page/anno/segment/'+anno_id, function(data){
        if (! processStatus(data))
            return;
//        console.log("Page Anno: " + JSON.stringify(data.result));
        curpage_annotations = data.result['anno'];
    });
    loadpage(true);
}

function getBook(hglass, bookId)
{
    console.log("in getbook");
    if (hglass == true) {
        $(".hourglass").show();
    }
    var xhr = $.getJSON('/api_v1/books/'+bookId).success(function(data){
        console.log("in done");
        viewBookState.bookdetails = data.result;
        setcurpage(0);
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
    loadpage();
}

function loadpage(reparse) {
    var curpage = viewBookState.curpage;
    console.log("Loading page " + curpage);
    if (curpage == undefined) {
        console.log(curpage)
        return;
    }
    var bookdetails = viewBookState.bookdetails;
    console.log("Book Details: " + JSON.stringify(bookdetails));
    var pagedetails = bookdetails.children[curpage].content;
    console.log(pagedetails);
    var fpath = pagedetails.path;
    console.log("Loading page path: " + fpath);
    viewBookState.canvasState = canvasStateList.get('pageCanvas',"",curpage);
//     viewBookState.canvasState.anno_id = anno_id;
    var params = { 'reparse' : reparse };
//     $.getJSON('/api_v1/page/anno/'+anno_id+'?' + serialize(params), function(data){
//         if (! processStatus(data))
//             return;
// //        console.log("Page Anno: " + JSON.stringify(data.result));
//         curpage_annotations = data.result['anno'];
//         viewBookState.canvasState = init('pageCanvas','/api_v1/page/image/'+fpath,
//             curpage_annotations, curpage);
//         console.log(viewBookState.canvasState);
//     });

//     var sec_id = pagedetails['sections'];
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
    viewBookState.canvasState = canvasStateList.add('pageCanvas', attrDisplay, oid);
    viewBookState.canvasState = canvasStateList.moveTo(viewBookState.canvasState.name);
    setcurpage(oid, attrDisplay);
}

