// Initially based on (likely) https://github.com/simonsarris/Canvas-tutorials/blob/master/shapes.js By Simon Sarris, modified heavily by deshmup.

// Constructor for Shape objects to hold data for all drawn objects.
// For now they will just be defined as rectangles.
function Shape(x, y, w, h, fill, obj) {
    /*
     This is a very simple and unsafe constructor. All we're doing is checking
     if the values exist. "x || 0" just means "if there is a value for x, use
     that. Otherwise use 0." But we aren't checking anything else! We could
     put "Lalala" for the value of x. stroke is hardcodes, can be passed as arg.
     */
    this.x = x || 0;
    this.y = y || 0;
    this.w = w || 30;
    this.h = h || 30;
    this.fill = fill || 'rgba(0,255,0,.2)';
    this.stroke = '#FFFF00';
    this.fontType = 'normal';
    this.fontPoints = this.h - 10;
    this.fontName = 'Arial Unicode MS';
    this.font = this.fontType + " " + this.fontPoints + "pt " + this.fontName;
    this.fillStyle = 'black';
    this.text = '';
    this.state = 'user_supplied';
    this.displayTextAbove = false;
    // Handle Object
    if (obj instanceof Object) {
        for (var attr in obj) {
            if (obj.hasOwnProperty(attr)) {
                this[attr] = obj[attr];
            }
        }
    }
}

Shape.prototype = {
    // Draws this shape to a given context with different stroke and fill
    draw: function (ctx) {
        if (this.state == "system_inferred") {
            this.stroke = 'rgba(255,0,0,1)';
            this.fill = 'rgba(0,255,0,.3)';
        } else if (this.state == "user_accepted") {
            this.stroke = 'rgba(255,255,0,0)';
            this.fill = 'rgba(0,255,255,.3)';
        } else if (this.state == "user_supplied") {
            this.stroke = 'rgba(255,255,0,1)';
            this.fill = 'rgba(0,255,0,.3)';
        } else if (this.state == "user_deleted") {
            // Dont draw
            return;
        }
        if (this.displayTextAbove == true) {
            this.stroke = 'rgba(255,255,0,1)';
            this.fill = 'rgba(0,255,0,.1)';
        }
        ctx.strokeStyle = this.stroke;
        ctx.beginPath();
        ctx.rect(this.x, this.y, this.w, this.h);
        ctx.stroke();
        ctx.fillStyle = this.fill;
        ctx.fill();
        // Text x,y starts from bottom left, whereas rectangle from top left
        ctx.font = this.font;
        ctx.fillStyle = this.fillStyle;
        if (this.displayTextAbove == true) {
            ctx.fillText(this.text, this.x, this.y);
        } else {
            ctx.fillText(this.text, this.x, this.y + this.fontPoints + 4);
        }
    },

    print: function () {
        var message = "";
        for (var attr in this) {
            if (this.hasOwnProperty(attr)) {
                message = message.concat("{" + attr + ":" + this[attr] + "}");
            }
        }
        console.log(message);
    },

    // increment the text font size
    increaseFont: function () {
        this.fontPoints++;
        this.font = this.fontType + " " + this.fontPoints + "pt " + this.fontName;
        this.print();
        return this.fontPoints;
    },

    // decrement the text font size
    decreaseFont: function () {
        this.fontPoints--;
        this.font = this.fontType + " " + this.fontPoints + "pt " + this.fontName;
        this.print();
        return this.fontPoints;
    },

    // text display above for review
    toggleDisplayText: function () {
        if (this.displayTextAbove == true) {
            this.displayTextAbove = false;
        } else {
            this.displayTextAbove = true;
        }
    },

    // text display should reset to the box
    resetDisplayText: function () {
        this.displayTextAbove = false;
    },

    // change state of the shape
    getState: function () {
        return this.state;
    },

    // change state of the shape
    changeStateTo: function (newState) {
        this.state = newState;
    },

    // Determine if a point is inside the shape's bounds
    contains: function (mx, my) {
        // All we have to do is make sure the Mouse X,Y fall in the area between
        // the shape's X and (X + Width) and its Y and (Y + Height)
        return (this.x < mx) && (this.x + this.w > mx) &&
            (this.y < my) && (this.y + this.h > my);
    },

    // Determine if a point is inside the shape's borders.
    atBorders: function (mx, my) {
        // All we have to do is make sure the Mouse X,Y fall in the area
        // segment around the four corners with certain distance.
        var distance = Math.round(this.h / 5);
        // currently only bottom right corner is enabled (To be enhanced)
        return (this.atBottomRight(mx, my, distance));
    },

    // Determine if a point is inside the shape's bottom-right boundary within a
    // sqare shape of hight and width equal to distance
    atBottomRight: function (mx, my, distance) {
        // All we have to do is make sure the Mouse X,Y fall in the area between
        // the squares X and (X + Width) and its Y and (Y + Height)
        var newx = this.x + this.w - distance;
        var newy = this.y + this.h - distance;
        var neww = distance;
        var newh = distance;

        return (newx < mx) && (newx + neww > mx) &&
            (newy < my) && (newy + newh > my);
    },

};

