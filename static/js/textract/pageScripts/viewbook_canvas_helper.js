// Simplest way to understand this file is by seeing how it is called.

// A collection of canvas objects - one for each page image.
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

    // Properly sets curCanvasState.
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

// A canvas object is a canvas on an image + a bunch of rectangles.
// Look at event handlers to understand how it functions.
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
            if (canvasStateContext.selectedRectangle) {
                canvasStateContext.handleTextSubmission();
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
    this.rectangles = [];  // the collection of things to be drawn
    this.containerScrollLeft = 0;
    this.containerScrollTop = 0;
    this.dragForScrolling = false;  // True when mouse down in canvas 
                                    // without any selectedRectangle
    this.dragForScrollingX = 0; // X position when mouse was moved down 
    this.dragForScrollingY = 0; // Y position when mouse was moved down 
    this.dragging = false; // Keep track of when we are dragging
    this.dragForResizing = false; // Keep track of when we are dragging 
                                  // for resizing

    // the current selected object. In the future we could turn this into an 
    // array for multiple selectedRectangle
    this.selectedRectangle = null;
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
    var canvasStateContext = this;

    // fixes a problem where double clicking causes text to get selected on the 
    // canvas
    canvas.addEventListener('selectstart', function (e) {
        e.preventDefault();
        return false;
    }, false);

    // Mousedown selects a rectangle. Can resize.
    // Up, down, and move are for dragging
    canvas.addEventListener('mousedown', function (e) {
        if (!canvasStateContext.active) {
            return;
        }
        var mouse = canvasStateContext.getMouse(e);
        var mx = mouse.x;
        var my = mouse.y;
        var shapes = canvasStateContext.rectangles;
        var l = shapes.length;
        for (var i = l - 1; i >= 0; i--) {
            if (shapes[i].contains(mx, my)) {
                var mySel;
                if (canvasStateContext.selectedRectangle && canvasStateContext.selectedRectangle.contains(mx, my)) {
                    mySel = shapes[canvasStateContext.selectionIndex];
                    if (canvasStateContext.mode == "R") {
                        if (mySel.getState() != "user_accepted") {
                            mySel.toggleDisplayText();
                        }
                    }
                } else { // Selection of differnt rectangle
                    mySel = shapes[i];
                    if (canvasStateContext.mode == "R") {
                        if (canvasStateContext.selectedRectangle) {
                            canvasStateContext.selectedRectangle.resetDisplayText();
                        }
                        if (mySel.getState() != "user_accepted") {
                            mySel.toggleDisplayText();
                        }
                    }
                    canvasStateContext.selectedRectangle = mySel;
                    canvasStateContext.selectionIndex = i;
                }
                // Keep track of where in the object we clicked
                // so we can move it smoothly (see mousemove)
                canvasStateContext.dragoffx = mx - mySel.x;
                canvasStateContext.dragoffy = my - mySel.y;
                canvasStateContext.dragging = true;
                if (mySel.atBorders(mx, my)) {
                    canvasStateContext.dragForResizing = true;
                    this.style.cursor = 'se-resize';
                }
                canvasStateContext.scrollX = Math.round(window.scrollX);
                canvasStateContext.scrollY = Math.round(window.scrollY);

                if (canvasStateContext.mode == "E") {
                    canvasStateContext.changeInputLocation(canvasStateContext.selectedRectangle);
                }

                canvasStateContext.valid = false;
                return;
            }
        }
        // havent returned means we have failed to select anything.
        // If there was an object selected, we deselect it
        if (canvasStateContext.selectedRectangle && (!canvasStateContext.inputTextContains(mx, my))) {
            console.log("Deselecting - MX: " + mx + " MY: " + my);
            if (canvasStateContext.mode == "R") {
                canvasStateContext.selectedRectangle.resetDisplayText();
            }
            canvasStateContext.selectedRectangle = null;
            canvasStateContext.selectionIndex = null;
            canvasStateContext.scrollX = Math.round(window.scrollX);
            canvasStateContext.scrollY = Math.round(window.scrollY);
            canvasStateContext.valid = false; // Need to clear the old selectedRectangle border
        }
        if (!canvasStateContext.dragForResizing && !canvasStateContext.dragging) {
            canvasStateContext.scrollX = Math.round(window.scrollX);
            canvasStateContext.scrollY = Math.round(window.scrollY);
            /**
             canvasStateContext.dragForScrolling = true;
             canvasStateContext.dragForScrollingX = e.pageX;
             canvasStateContext.dragForScrollingY = e.pageY;
             */
            canvasStateContext.valid = false; // Need to move the canvas
        }
    }, true);

    canvas.addEventListener('mousemove', function (e) {
        if (!canvasStateContext.active) {
            return;
        }
        e.preventDefault();
        if (canvasStateContext.dragging) {
            var mouse = canvasStateContext.getMouse(e);
            if (!canvasStateContext.dragForResizing) {
                // We don't want to drag the object by its top-left corner,
                // we want to drag it from where we clicked. Thats why we
                // saved the offset and use it here
                canvasStateContext.selectedRectangle.updateBounds(mouse.x - canvasStateContext.dragoffx,
                    mouse.y - canvasStateContext.dragoffy, undefined, undefined);
            } else {
                // Not allowing the selectedRectangle to go -ve and keeping the min
                // size of rectangle as 15.
                if ((mouse.x - canvasStateContext.selectedRectangle.x) > 15 &&
                    (mouse.y - canvasStateContext.selectedRectangle.y) > 15) {
                    canvasStateContext.selectedRectangle.updateBounds(undefined, undefined, mouse.x - canvasStateContext.selectedRectangle.x,
                        mouse.y - canvasStateContext.selectedRectangle.y)
                }
            }
            canvasStateContext.scrollX = Math.round(window.scrollX);
            canvasStateContext.scrollY = Math.round(window.scrollY);
            canvasStateContext.valid = false; // Something's dragging so we must redraw
        } else if (canvasStateContext.selectedRectangle) {
            var mouse = canvasStateContext.getMouse(e);
            var mx = mouse.x;
            var my = mouse.y;
            if (canvasStateContext.selectedRectangle.atBorders(mx, my)) {
                this.style.cursor = 'se-resize';
            } else {
                this.style.cursor = 'auto';
            }
        } else if (canvasStateContext.dragForScrolling) {
            /*
             this.style.cursor = 'all-scroll';
             var leftMove = canvasStateContext.canvasContainer.scrollLeft;
             var topMove = canvasStateContext.canvasContainer.scrollTop;

             console.log("1.Scrolling Div To"+ leftMove+" "+ topMove);

             leftMove += (canvasStateContext.dragForScrollingX - e.pageX);
             if (leftMove < 0 ) {
             leftMove = 0;
             }
             console.log("2.Scrolling Div To"+ leftMove+" "+ topMove);

             if (leftMove > (canvasStateContext.canvasContainer.scrollWidth - canvasStateContext.canvasContainer.clientWidth)) {
             leftMove = canvasStateContext.canvasContainer.scrollWidth - canvasStateContext.canvasContainer.clientWidth;
             }
             leftMove = Math.round(leftMove);

             topMove += (canvasStateContext.dragForScrollingY - e.pageY);
             if (topMove < 0 ) {
             topMove = 0;
             }
             if (topMove > (canvasStateContext.canvasContainer.scrollHeight - canvasStateContext.canvasContainer.clientHeight)) {
             topMove = canvasStateContext.canvasContainer.scrollHeight - canvasStateContext.canvasContainer.clientHeight;
             }
             topMove = Math.round(topMove);

             canvasStateContext.dragForScrollingX = e.pageX;
             canvasStateContext.dragForScrollingY = e.pageY;
             canvasStateContext.canvasContainer.scrollLeft = leftMove;
             canvasStateContext.canvasContainer.scrollTop = topMove;
             canvasStateContext.containerScrollLeft = leftMove;
             canvasStateContext.containerScrollTop = topMove;
             console.log("Scrolling Div To"+ leftMove+" "+ topMove);

             canvasStateContext.valid = false; // Something's dragging so we must redraw
             */
        }
    }, true);

    canvas.addEventListener('mouseup', function (e) {
        if (!canvasStateContext.active) {
            return;
        }
        if (canvasStateContext.dragForScrolling) {
            /*
             var leftMove = canvasStateContext.canvasContainer.scrollLeft;
             var topMove = canvasStateContext.canvasContainer.scrollTop;

             leftMove += (canvasStateContext.dragForScrollingX - e.pageX);
             if (leftMove < 0 ) {
             leftMove = 0;
             }
             if (leftMove > (canvasStateContext.canvasContainer.scrollWidth - canvasStateContext.canvasContainer.clientWidth)) {
             leftMove = canvasStateContext.canvasContainer.scrollWidth - canvasStateContext.canvasContainer.clientWidth;
             }
             leftMove = Math.round(leftMove);

             topMove += (canvasStateContext.dragForScrollingY - e.pageY);
             if (topMove < 0 ) {
             topMove = 0;
             }
             if (topMove > (canvasStateContext.canvasContainer.scrollHeight - canvasStateContext.canvasContainer.clientHeight)) {
             topMove = canvasStateContext.canvasContainer.scrollHeight - canvasStateContext.canvasContainer.clientHeight;
             }
             topMove = Math.round(topMove);

             canvasStateContext.dragForScrollingX = e.pageX;
             canvasStateContext.dragForScrollingY = e.pageY;
             canvasStateContext.canvasContainer.scrollLeft = leftMove;
             canvasStateContext.canvasContainer.scrollTop = topMove;
             canvasStateContext.containerScrollLeft = leftMove;
             canvasStateContext.containerScrollTop = topMove;
             console.log("Scrolling Div To"+ leftMove+" "+ topMove);
             canvasStateContext.valid = false; // Something's dragging so we must redraw
             */
        }
        if (canvasStateContext.selectedRectangle) {
            canvasStateContext.changeInputLocation(canvasStateContext.selectedRectangle);
        }
        canvasStateContext.valid = false;
        canvasStateContext.dragging = false;
        canvasStateContext.dragForResizing = false;
//        canvasStateContext.dragForScrolling = false;
        this.style.cursor = 'auto';
    }, true);

    // double click for making new rectangles
    canvas.addEventListener('dblclick', function (e) {
        if (!canvasStateContext.active) {
            return;
        }
        var mouse = canvasStateContext.getMouse(e);
        // To keep the rectangle of same size, we would need to scale up the 
        // rectangle by the amount the image is scaled down
        var width = Math.round(30 / canvasStateContext.scale);
        var height = Math.round(30 / canvasStateContext.scale);
        canvasStateContext.addRectangle(new Rectangle(mouse.x - width / 2, mouse.y - height / 2,
            width, height));
    }, true);

    window.addEventListener('keydown', function (e) {
        if (!canvasStateContext.active) {
            return false;
        }
        var charPressed = e.which || e.keyCode;
//        console.log("You pressed Key "+charPressed);
        if (charPressed == 9) {
            canvasStateContext.handleTextSubmission();
            canvasStateContext.handleTab(e);
            e.preventDefault();
            e.stopPropagation();
        }
        // Undo operation called
        if (charPressed == 90 && e.ctrlKey) {
            canvasStateContext.undoActivity();
            e.preventDefault();
            e.stopPropagation();
        } else if (charPressed == 89 && e.ctrlKey) {
            canvasStateContext.redoActivity();
            e.preventDefault();
            e.stopPropagation();
        }

        // Alt+up/down should hide and unhide the inputText bar
        if ((charPressed == 40 || charPressed == 38) && e.shiftKey) {
            if (canvasStateContext.mode == "R") {
                return;
            } //No action taken
            if (canvasStateContext.inputText.height() == 1) {
                if (canvasStateContext.selectedRectangle) {
                    canvasStateContext.changeInputLocation(canvasStateContext.selectedRectangle);
                }
                canvasStateContext.inputText.height(24);
                canvasStateContext.inputText.width(90);
            } else {
                canvasStateContext.inputText.height(1);
                canvasStateContext.inputText.width(1);
            }
            canvasStateContext.valid = false; // Something's changed so we must redraw
        }
        if (!canvasStateContext.selectedRectangle) {
            return;
        }
        if (charPressed == 39 && e.shiftKey) {
//            console.log("You pressed + key");
            canvasStateContext.selectedRectangle.increaseFont();
            canvasStateContext.valid = false; // Something's changed so we must redraw
        } else if (charPressed == 37 && e.shiftKey) {
//            console.log("You pressed - key");
            canvasStateContext.selectedRectangle.decreaseFont();
            canvasStateContext.valid = false; // Something's changed so we must redraw
        } else if (charPressed == 46) { // Del key triggered
//            console.log("You pressed del key");
            //removing the shape from the array
            if (canvasStateContext.mode != "S") {
                var oldState = canvasStateContext.selectedRectangle.getState();
                canvasStateContext.addActivity('StateChange', canvasStateContext.selectedRectangle, oldState, 'user_deleted');
                canvasStateContext.selectedRectangle.markDeleted();
                canvasStateContext.valid = false; // Something's changed so we must redraw
                e.preventDefault();
                e.stopPropagation();
            }
//            canvasStateContext.rectangles.splice(canvasStateContext.selectionIndex,1);
//            canvasStateContext.selectedRectangle = null;
//            canvasStateContext.selectionIndex = null;
//            canvasStateContext.valid = false; // Something's deleted so we must redraw
        } else if (charPressed == 65) {
            if (canvasStateContext.mode == "R") {
                var oldState = canvasStateContext.selectedRectangle.getState();
                canvasStateContext.addActivity('StateChange', canvasStateContext.selectedRectangle, oldState, 'user_accepted');
                canvasStateContext.selectedRectangle.changeStateTo('user_accepted');
                canvasStateContext.selectedRectangle.resetDisplayText();
                canvasStateContext.valid = false; // Something's changed so we must redraw
                e.preventDefault();
                e.stopPropagation();
            }
        } else if (charPressed == 72 && e.ctrlKey && e.shiftKey) {
            if (canvasStateContext.selectedRectangle.getState() != "user_accepted") {
                canvasStateContext.selectedRectangle.toggleDisplayText();
            }
            canvasStateContext.valid = false; // Something's changed so we must redraw
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
//    setInterval(function() { canvasStateContext.draw(); }, canvasStateContext.interval);
}

CanvasState.prototype.handleTextSubmission = function () {
    var canvasStateContext = this;
    if (canvasStateContext.selectedRectangle) {
        canvasStateContext.selectedRectangle.print();
        var prevValue = canvasStateContext.selectedRectangle.getText();
        console.log(canvasStateContext.inputText.value());
        canvasStateContext.selectedRectangle.setText(canvasStateContext.inputText.value());
//        canvasStateContext.selectedRectangle.fontPoints = Math.round(canvasStateContext.selectedRectangle.h - 5/canvasStateContext.scale);
//        canvasStateContext.selectedRectangle.font = canvasStateContext.selectedRectangle.fontType+" "+canvasStateContext.selectedRectangle.fontPoints+"pt "+canvasStateContext.selectedRectangle.fontName;
        canvasStateContext.valid = false;
        console.log("Prev =" + prevValue + " New=" + canvasStateContext.selectedRectangle.getText());
        if (canvasStateContext.selectedRectangle.getText() != prevValue) {
            var oldState = canvasStateContext.selectedRectangle.getState();
            canvasStateContext.addActivity('StateChange', canvasStateContext.selectedRectangle, oldState, 'user_supplied');
            canvasStateContext.selectedRectangle.changeStateTo('user_supplied');
        }
        canvasStateContext.inputText.value('');
        canvasStateContext.selectedRectangle.print();
        // canvasStateContext.selectedRectangle.draw(canvasStateContext.ctx);
    } else {
        console.log("First select the area");
    }
}

CanvasState.prototype.handleTab = function (e) {
    var canvasStateContext = this;
    if (canvasStateContext.selectedRectangle) {
        canvasStateContext.selectedRectangle.resetDisplayText();
    } else {
        console.log("No selectedRectangle done ");
        return false;
    }
    var prevSelection = canvasStateContext.selectedRectangle;
    var newSelection = prevSelection;
    do {
        if (e.shiftKey) {
            if (canvasStateContext.selectionIndex == 0) {
                canvasStateContext.selectionIndex = canvasStateContext.rectangles.length - 1;
            } else {
                canvasStateContext.selectionIndex--;
            }
        } else {
            if (canvasStateContext.selectionIndex == (canvasStateContext.rectangles.length - 1)) {
                canvasStateContext.selectionIndex = 0;
            } else {
                canvasStateContext.selectionIndex++;
            }
        }
        newSelection = canvasStateContext.rectangles[canvasStateContext.selectionIndex];
    } while (newSelection.getState() == "user_deleted");

    canvasStateContext.selectedRectangle = newSelection;

    if (canvasStateContext.mode == "R") {
        if (canvasStateContext.selectedRectangle.getState() != "user_accepted") {
            canvasStateContext.selectedRectangle.toggleDisplayText();
        }
    }
    if (canvasStateContext.mode == "E") {
        canvasStateContext.changeInputLocation(canvasStateContext.selectedRectangle);
    }

    canvasStateContext.scrollX = Math.round(window.scrollX);
    canvasStateContext.scrollY = Math.round(window.scrollY);
//  console.log("ScrollX = "+canvasStateContext.scrollX+" ScrollY = "+canvasStateContext.scrollY);

    var scrollLeft = canvasStateContext.canvasContainer.scrollLeft;
    var scrollTop = canvasStateContext.canvasContainer.scrollTop;
    var scrollWidth = canvasStateContext.canvasContainer.scrollWidth;
    var scrollHeight = canvasStateContext.canvasContainer.scrollHeight;
    var clientWidth = canvasStateContext.canvasContainer.clientWidth;
    var clientHeight = canvasStateContext.canvasContainer.clientHeight;
    var horizontalMove = 0;
    var verticalMove = 0;
//  console.log("ScrollHeight = "+scrollHeight+" clientHeight "+clientHeight);
//  console.log("ScrollWidth = "+scrollWidth+" clientWidth "+clientWidth);

    var hDistance = Math.abs((newSelection.x - prevSelection.x) * canvasStateContext.scale);
//  console.log("H-Distance = "+hDistance);
    //Check if the new selectedRectangle is on right or left of viewport
    if ((newSelection.x * canvasStateContext.scale) > (scrollLeft + clientWidth)) {
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
    } else if ((newSelection.x * canvasStateContext.scale) < scrollLeft) {
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

    var vDistance = Math.abs((newSelection.y - prevSelection.y) * canvasStateContext.scale);
//    console.log("V-Distance = "+vDistance);
    //Check if the new selectedRectangle is on top or bottom of viewport
    if ((newSelection.y * canvasStateContext.scale) > (scrollTop + clientHeight)) {
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
    } else if ((newSelection.y * canvasStateContext.scale) < scrollTop) {
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
    canvasStateContext.canvasContainer.scrollLeft = scrollLeft + horizontalMove;
    canvasStateContext.canvasContainer.scrollTop = scrollTop + verticalMove;
    canvasStateContext.valid = false;
    // For logging purpose only
//     scrollLeft = canvasStateContext.canvasContainer.scrollLeft;
//     scrollTop = canvasStateContext.canvasContainer.scrollTop;
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
    // console.log(JSON.stringify(selectedShape, null, 2));
    console.log(selectedShape, this.inputText);
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

CanvasState.prototype.addRectangle = function (rectangle) {
    var length = this.rectangles.length;
    // traversing from the back of the list. Bottom right to top left 
    for (i = length - 1; i >= 0; i--) {
        var lastShape = this.rectangles[i];
        var shapeInserted = false;
        if (lastShape.x < rectangle.x && (Math.abs(lastShape.y - rectangle.y) < (lastShape.h / 2))) { // Right side on the same row
            this.rectangles.splice(i + 1, 0, rectangle);
            shapeInserted = true;
            break;
        } else if ((rectangle.y - lastShape.y) > (lastShape.h / 2)) { // Next row case
            this.rectangles.splice(i + 1, 0, rectangle);
            shapeInserted = true;
            break;
        }
    }
    if (length == 0) {
        this.rectangles.push(rectangle);
    } else if (shapeInserted == false) { // Insert at the begining
        this.rectangles.splice(0, 0, rectangle);
    }
    if (rectangle.getText() != null) {
        rectangle.print();
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
        var rectangles = this.rectangles;
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

        if (this.selectedRectangle != null && this.mode != "R") {
            this.inputText.width(Math.round(Math.max(this.INPUT_WIDTH / this.scale, this.selectedRectangle.w)));
            this.inputText.height(Math.round(this.INPUT_HEIGHT / this.scale));
            this.inputText.fontSize(Math.round(this.INPUT_FONT_SIZE / this.scale));
            this.inputText.value(this.selectedRectangle.getTextOrEmpty());
            this.inputText.render();
            this.inputText.focus();
        }

        // draw all rectangles
        var l = rectangles.length;
//        console.log("Shapes Length: "+l);
        for (var i = 0; i < l; i++) {
            var shape = rectangles[i];
            // We can skip the drawing of elements that have moved off 
            // the screen:
            if (shape.x > imageObj.width || shape.y > imageObj.height ||
                shape.x + shape.w < 0 || shape.y + shape.h < 0) continue;
//            console.log("Rectangle "+i+" draw called");
            rectangles[i].draw(ctx);
        }

        // draw selectedRectangle
        // right now this is just a stroke along the edge of the selected Rectangle
        if (this.selectedRectangle != null) {
            ctx.strokeStyle = this.selectionColor;
            ctx.lineWidth = this.selectionWidth;
            var mySel = this.selectedRectangle;
            ctx.strokeRect(mySel.x, mySel.y, mySel.w, mySel.h);
        }
//        console.log("Scrolling To"+ this.scrollX+" "+ this.scrollY); 
        window.scrollTo(this.scrollX, this.scrollY);

        // ** Add stuff you want drawn on top all the time here **

        this.valid = true;
    }
}

CanvasState.prototype.log = function (str) {
    if (!this.selectedRectangle) {
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

// Shapes are rectangles. This overlays boxes on an image, makes them selectable etc..
CanvasState.prototype.setAnnotations = function(annotationNodes) {
    this.rectangles = []; // initialize the rectangles as we are getting all info together
    this.addAnnotations(annotationNodes);
}

CanvasState.prototype.addAnnotations = function(annotationNodes) {
    self = this;
    annotationNodes.forEach(function(annotationNode, index) {
        console.log(annotationNode)
        var rectangle = annotationNode.content.targets[0].rectangle;
        self.addRectangle(new Rectangle(rectangle.x1, rectangle.y1, rectangle.w, rectangle.h, annotationNode));
    })
}



// Currently there are 2 modes supported "E" edit mode and "R" review mode
CanvasState.prototype.changeMode = function (flag) {
    this.mode = flag;
    if (this.selectedRectangle) {
        this.selectedRectangle.resetDisplayText();
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
    if (this.selectedRectangle) {
        var oldState = this.selectedRectangle.getState();
        this.addActivity('StateChange', oldState, 'user_accepted');
        this.selectedRectangle.changeStateTo('user_accepted');
        this.selectedRectangle.resetDisplayText();
        this.valid = false;
    } else {
        console.log("No active selectedRectangle");
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

CanvasState.prototype.saveAnnotations = function (pageId) {
    var modifiedUndeletedRectangles = this.rectangles.filter(function (x) {
        return x.modified && !x.deleted;
    });
    var updatedAnnotationNodes = modifiedUndeletedRectangles.map(function (x) {
        return x.annotationNode;
    });
    var unmodifiedRectangles = this.rectangles.filter(function (x) {
        return !x.modified;
    });
    var canvasStateContext = this;
    if (updatedAnnotationNodes.length > 0) {
        console.log('POST anno contents: ', updatedAnnotationNodes);
        $.ajax({
            url: '/ullekhanam/v1/annotations',
            type: 'POST',
            data: JSON.stringify(updatedAnnotationNodes),
            contentType: 'application/json; charset=utf-8',
            dataType: 'json',
            success: function (nodes) {
                console.log("Annotations saved successfully.");
                canvasStateContext.rectangles = unmodifiedRectangles;
                canvasStateContext.addAnnotations(nodes);
            }
        });
    }

    var deletedRectangles = this.rectangles.filter(function (x) {
        return x.deleted;
    });
    // console.log('DELETE deletedRectangles: ', deletedRectangles);
    var deletedAnnotationNodes = deletedRectangles.map(function (x) {
        return x.annotationNode;
    })
    // console.log('DELETE anno contents: ', deletedAnnotationNodes);
    var deletedAnnotationNodesWithId = deletedAnnotationNodes.filter(function (x) {
        return (x.content._id != undefined)
    });
    if (deletedAnnotationNodesWithId.length > 0) {
        console.log('DELETE anno contents: ', deletedAnnotationNodesWithId);
        //post('/textract/v1/page/anno/'+oid, JSON.stringify(rectangles));
        $.ajax({
            url: '/ullekhanam/v1/annotations',
            type: 'DELETE',
            data: JSON.stringify(deletedAnnotationNodesWithId),
            contentType: 'application/json; charset=utf-8',
            dataType: 'json',
            success: function(result) {
                console.log("Annotations deleted successfully. Dropping: ", canvasStateContext.rectangles.length);
                canvasStateContext.rectangles = canvasStateContext.rectangles.filter(function (x) {
                    return !x.deleted;
                })
                console.log("Dropped: ", canvasStateContext.rectangles.length);
            }
        });
    }
}
