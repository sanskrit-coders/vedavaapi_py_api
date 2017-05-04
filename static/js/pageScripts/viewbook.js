
//var canvas = document.getElementById('pageCanvas');
var container = document.getElementById('container');
//container.appendChild(canvas);
//var context = canvas.getContext('2d');

window.cState = undefined;
var curpage_annotations = {};
var curpage_sections = {};
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

    var curpage = $('#curpage').val();
    if (curpage == undefined)
        return;
    var details = $('#bookdetails').val();
    var bookdetails = JSON.parse(details);
    var pagedetails = bookdetails['result']['pages'][curpage];
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

function loadpage(reparse = false) {
    var curpage = $('#curpage').val();
    if (curpage == undefined)
        return;
    console.log("Loading page " + curpage);
    var details = $('#bookdetails').val();
    console.log("Details: " + details);
    var bookdetails = JSON.parse(details);
    console.log("Book Details: " + JSON.stringify(bookdetails));
    var pagedetails = bookdetails['result']['pages'][curpage];
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
    var curpage = $('#curpage').val();
    if (!curpage) {
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

    $('#curpage').change(function() {
//            loadpage();
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