function CanvasStateList() {
    this.csList = [];
    this.curCanvasState = null;
    this.interval = 30;
    var myListState = this;
    setInterval(function () {
        myListState.draw();
    }, myListState.interval);
}

CanvasStateList.prototype = {
    add: function (canvasId, dataURL, oid) {
        var canvasStateName = canvasId + oid;
        console.log("Add: Canvas Id " + canvasId + " oid " + oid);
        if (typeof this.csList[canvasStateName] !== "undefined" &&
            this.csList[canvasStateName] !== null) {
            console.log("Add: Canvas " + canvasStateName + " already added");
            return this.csList[canvasStateName];
        } else {
            this.csList[canvasStateName] = new CanvasState(canvasId, dataURL, oid);
            return this.csList[canvasStateName];
        }
    },
    get: function (canvasId, dataURL, oid) {
        var canvasStateName = canvasId + oid;
        console.log("Get: Canvas Id " + canvasId + " oid " + oid);
        if (typeof this.csList[canvasStateName] !== "undefined" &&
            this.csList[canvasStateName] !== null) {
            console.log("Get: Canvas " + canvasStateName + " found");
            return this.csList[canvasStateName];
        } else {
            console.log("Get: Canvas " + canvasStateName + " not found");
            return null;
        }
    },
    moveTo: function (canvasStateName) {
        if (typeof this.csList[canvasStateName] !== "undefined" &&
            this.csList[canvasStateName] !== null) {
            if (this.curCanvasState !== null) {
                this.curCanvasState.active = false;
            }
            this.curCanvasState = this.csList[canvasStateName];
            this.curCanvasState.active = true;
            this.curCanvasState.canvasContainer.scrollLeft = this.curCanvasState.containerScrollLeft;
            this.curCanvasState.canvasContainer.scrollTop = this.curCanvasState.containerScrollTop;
            this.curCanvasState.valid = false;
            console.log(this.curCanvasState);
            return this.curCanvasState;
        } else {
            console.log("MoveTo: Canvas " + canvasStateName + " does not exist");
            return null;
        }
    },
    delete: function (canvasStateName) {
        if (typeof this.csList[canvasStateName] !== "undefined" &&
            this.csList[canvasStateName] !== null) {
            delete this.csList[canvasStateName];
        } else {
            console.log("Delete: Canvas " + canvasStateName + " does not exist");
        }
    },
    draw: function () {
        if (this.curCanvasState !== null) {
            this.curCanvasState.draw();
        }
    },
};

