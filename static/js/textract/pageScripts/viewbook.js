'use strict';

var canvasStateList = new CanvasStateList();

var viewBookState = {};
viewBookState.canvasState = undefined;
viewBookState.curpage = 1;

$(document).ready(function () {
    console.log("In ready function.");
    getBook(true, $.query.get('_id'));
    console.log("Get Book Returned");
});

document.onkeypress = function (e) {
//        e = e || window.event;//Get event
    if (e.ctrlKey && e.shiftKey) {
        var c = e.which || e.keyCode;//Get key code
        console.log("You pressed Ctrl+Shift+" + c);
        switch (c) {
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
    document.getElementById("modeButton").innerHTML = '<b><u>' + mode + ' </u></b><span class="caret"></span>';
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

    var curpage = viewBookState.curpage;
    var bookdetails = viewBookState.bookdetails;
    var pagedetails = bookdetails.children[curpage].content;

    $.getJSON('/textract/v1/pages/' + pagedetails._id + '/image_annotations/all', function (data) {
        console.log("Page Anno: ", data);
        loadpage(data);
    });
}

function saveData() {
    var curpage = viewBookState.curpage;
    var bookdetails = viewBookState.bookdetails;
    var pagedetails = bookdetails.children[curpage].content;
    viewBookState.canvasState.saveAnnotations(pagedetails._id);
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

function getBook(hglass, bookId) {
    console.log("in getbook");
    if (hglass == true) {
        $(".hourglass").show();
    }
    var xhr = $.getJSON('/textract/v1/books/' + bookId).success(function (data) {
        console.log("in done");
        viewBookState.bookdetails = data;
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

function setcurpage(idx) {
    //console.log("Selected page: " + idx + ", value: " + value);
    var oldval = viewBookState.curpage;
    var newval = idx;

    if (newval != oldval) {
        console.log("Changed cur page from " + oldval + " to " + newval);
        viewBookState.curpage = newval;
    }
    loadpage();
}

function loadpage(annotationNodes) {
    var curpage = viewBookState.curpage;
    console.log("Loading page " + curpage);
    if (curpage == undefined) {
        console.log(curpage)
        return;
    }
    var bookdetails = viewBookState.bookdetails;
    // console.log("Book Details: ", bookdetails);
    var pagedetails = bookdetails.children[curpage].content;
    console.log(pagedetails);
    var fpath = "/textract/relpath/" + pagedetails.path;
    console.log("Loading page path: ", fpath);
    viewBookState.canvasState = canvasStateList.add('pageCanvas', fpath, curpage);
    viewBookState.canvasState = canvasStateList.moveTo(viewBookState.canvasState.name);
    if (annotationNodes != undefined) {
        viewBookState.canvasState.setAnnotations(annotationNodes);
    }
    viewBookState.canvasState.draw();
}

function slideTo(where) {
    var curpage = viewBookState.curpage;
    if (curpage == undefined) {
        console.log("curpage not defined. returning");
        return;
    }
    console.log("Curpage = ", curpage);
    if (where.toLowerCase() == 'next') {
        var newpage = parseInt(curpage) + 1;
    } else {
        var newpage = parseInt(curpage) - 1;
    }
    console.log("Nextpage = ", newpage);

    if (newpage < 0 || newpage >= viewBookState.bookdetails.children.length) {
        console.log("Reached the end or start ", newpage);
        return;
    } else {
        setcurpage(newpage);
    }
}

function makeImageAnnotation(rectangle) {
    var curpage = viewBookState.curpage;
    var bookdetails = viewBookState.bookdetails;
    var pagedetails = bookdetails.children[curpage].content;
    return {
        "py/object": "textract.backend.data_containers.ImageAnnotation",
        "source": {
            "py/object": "textract.backend.data_containers.AnnotationSource",
            "type": "user_supplied",
            "id": "UNK"
        },
        "targets": [
            {
                "py/object": "textract.backend.data_containers.ImageTarget",
                "container_id": pagedetails._id,
                "rectangle": {
                    "py/object": "textract.backend.data_containers.Rectangle",
                    "h": rectangle.h,
                    "w": rectangle.w,
                    "y1": rectangle.y,
                    "x1": rectangle.x
                }
            }
        ]
    };
}

function makeJsonObjectNode(jsonObject) {
    return {
        "py/object": "common.data_containers.JsonObjectNode",
        "content": jsonObject,
        "children": []
    };
}

function makeTextAnnotation(text) {
    return {
        "py/object": "textract.backend.data_containers.TextAnnotation",
        "source": {
            "py/object": "textract.backend.data_containers.AnnotationSource",
            "type": "user_supplied",
            "id": "UNK"
        },
        "content": {
            "py/object": "textract.backend.data_containers.TextContent",
            "text": text
        }
    }
}

function addDetails() {
    // $("#divDetailedAnnotations").css("display", "block");
    alert("Not implemented");
}

function divDetailedAnnotationsDone() {

    $("#divDetailedAnnotations").css("display", "none");
}

function divDetailedAnnotationsCancel() {

    $("#divDetailedAnnotations").css("display", "none");
}