function CanvasState(canvasId, dataURL, oid) {
    // **** First some setup! ****
    this.name = canvasId + oid;
    this.active = false;
    this.INPUT_WIDTH = 90;
    this.INPUT_HEIGHT = 24;
    this.INPUT_FONT_SIZE = 20;
    canvas = document.getElementById(canvasId);
    this.inputText = new CanvasInput({
        canvas: document.getElementById(canvasId),
        width: this.INPUT_WIDTH,
        height: this.INPUT_HEIGHT,
        fontSize: this.INPUT_FONT_SIZE,
        padding: 0,
        borderWidth: 0,
        borderRadius: 0,
        onsubmit: function () {
            if (myState.selection) {
                myState.handleOnSubmit();
            } else {
                alert("First select the area");
            }
        },
    });
    this.canvas = canvas;
    this.canvasContainer = canvas.parentElement;
    this.width = canvas.width;
    this.height = canvas.height;
    this.ctx = this.canvas.getContext('2d');
    this.imageURL = dataURL;
    this.oid = oid;
    this.anno_id = "0";
    // This complicates things a little but but fixes mouse co-ordinate problems
    // when there's a border or padding. See getMouse for more detail
    var stylePaddingLeft, stylePaddingTop, styleBorderLeft, styleBorderTop;
    if (document.defaultView && document.defaultView.getComputedStyle) {
        this.stylePaddingLeft = parseInt(document.defaultView.getComputedStyle(canvas, null)['paddingLeft'], 10) || 0;
        this.stylePaddingTop = parseInt(document.defaultView.getComputedStyle(canvas, null)['paddingTop'], 10) || 0;
        this.styleBorderLeft = parseInt(document.defaultView.getComputedStyle(canvas, null)['borderLeftWidth'], 10) || 0;
        this.styleBorderTop = parseInt(document.defaultView.getComputedStyle(canvas, null)['borderTopWidth'], 10) || 0;
    }
    // Some pages have fixed-position bars (like the stumbleupon bar) at the 
    // top or left of the page. They will mess up mouse coordinates and this 
    // fixes that
    var html = document.body.parentNode;
    this.htmlTop = html.offsetTop;
    this.htmlLeft = html.offsetLeft;

    // **** Keep track of state! ****

    this.mode = "E"; // Initializing with "E" edit mode. ("E"|"R"|"N"|"S") 
    this.scale = 1; // Initialize with scale as 1 (range is 0.1 - 1.0) 
    this.scrollX = 0;
    this.scrollY = 0;

    this.valid = false; // when set to false, the canvas will redraw everything
    this.shapes = [];  // the collection of things to be drawn
    this.containerScrollLeft = 0;
    this.containerScrollTop = 0;
    this.dragForScrolling = false;  // True when mouse down in canvas 
                                    // without any selection 
    this.dragForScrollingX = 0; // X position when mouse was moved down 
    this.dragForScrollingY = 0; // Y position when mouse was moved down 
    this.dragging = false; // Keep track of when we are dragging
    this.dragForResizing = false; // Keep track of when we are dragging 
                                  // for resizing

    // the current selected object. In the future we could turn this into an 
    // array for multiple selection
    this.selection = null;
    this.selectionIndex = null;
    this.dragoffx = 0; // See mousedown and mousemove events for explanation
    this.dragoffy = 0;

    // **** Then events! ****

    // This is an example of a closure!
    // Right here "this" means the CanvasState. But we are making events on the 
    // Canvas itself, and when the events are fired on the canvas the variable 
    // "this" is going to mean the canvas!. Since we still want to use this 
    // particular CanvasState in the events we have to save a reference to it.
    // This is our reference!
    var myState = this;

    // fixes a problem where double clicking causes text to get selected on the 
    // canvas
    canvas.addEventListener('selectstart', function (e) {
        e.preventDefault();
        return false;
    }, false);

    // Up, down, and move are for dragging
    canvas.addEventListener('mousedown', function (e) {
        if (!myState.active) {
            return;
        }
        var mouse = myState.getMouse(e);
        var mx = mouse.x;
        var my = mouse.y;
        var shapes = myState.shapes;
        var l = shapes.length;
        for (var i = l - 1; i >= 0; i--) {
            if (shapes[i].contains(mx, my)) {
                var mySel;
                if (myState.selection && myState.selection.contains(mx, my)) {
                    mySel = shapes[myState.selectionIndex];
                    if (myState.mode == "R") {
                        if (mySel.state != "user_accepted") {
                            mySel.toggleDisplayText();
                        }
                    }
                } else { // Selection of differnt rectangle
                    mySel = shapes[i];
                    if (myState.mode == "R") {
                        if (myState.selection) {
                            myState.selection.resetDisplayText();
                        }
                        if (mySel.state != "user_accepted") {
                            mySel.toggleDisplayText();
                        }
                    }
                    myState.selection = mySel;
                    myState.selectionIndex = i;
                }
                // Keep track of where in the object we clicked
                // so we can move it smoothly (see mousemove)
                myState.dragoffx = mx - mySel.x;
                myState.dragoffy = my - mySel.y;
                myState.dragging = true;
                if (mySel.atBorders(mx, my)) {
                    myState.dragForResizing = true;
                    this.style.cursor = 'se-resize';
                }
                myState.scrollX = Math.round(window.scrollX);
                myState.scrollY = Math.round(window.scrollY);

                if (myState.mode == "E") {
                    myState.changeInputLocation(myState.selection);
                }

                myState.valid = false;
                return;
            }
        }
        // havent returned means we have failed to select anything.
        // If there was an object selected, we deselect it
        if (myState.selection && (!myState.inputTextContains(mx, my))) {
            console.log("Deselecting - MX: " + mx + " MY: " + my);
            if (myState.mode == "R") {
                myState.selection.resetDisplayText();
            }
            myState.selection = null;
            myState.selectionIndex = null;
            myState.scrollX = Math.round(window.scrollX);
            myState.scrollY = Math.round(window.scrollY);
            myState.valid = false; // Need to clear the old selection border
        }
        if (!myState.dragForResizing && !myState.dragging) {
            myState.scrollX = Math.round(window.scrollX);
            myState.scrollY = Math.round(window.scrollY);
            /**
             myState.dragForScrolling = true;
             myState.dragForScrollingX = e.pageX;
             myState.dragForScrollingY = e.pageY;
             */
            myState.valid = false; // Need to move the canvas 
        }
    }, true);

    canvas.addEventListener('mousemove', function (e) {
        if (!myState.active) {
            return;
        }
        e.preventDefault();
        if (myState.dragging) {
            var mouse = myState.getMouse(e);
            if (!myState.dragForResizing) {
                // We don't want to drag the object by its top-left corner,
                // we want to drag it from where we clicked. Thats why we
                // saved the offset and use it here
                myState.selection.x = mouse.x - myState.dragoffx;
                myState.selection.y = mouse.y - myState.dragoffy;
            } else {
                // Not allowing the selection to go -ve and keeping the min
                // size of rectangle as 15.
                if ((mouse.x - myState.selection.x) > 15 &&
                    (mouse.y - myState.selection.y) > 15) {
                    myState.selection.w = mouse.x - myState.selection.x;
                    myState.selection.h = mouse.y - myState.selection.y;
                }
            }
            myState.scrollX = Math.round(window.scrollX);
            myState.scrollY = Math.round(window.scrollY);
            myState.valid = false; // Something's dragging so we must redraw
        } else if (myState.selection) {
            var mouse = myState.getMouse(e);
            var mx = mouse.x;
            var my = mouse.y;
            if (myState.selection.atBorders(mx, my)) {
                this.style.cursor = 'se-resize';
            } else {
                this.style.cursor = 'auto';
            }
        } else if (myState.dragForScrolling) {
            /*
             this.style.cursor = 'all-scroll';
             var leftMove = myState.canvasContainer.scrollLeft;
             var topMove = myState.canvasContainer.scrollTop;

             console.log("1.Scrolling Div To"+ leftMove+" "+ topMove);

             leftMove += (myState.dragForScrollingX - e.pageX);
             if (leftMove < 0 ) {
             leftMove = 0;
             }
             console.log("2.Scrolling Div To"+ leftMove+" "+ topMove);

             if (leftMove > (myState.canvasContainer.scrollWidth - myState.canvasContainer.clientWidth)) {
             leftMove = myState.canvasContainer.scrollWidth - myState.canvasContainer.clientWidth;
             }
             leftMove = Math.round(leftMove);

             topMove += (myState.dragForScrollingY - e.pageY);
             if (topMove < 0 ) {
             topMove = 0;
             }
             if (topMove > (myState.canvasContainer.scrollHeight - myState.canvasContainer.clientHeight)) {
             topMove = myState.canvasContainer.scrollHeight - myState.canvasContainer.clientHeight;
             }
             topMove = Math.round(topMove);

             myState.dragForScrollingX = e.pageX;
             myState.dragForScrollingY = e.pageY;
             myState.canvasContainer.scrollLeft = leftMove;
             myState.canvasContainer.scrollTop = topMove;
             myState.containerScrollLeft = leftMove;
             myState.containerScrollTop = topMove;
             console.log("Scrolling Div To"+ leftMove+" "+ topMove);

             myState.valid = false; // Something's dragging so we must redraw
             */
        }
    }, true);

    canvas.addEventListener('mouseup', function (e) {
        if (!myState.active) {
            return;
        }
        if (myState.dragForScrolling) {
            /*
             var leftMove = myState.canvasContainer.scrollLeft;
             var topMove = myState.canvasContainer.scrollTop;

             leftMove += (myState.dragForScrollingX - e.pageX);
             if (leftMove < 0 ) {
             leftMove = 0;
             }
             if (leftMove > (myState.canvasContainer.scrollWidth - myState.canvasContainer.clientWidth)) {
             leftMove = myState.canvasContainer.scrollWidth - myState.canvasContainer.clientWidth;
             }
             leftMove = Math.round(leftMove);

             topMove += (myState.dragForScrollingY - e.pageY);
             if (topMove < 0 ) {
             topMove = 0;
             }
             if (topMove > (myState.canvasContainer.scrollHeight - myState.canvasContainer.clientHeight)) {
             topMove = myState.canvasContainer.scrollHeight - myState.canvasContainer.clientHeight;
             }
             topMove = Math.round(topMove);

             myState.dragForScrollingX = e.pageX;
             myState.dragForScrollingY = e.pageY;
             myState.canvasContainer.scrollLeft = leftMove;
             myState.canvasContainer.scrollTop = topMove;
             myState.containerScrollLeft = leftMove;
             myState.containerScrollTop = topMove;
             console.log("Scrolling Div To"+ leftMove+" "+ topMove);
             myState.valid = false; // Something's dragging so we must redraw
             */
        }
        if (myState.selection) {
            myState.changeInputLocation(myState.selection);
        }
        myState.valid = false;
        myState.dragging = false;
        myState.dragForResizing = false;
//        myState.dragForScrolling = false; 
        this.style.cursor = 'auto';
    }, true);

    // double click for making new shapes
    canvas.addEventListener('dblclick', function (e) {
        if (!myState.active) {
            return;
        }
        var mouse = myState.getMouse(e);
        // To keep the rectangle of same size, we would need to scale up the 
        // rectangle by the amount the image is scaled down
        var width = Math.round(30 / myState.scale);
        var height = Math.round(30 / myState.scale);
        myState.addShape(new Shape(mouse.x - width / 2, mouse.y - height / 2,
            width, height, 'rgba(0,255,0,.3)'));
    }, true);

    window.addEventListener('keydown', function (e) {
        if (!myState.active) {
            return false;
        }
        var charPressed = e.which || e.keyCode;
//        console.log("You pressed Key "+charPressed);
        if (charPressed == 9) {
            myState.handleOnSubmit();
            myState.handleTab(e);
            e.preventDefault();
            e.stopPropagation();
        }
        // Undo operation called
        if (charPressed == 90 && e.ctrlKey) {
            myState.undoActivity();
            e.preventDefault();
            e.stopPropagation();
        } else if (charPressed == 89 && e.ctrlKey) {
            myState.redoActivity();
            e.preventDefault();
            e.stopPropagation();
        }

        // Alt+up/down should hide and unhide the inputText bar
        if ((charPressed == 40 || charPressed == 38) && e.shiftKey) {
            if (myState.mode == "R") {
                return;
            } //No action taken
            if (myState.inputText.height() == 1) {
                if (myState.selection) {
                    myState.changeInputLocation(myState.selection);
                }
                myState.inputText.height(24);
                myState.inputText.width(90);
            } else {
                myState.inputText.height(1);
                myState.inputText.width(1);
            }
            myState.valid = false; // Something's changed so we must redraw
        }
        if (!myState.selection) {
            return;
        }
        if (charPressed == 39 && e.shiftKey) {
//            console.log("You pressed + key");
            myState.selection.increaseFont();
            myState.valid = false; // Something's changed so we must redraw
        } else if (charPressed == 37 && e.shiftKey) {
//            console.log("You pressed - key");
            myState.selection.decreaseFont();
            myState.valid = false; // Something's changed so we must redraw
        } else if (charPressed == 46) { // Del key triggered
//            console.log("You pressed del key");
            //removing the shape from the array
            if (myState.mode != "S") {
                var oldState = myState.selection.getState();
                myState.addActivity('StateChange', myState.selection, oldState, 'user_deleted');
                myState.selection.changeStateTo('user_deleted');
                myState.selection.resetDisplayText();
                myState.valid = false; // Something's changed so we must redraw
                e.preventDefault();
                e.stopPropagation();
            }
//            myState.shapes.splice(myState.selectionIndex,1);
//            myState.selection = null;
//            myState.selectionIndex = null;
//            myState.valid = false; // Something's deleted so we must redraw
        } else if (charPressed == 65) {
            if (myState.mode == "R") {
                var oldState = myState.selection.getState();
                myState.addActivity('StateChange', myState.selection, oldState, 'user_accepted');
                myState.selection.changeStateTo('user_accepted');
                myState.selection.resetDisplayText();
                myState.valid = false; // Something's changed so we must redraw
                e.preventDefault();
                e.stopPropagation();
            }
        } else if (charPressed == 72 && e.ctrlKey && e.shiftKey) {
            if (myState.selection.state != "user_accepted") {
                myState.selection.toggleDisplayText();
            }
            myState.valid = false; // Something's changed so we must redraw
            e.preventDefault();
            e.stopPropagation();
        } else {
            return;
        }
    }, true);

    // **** Options! ****

    this.selectionColor = '#CC0000';
    this.selectionWidth = 2;

    this.undoStack = []; // Items stores as {"Op",oldState,newShape}
    this.redoStack = []; // Items stores as {"Op",newShape,oldShape}
//    this.interval = 30;
//    setInterval(function() { myState.draw(); }, myState.interval);
}

CanvasState.prototype.handleOnSubmit = function () {
    myState = this;
    if (myState.selection) {
        myState.selection.print();
        var prevValue = myState.selection.text;
        myState.selection.text = myState.inputText.value();
//        myState.selection.fontPoints = Math.round(myState.selection.h - 5/myState.scale);
//        myState.selection.font = myState.selection.fontType+" "+myState.selection.fontPoints+"pt "+myState.selection.fontName;
        myState.valid = false;
        console.log("Prev =" + prevValue + " New=" + myState.selection.text);
        if (myState.selection.text != prevValue) {
            var oldState = myState.selection.getState();
            myState.addActivity('StateChange', myState.selection, oldState, 'user_supplied');
            myState.selection.changeStateTo('user_supplied');
        }
        myState.inputText.value('');
        myState.selection.print();
    } else {
        console.log("First select the area");
    }
}

CanvasState.prototype.handleTab = function (e) {
    myState = this;
    if (myState.selection) {
        myState.selection.resetDisplayText();
    } else {
        console.log("No selection done ");
        return false;
    }
    var prevSelection = myState.selection;
    var newSelection = prevSelection;
    do {
        if (e.shiftKey) {
            if (myState.selectionIndex == 0) {
                myState.selectionIndex = myState.shapes.length - 1;
            } else {
                myState.selectionIndex--;
            }
        } else {
            if (myState.selectionIndex == (myState.shapes.length - 1)) {
                myState.selectionIndex = 0;
            } else {
                myState.selectionIndex++;
            }
        }
        newSelection = myState.shapes[myState.selectionIndex];
    } while (newSelection.state == "user_deleted");

    myState.selection = newSelection;

    if (myState.mode == "R") {
        if (myState.selection.state != "user_accepted") {
            myState.selection.toggleDisplayText();
        }
    }
    if (myState.mode == "E") {
        myState.changeInputLocation(myState.selection);
    }

    myState.scrollX = Math.round(window.scrollX);
    myState.scrollY = Math.round(window.scrollY);
//  console.log("ScrollX = "+myState.scrollX+" ScrollY = "+myState.scrollY);

    var scrollLeft = myState.canvasContainer.scrollLeft;
    var scrollTop = myState.canvasContainer.scrollTop;
    var scrollWidth = myState.canvasContainer.scrollWidth;
    var scrollHeight = myState.canvasContainer.scrollHeight;
    var clientWidth = myState.canvasContainer.clientWidth;
    var clientHeight = myState.canvasContainer.clientHeight;
    var horizontalMove = 0;
    var verticalMove = 0;
//  console.log("ScrollHeight = "+scrollHeight+" clientHeight "+clientHeight);
//  console.log("ScrollWidth = "+scrollWidth+" clientWidth "+clientWidth);

    var hDistance = Math.abs((newSelection.x - prevSelection.x) * myState.scale);
//  console.log("H-Distance = "+hDistance);
    //Check if the new selection is on right or left of viewport
    if ((newSelection.x * myState.scale) > (scrollLeft + clientWidth)) {
        if (hDistance < (clientWidth / 4)) {
            horizontalMove = Math.min(clientWidth / 4,
                (scrollWidth - (scrollLeft + clientWidth)));
        } else if (hDistance > (clientWidth / 2)) {
            horizontalMove = Math.min((hDistance + clientWidth / 4),
                (scrollWidth - (scrollLeft + clientWidth)));
        } else {
            horizontalMove = Math.min(clientWidth / 2,
                (scrollWidth - (scrollLeft + clientWidth)));
        }
    } else if ((newSelection.x * myState.scale) < scrollLeft) {
        if (hDistance < (clientWidth / 4)) {
            horizontalMove = -(Math.min(clientWidth / 4, scrollLeft));
        } else if (hDistance > (clientWidth / 2)) {
            horizontalMove = -(Math.min((hDistance + clientWidth / 4),
                scrollLeft));
        } else {
            horizontalMove = -(Math.min(clientWidth / 2, scrollLeft));
        }
    }
    horizontalMove = Math.round(horizontalMove);

    var vDistance = Math.abs((newSelection.y - prevSelection.y) * myState.scale);
//    console.log("V-Distance = "+vDistance);
    //Check if the new selection is on top or bottom of viewport
    if ((newSelection.y * myState.scale) > (scrollTop + clientHeight)) {
        if (vDistance < (clientHeight / 4)) {
            verticalMove = Math.min(clientHeight / 4,
                (scrollHeight - (scrollTop + clientHeight)));
        } else if (vDistance > (clientHeight / 2)) {
            verticalMove = Math.min((vDistance + clientHeight / 4),
                (scrollHeight - (scrollTop + clientHeight)));
        } else {
            verticalMove = Math.min(clientHeight / 2,
                (scrollHeight - (scrollTop + clientHeight)));
        }
    } else if ((newSelection.y * myState.scale) < scrollTop) {
        if (vDistance < (clientHeight / 4)) {
            verticalMove = -(Math.min(clientHeight / 4, scrollTop));
        } else if (vDistance > (clientHeight / 2)) {
            verticalMove = -(Math.min((vDistance + clientHeight / 4),
                scrollTop));
        } else {
            verticalMove = -(Math.min(clientHeight / 2, scrollTop));
        }
    }
    verticalMove = Math.round(verticalMove);

//     console.log("Current Scroll by X: "+scrollLeft+" Y: "+scrollTop);
//     console.log("Scrolling by X: "+horizontalMove+" Y: "+verticalMove);
    myState.canvasContainer.scrollLeft = scrollLeft + horizontalMove;
    myState.canvasContainer.scrollTop = scrollTop + verticalMove;
    myState.valid = false;
    // For logging purpose only
//     scrollLeft = myState.canvasContainer.scrollLeft; 
//     scrollTop = myState.canvasContainer.scrollTop; 
//     console.log("New Scroll by X: "+scrollLeft+" Y: "+scrollTop);
}

CanvasState.prototype.addActivity = function (activityName, object, prevVal, newVal) {
    this.undoStack.push([activityName, object, prevVal, newVal]);
    this.redoStack = []; // reseting redo with any new activity
}

CanvasState.prototype.undoActivity = function () {
    if (this.undoStack.length == 0) {
        return;
    }
    var activity = this.undoStack.pop();
    var activityName = activity[0];
    var object = activity[1];
    var prevVal = activity[2];
    var newVal = activity[3];
    this.redoStack.push(activity);
    if (activityName == "StateChange") {
        if (object !== null) {
            object.changeStateTo(prevVal);
            this.valid = false;
        } else {
            console.log("undo on un-selected item");
        }
    }
}

CanvasState.prototype.redoActivity = function () {
    if (this.redoStack.length == 0) {
        return;
    }
    var activity = this.redoStack.pop();
    var activityName = activity[0];
    var object = activity[1];
    var prevVal = activity[2];
    var newVal = activity[3];
    this.undoStack.push(activity);
    if (activityName == "StateChange") {
        if (object !== null) {
            object.changeStateTo(newVal);
            this.valid = false;
        } else {
            console.log("redo on un-selected item");
        }
    }
}

CanvasState.prototype.changeInputLocation = function (selectedShape) {
    buffer = 5;
    this.inputText.x(selectedShape.x);
    scaledHeight = Math.round(this.INPUT_HEIGHT / this.scale);
    if (selectedShape.y < (scaledHeight + buffer)) {
        this.inputText.y(selectedShape.y + selectedShape.h + buffer);
    } else {
        this.inputText.y(selectedShape.y - (scaledHeight + buffer));
    }
    console.log("Shape X: " + selectedShape.x + " Y: " + selectedShape.y + " H: " + selectedShape.h + " W: " + selectedShape.w + " Ix: " + this.inputText.x() + " Iy: " + this.inputText.y() + " Ih: " + this.inputText.height() + " Iw: " + this.inputText.width());
}

// Determine if a point is inside the input text box
CanvasState.prototype.inputTextContains = function (mx, my) {
    // All we have to do is make sure the Mouse X,Y fall in the area between
    // the shape's X and (X + Width) and its Y and (Y + (Height))
    return (this.inputText.x() < mx) &&
        (this.inputText.x() + this.inputText.width() > mx) &&
        (this.inputText.y() < my) &&
        (this.inputText.y() + (this.inputText.height()) > my);
}

CanvasState.prototype.addShape = function (shape) {
    var length = this.shapes.length;
    // traversing from the back of the list. Bottom right to top left 
    for (i = length - 1; i >= 0; i--) {
        var lastShape = this.shapes[i];
        var shapeInserted = false;
        if (lastShape.x < shape.x && (Math.abs(lastShape.y - shape.y) < (lastShape.h / 2))) { // Right side on the same row
            this.shapes.splice(i + 1, 0, shape);
            shapeInserted = true;
            break;
        } else if ((shape.y - lastShape.y) > (lastShape.h / 2)) { // Next row case
            this.shapes.splice(i + 1, 0, shape);
            shapeInserted = true;
            break;
        }
    }
    if (length == 0) {
        this.shapes.push(shape);
    } else if (shapeInserted == false) { // Insert at the begining
        this.shapes.splice(0, 0, shape);
    }
    if (shape.text != '') {
        shape.print();
    }
    this.valid = false;
}

CanvasState.prototype.clear = function () {
    this.ctx.clearRect(0, 0, this.width, this.height);
}

// While draw is called as often as the INTERVAL variable demands,
// It only ever does something if the canvas gets invalidated by our code
CanvasState.prototype.draw = function () {
    if (!this.active) {
        console.log("not active, returning!");
        return;
    }
    // if our state is invalid, redraw and validate!
    if (!this.valid) {
        var ctx = this.ctx;
        var shapes = this.shapes;
        var imageURL = this.imageURL;
        this.clear();

        // ** Add stuff you want drawn in the background all the time here **
        var imageObj = new Image();
        imageObj.src = imageURL;
        this.canvas.width = imageObj.width * this.scale;
        this.canvas.height = imageObj.height * this.scale;
        if (!imageObj.complete) {
            return;
        }
//        console.log("Image: "+imageObj.width+" "+imageObj.height+" Scale: "+this.scale);
        ctx.scale(this.scale, this.scale);
        ctx.drawImage(imageObj, 0, 0);

        if (this.selection != null && this.mode != "R") {
            this.inputText.width(Math.round(Math.max(this.INPUT_WIDTH / this.scale, this.selection.w)));
            this.inputText.height(Math.round(this.INPUT_HEIGHT / this.scale));
            this.inputText.fontSize(Math.round(this.INPUT_FONT_SIZE / this.scale));
            this.inputText.value(this.selection.text);
            this.inputText.render();
            this.inputText.focus();
        }

        // draw all shapes
        var l = shapes.length;
//        console.log("Shapes Length: "+l);
        for (var i = 0; i < l; i++) {
            var shape = shapes[i];
            // We can skip the drawing of elements that have moved off 
            // the screen:
            if (shape.x > imageObj.width || shape.y > imageObj.height ||
                shape.x + shape.w < 0 || shape.y + shape.h < 0) continue;
//            console.log("Shape "+i+" draw called");
            shapes[i].draw(ctx);
        }

        // draw selection
        // right now this is just a stroke along the edge of the selected Shape
        if (this.selection != null) {
            ctx.strokeStyle = this.selectionColor;
            ctx.lineWidth = this.selectionWidth;
            var mySel = this.selection;
            ctx.strokeRect(mySel.x, mySel.y, mySel.w, mySel.h);
        }
//        console.log("Scrolling To"+ this.scrollX+" "+ this.scrollY); 
        window.scrollTo(this.scrollX, this.scrollY);

        // ** Add stuff you want drawn on top all the time here **

        this.valid = true;
    }
}

CanvasState.prototype.log = function (str) {
    if (!this.selection) {
//        console.log(str);
    }
}

// Creates an object with x and y defined, set to the mouse position 
// relative to the state's canvas
// If you wanna be super-correct this can be tricky, we have to worry 
// about padding and borders
CanvasState.prototype.getMouse = function (e) {
    var element = this.canvas, offsetX = 0, offsetY = 0, mx, my;

    // Compute the total offset
    if (element.offsetParent !== undefined) {
        do {
            this.log("Element: " + element.id + " OffL: " + element.offsetLeft + " scrollL: " + element.scrollLeft);
            this.log("Element: " + element.id + " OffT: " + element.offsetTop + " scrollT: " + element.scrollTop);
            offsetX += element.offsetLeft;
            offsetY += element.offsetTop;
        } while ((element = element.offsetParent));
    }

    var divLeft = this.canvasContainer.scrollLeft;
    var divTop = this.canvasContainer.scrollTop;

    this.log(" OffL: " + offsetX + " OffT: " + offsetY);

    // Add padding and border style widths to offset
    // Also add the <html> offsets in case there's a position:fixed bar
    offsetX += this.stylePaddingLeft + this.styleBorderLeft + this.htmlLeft;
    offsetY += this.stylePaddingTop + this.styleBorderTop + this.htmlTop;

    this.log(" OffL: " + offsetX + " OffT: " + offsetY);

    this.log("event pageX: " + e.pageX + " DivLeft: " + divLeft + " OffL: " + offsetX);
    this.log("event pageY: " + e.pageY + " DivTop: " + divTop + " OffT: " + offsetY);
    this.log("event clientX: " + e.clientX + " OffL: " + offsetX);
    this.log("event clientY: " + e.clientY + " OffT: " + offsetY);

    mx = Math.round((e.pageX + divLeft - offsetX) / this.scale);
    my = Math.round((e.pageY + divTop - offsetY) / this.scale);

    this.log(" MX: " + mx + " MY: " + my);

    // We return a simple javascript object (a hash) with x and y defined
    return {x: mx, y: my};
}

// If you dont want to use <body onLoad='init()'>
// You could uncomment this init() reference and place the script reference inside the body tag
//init();

// Shapes are rectangles. This overlays boxes on an image, makes them selectable etc..
function init(canvas, dataURL, oldShapes, oid) {
    var s = canvasStateList.get(canvas, dataURL, oid);
    console.log("Init Called for " + oid);
//    oldShapes = JSON.parse(oldShapes);
// JSON.parse did not work so moved to eval however that has some security risks
//    oldShapes = eval('(' + oldShapes + ')');
//    console.log(oldShapes);
    if (oldShapes == null) {
        return s;
    }
    s.shapes = []; // initialize the shapes as we are getting all info together
    console.log("Length of oldShapes = " + oldShapes.length);
    for (var i = 0; i < oldShapes.length; i++) {
        oldShape = oldShapes[i];
//            console.log(oldShape);
//            console.log("X:"+oldShape.x+"Y:"+oldShape.y+"W:"+oldShape.w+"H:"+oldShape.h+" Fill:"+oldShape.fill);
        s.addShape(new Shape(oldShape.x, oldShape.y, oldShape.w, oldShape.h, oldShape));
    }
//  s.addShape(new Shape(40,40,50,50)); // The default is gray
//  s.addShape(new Shape(60,140,40,60, 'lightskyblue'));
// Lets make some partially transparent
//  s.addShape(new Shape(80,150,60,30, 'rgba(127, 255, 212, .1)'));
//  s.addShape(new Shape(125,80,30,80, 'rgba(245, 222, 179, .2)'));
    return s;
}


// Now go make something amazing!

// Expand the canvas dimensions by 10% fixed value, later that 
// can be made configurable
CanvasState.prototype.zoomOut = function () {
    if (parseFloat(this.scale).toFixed(1) > 0.1) {
        this.scale = this.scale - 0.1;
        this.valid = false;
    } else {
        alert("Cannot scale below 10%")
    }
}

// Currently there are 2 modes supported "E" edit mode and "R" review mode
CanvasState.prototype.changeMode = function (flag) {
    this.mode = flag;
    if (this.selection) {
        this.selection.resetDisplayText();
    }
    if (this.mode == "E") {
        this.inputText.height(24);
        this.inputText.width(90);
    } else if (this.mode == "R") {
        this.inputText.height(1);
        this.inputText.width(1);
    }
    this.valid = false; // Something's changed so we must redraw
}

// Accept the selected shape
CanvasState.prototype.accept = function () {
    if (this.selection) {
        var oldState = this.selection.getState();
        this.addActivity('StateChange', oldState, 'user_accepted');
        this.selection.changeStateTo('user_accepted');
        this.selection.resetDisplayText();
        this.valid = false;
    } else {
        console.log("No active selection");
    }
}

// Shrink the canvas dimensions by 10% fixed value, later that 
// can be made configurable
CanvasState.prototype.zoomIn = function () {
    if (parseFloat(this.scale).toFixed(1) < 3.0) {
        this.scale = this.scale + 0.1;
        this.valid = false;
    } else {
        alert("Cannot scale above 300%")
    }
}

CanvasState.prototype.saveShapes = function () {
    var shapes = this.shapes;
    var oid = this.oid;
    var anno_id = this.anno_id;

//    console.log(JSON.stringify(shapes));
    for (var i = 0; i < shapes.length; i++) {
        var shape = shapes[i];

        if (shape.text != '') {
//            console.log(Object.prototype.toString.call(shape));
//            console.log("X:"+shape.x+" Y:"+shape.y+" W:"+shape.w+" H:"+shape.h);
            console.log(JSON.parse(JSON.stringify(shape)));
            console.log(JSON.stringify(shape));
        }
    }
    console.log('POST /api_v1/page/anno/' + anno_id);
    var res = {'anno': JSON.stringify(shapes)};
//    console.log('POST anno contents: ' + JSON.stringify(res));
    $.post('/api_v1/page/anno/' + anno_id, res, function (data) {
        processStatus(data, "Annotations saved successfully.",
            "Error saving annotations.");
    }, "json");
    //post('/api_v1/page/anno/'+oid, JSON.stringify(shapes));
}

function post(path, params, method) {
    method = method || "post"; // Set method to post by default if unspecified.

    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", method);
    form.setAttribute("action", path);

//    for(var key in params) {
//        if(params.hasOwnProperty(key)) {
    var hiddenField = document.createElement("input");
    hiddenField.setAttribute("type", "hidden");
    hiddenField.setAttribute("name", "Blob");
    hiddenField.setAttribute("value", params);
//            hiddenField.setAttribute("name", key);
//            hiddenField.setAttribute("value", params[key]);

    form.appendChild(hiddenField);
//         }
//    }

    document.body.appendChild(form);
    form.submit();
}

