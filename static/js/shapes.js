// By Simon Sarris
// www.simonsarris.com
// sarris@acm.org
//
// Last update December 2011
//
// Free to use and distribute at will
// So long as you are nice to people, etc

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
    this.fill = fill || '#AAAAAA';
    this.stroke = '#FFFF00';
    this.fontType = 'normal';
    this.fontPoints = 22;
    this.fontName = 'Arial Unicode MS';
    this.font = this.fontType+" "+this.fontPoints+"pt "+this.fontName;
    this.fillStyle = 'black';
    this.fillText = '';
    // Handle Object
    if (obj instanceof Object) {
        for (var attr in obj) {
            if (obj.hasOwnProperty(attr)){
                this[attr] = obj[attr];
            }
        }
    }
}

Shape.prototype = {
    // Draws this shape to a given context with different stroke and fill
    draw: function(ctx) {
        ctx.strokeStyle = this.stroke;
        ctx.beginPath();
        ctx.rect(this.x, this.y, this.w, this.h);
        ctx.stroke();
        ctx.fillStyle = this.fill;
        ctx.fill();
    // Text x,y starts from bottom left, whereas rectangle from top left
        ctx.font = this.font; 
        ctx.fillStyle = this.fillStyle;
        ctx.fillText(this.fillText,this.x,this.y+this.fontPoints+4);
    },

    // increment the text font size
    increaseFont: function() {
        this.fontPoints++;
        this.font = this.fontType+" "+this.fontPoints+"pt "+this.fontName;
        return this.fontPoints;
    },

    // decrement the text font size
    decreaseFont: function() {
        this.fontPoints--;
        this.font = this.fontType+" "+this.fontPoints+"pt "+this.fontName;
        return this.fontPoints;
    },

    // Determine if a point is inside the shape's bounds
    contains: function(mx, my) {
        // All we have to do is make sure the Mouse X,Y fall in the area between
        // the shape's X and (X + Width) and its Y and (Y + Height)
        return  (this.x < mx) && (this.x + this.w > mx) &&
                (this.y < my) && (this.y + this.h > my);
    },

    // Determine if a point is inside the shape's borders. 
    atBorders: function(mx, my) {
        // All we have to do is make sure the Mouse X,Y fall in the area 
        // segment around the four corners with certain distance.  
        var distance = 7;
        // currently only bottom right corner is enabled (To be enhanced)
        return  (this.atBottomRight(mx, my, distance));
    },

    // Determine if a point is inside the shape's bottom-right boundary within a
    // sqare shape of hight and width equal to distance 
    atBottomRight: function(mx, my, distance) {
        // All we have to do is make sure the Mouse X,Y fall in the area between
        // the squares X and (X + Width) and its Y and (Y + Height)
        var newx = this.x + this.w - distance;
        var newy = this.y + this.h - distance;
        var neww = distance;
        var newh = distance;

        return  (newx < mx) && (newx + neww > mx) &&
                (newy < my) && (newy + newh > my);
    },

};

function CanvasState(canvasId, dataURL, oid) {
    // **** First some setup! ****
    this.INPUT_WIDTH = 90;
    this.INPUT_HEIGHT = 24; 
    canvas = document.getElementById(canvasId);
    this.inputText = new CanvasInput({
        canvas: document.getElementById(canvasId),
        width: this.INPUT_WIDTH,
        height: this.INPUT_HEIGHT,
        padding: 0,
        borderWidth: 0,
        borderRadius: 0,
        onsubmit: function() {
                if (myState.selection) {
                    myState.selection.fillText = myState.inputText.value(); 
                    myState.valid = false;  
                    myState.inputText.value('');
                } else {
                    alert("First select the area");
                }
            },
    }); 
    this.canvas = canvas;
    this.width = canvas.width;
    this.height = canvas.height;
    this.ctx = this.canvas.getContext('2d');
    this.imageURL = dataURL;
    this.oid = oid;
    // This complicates things a little but but fixes mouse co-ordinate problems
    // when there's a border or padding. See getMouse for more detail
    var stylePaddingLeft, stylePaddingTop, styleBorderLeft, styleBorderTop;
    if (document.defaultView && document.defaultView.getComputedStyle) {
        this.stylePaddingLeft = parseInt(document.defaultView.getComputedStyle(canvas, null)['paddingLeft'], 10)      || 0;
        this.stylePaddingTop  = parseInt(document.defaultView.getComputedStyle(canvas, null)['paddingTop'], 10)       || 0;
        this.styleBorderLeft  = parseInt(document.defaultView.getComputedStyle(canvas, null)['borderLeftWidth'], 10)  || 0;
        this.styleBorderTop   = parseInt(document.defaultView.getComputedStyle(canvas, null)['borderTopWidth'], 10)   || 0;
    }
    // Some pages have fixed-position bars (like the stumbleupon bar) at the 
    // top or left of the page. They will mess up mouse coordinates and this 
    // fixes that
    var html = document.body.parentNode;
    this.htmlTop = html.offsetTop;
    this.htmlLeft = html.offsetLeft;

    // **** Keep track of state! ****
 
    this.scale = 1; // Initialize with scale as 1 (range is 0.1 - 1.0) 
    this.scrollX = 0;
  
    this.valid = false; // when set to false, the canvas will redraw everything
    this.shapes = [];  // the collection of things to be drawn
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
    canvas.addEventListener('selectstart', function(e) { e.preventDefault(); 
        return false; }, false);
    // Up, down, and move are for dragging
    canvas.addEventListener('mousedown', function(e) {
        var mouse = myState.getMouse(e);
        var mx = mouse.x;
        var my = mouse.y;
        var shapes = myState.shapes;
        var l = shapes.length;
        for (var i = l-1; i >= 0; i--) {
            if (shapes[i].contains(mx, my)) {
                var mySel; 
                if (myState.selection && myState.selection.contains(mx,my)) {
                    mySel = shapes[myState.selectionIndex];
                } else {
                    mySel = shapes[i];
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
                myState.scrollX = window.scrollX;
                myState.scrollY = window.scrollY;
                myState.valid = false;
                return;
            }
        }
        // havent returned means we have failed to select anything.
        // If there was an object selected, we deselect it
        if (myState.selection && (!myState.inputTextContains(mx,my))) {
            console.log("Deselecting - MX: "+mx+" MY: "+my);
            myState.selection = null;
            myState.selectionIndex = null;
            myState.scrollX = window.scrollX;
            myState.scrollY = window.scrollY;
            myState.valid = false; // Need to clear the old selection border
        }
    }, true);

    canvas.addEventListener('mousemove', function(e) {
        if (myState.dragging){
            var mouse = myState.getMouse(e);
            if (! myState.dragForResizing) {
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
            myState.scrollX = window.scrollX;
            myState.scrollY = window.scrollY;
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
        }
    }, true);

    canvas.addEventListener('mouseup', function(e) {
        if (myState.selection) {
            myState.changeInputLocation(myState.selection);
            myState.valid = false;
        }
        myState.dragging = false; myState.dragForResizing = false; 
        this.style.cursor = 'auto';
    }, true);

    // double click for making new shapes
    canvas.addEventListener('dblclick', function(e) {
        var mouse = myState.getMouse(e);
        // To keep the rectangle of same size, we would need to scale up the 
        // rectangle by the amount the image is scaled down
        var width = Math.round(30 / myState.scale);
        var height = Math.round(30 / myState.scale);
        myState.addShape(new Shape(mouse.x - width/2, mouse.y - height/2, 
                                   width, height, 'rgba(0,255,0,.3)'));
    }, true);

    this.altKeyDown = false;
    window.addEventListener('keyup', function(e) {
        var charPressed = e.keyCode;
        console.log("You lifted Keycode "+e.keyCode);
        if (charPressed == 16) {
            this.shiftKeyDown = false;
        }
    }, true);

    window.addEventListener('keydown', function(e) {
        var charPressed = e.keyCode;
        console.log("You pressed Keycode "+e.keyCode);
        if (charPressed == 8) {
            myState.scrollX = window.scrollX;
            myState.scrollY = window.scrollY;
            myState.valid = false;
        }
        if (charPressed == 16) {
            this.shiftKeyDown = true;
        }
        // Alt+up/down should hide and unhide the inputText bar
        if ((charPressed == 40 || charPressed == 38) && this.shiftKeyDown) {
            if (myState.inputText.height() == 1) {
                myState.inputText.height(24);
                myState.inputText.width(90);
            }else {
                myState.inputText.height(1);
                myState.inputText.width(1);
            }
            myState.valid = false; // Something's deleted so we must redraw
        }
        if (!myState.selection) {
            return;
        }
        if (charPressed == 39 && this.shiftKeyDown) {
            console.log("You pressed + key");
            myState.selection.increaseFont();
            myState.valid = false; // Something's deleted so we must redraw
        } else if (charPressed == 37 && this.shiftKeyDown) {
            console.log("You pressed - key");
            myState.selection.decreaseFont();
            myState.valid = false; // Something's deleted so we must redraw
        }else if (charPressed == 46) { // Del key triggered
            console.log("You pressed del key");
            //removing the shape from the array
            myState.shapes.splice(myState.selectionIndex,1);
            myState.selection = null;
            myState.selectionIndex = null;
            myState.valid = false; // Something's deleted so we must redraw
        } else {
            return; 
        }
    }, true);
 
/*
  window.addEventListener('mousedown', function(e) {
    var mouse = myState.getMouse(e);
    var mx = mouse.x;
    var my = mouse.y;
//    console.log("X:"+mx+"Y:"+my+"W: "+this.canvas.width+" H: "+this.canvas.height);
    if (myState.selection && (mx > this.canvas.width || my > this.canvas.height) ) {
      myState.selection = null;
      myState.selectionIndex = null;
      myState.valid = false; // Need to clear the old selection border
    }
  }, true);
*/
  // **** Options! ****
  
    this.selectionColor = '#CC0000';
    this.selectionWidth = 2;  
    this.interval = 30;
    setInterval(function() { myState.draw(); }, myState.interval);
}

CanvasState.prototype.changeInputLocation = function(selectedShape) {
    buffer = 5;
    this.inputText.x(selectedShape.x);
    if (selectedShape.y < (this.inputText.height() + buffer)) {
        this.inputText.y(selectedShape.y+selectedShape.h + buffer);
    }else {
        this.inputText.y(selectedShape.y-(this.inputText.height() + buffer));
    }
    console.log("Shape X: "+selectedShape.x+" Y: "+selectedShape.y+" H: "+selectedShape.h+" W: "+selectedShape.w+" Ix: "+this.inputText.x()+" Iy: "+this.inputText.y()+" Ih: "+this.inputText.height()+" Iw: "+this.inputText.width());
}

// Determine if a point is inside the input text box
CanvasState.prototype.inputTextContains = function(mx, my) {
    // All we have to do is make sure the Mouse X,Y fall in the area between
    // the shape's X and (X + Width) and its Y and (Y + (Height))
    return  (this.inputText.x() < mx) && 
            (this.inputText.x() + this.inputText.width() > mx) &&
            (this.inputText.y() < my) && 
            (this.inputText.y() + (this.inputText.height()) > my);
}

CanvasState.prototype.addShape = function(shape) {
    this.shapes.push(shape);
    this.valid = false;
}

CanvasState.prototype.clear = function() {
    this.ctx.clearRect(0, 0, this.width, this.height);
}

// Update the dimensions of all components of canvas.
CanvasState.prototype.adjustAllComponentsToScale = function() {
    var shapes = this.shapes;
    var imageURL = this.imageURL;
    var imageObj = new Image();
    imageObj.src = imageURL;

}

// While draw is called as often as the INTERVAL variable demands,
// It only ever does something if the canvas gets invalidated by our code
CanvasState.prototype.draw = function() {
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
        console.log("Image: "+imageObj.width+" "+imageObj.height+" Scale: "+this.scale);
        ctx.scale(this.scale,this.scale); 
        ctx.drawImage(imageObj,0,0);
        this.inputText.width(Math.round(this.INPUT_WIDTH / this.scale));
        this.inputText.height(Math.round(this.INPUT_HEIGHT / this.scale));
        this.inputText.render();
        this.inputText.focus();
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
            ctx.strokeRect(mySel.x,mySel.y,mySel.w,mySel.h);
        }
        console.log("Scrolling To"+ this.scrollX+" "+ this.scrollY); 
        window.scrollTo(this.scrollX, this.scrollY); 
    
        // ** Add stuff you want drawn on top all the time here **
    
        this.valid = true;
    }
}

CanvasState.prototype.log = function(str) {
    if (!this.selection) {
        console.log(str);
    }
}

// Creates an object with x and y defined, set to the mouse position 
// relative to the state's canvas
// If you wanna be super-correct this can be tricky, we have to worry 
// about padding and borders
CanvasState.prototype.getMouse = function(e) {
    var element = this.canvas, offsetX = 0, offsetY = 0, mx, my;
  
    // Compute the total offset
    if (element.offsetParent !== undefined) {
        do {
            this.log("Element: "+element.id+" OffL: "+element.offsetLeft+" scrollL: "+element.scrollLeft);
            this.log("Element: "+element.id+" OffT: "+element.offsetTop+" scrollT: "+element.scrollTop);
            offsetX += element.offsetLeft;
            offsetY += element.offsetTop;
        } while ((element = element.offsetParent));
    }

//BELOW 2 LINES have to be MADE GENERIC
    var divTop = document.getElementById("container").scrollTop;
    var divLeft = document.getElementById("container").scrollLeft;

    this.log(" OffL: "+offsetX+" OffT: "+offsetY);
    
    // Add padding and border style widths to offset
    // Also add the <html> offsets in case there's a position:fixed bar
    offsetX += this.stylePaddingLeft + this.styleBorderLeft + this.htmlLeft;
    offsetY += this.stylePaddingTop + this.styleBorderTop + this.htmlTop;

    this.log(" OffL: "+offsetX+" OffT: "+offsetY);

    this.log("event pageX: "+e.pageX+" DivLeft: "+divLeft+" OffL: "+offsetX);
    this.log("event pageY: "+e.pageY+" DivTop: "+divTop+" OffT: "+offsetY);
    this.log("event clientX: "+e.clientX+" OffL: "+offsetX);
    this.log("event clientY: "+e.clientY+" OffT: "+offsetY);

    mx = Math.round((e.pageX + divLeft - offsetX) / this.scale);
    my = Math.round((e.pageY + divTop - offsetY) / this.scale);

    this.log(" MX: "+mx+" MY: "+my);

    // We return a simple javascript object (a hash) with x and y defined
    return {x: mx, y: my};
}

// If you dont want to use <body onLoad='init()'>
// You could uncomment this init() reference and place the script reference inside the body tag
//init();

function init(canvas,dataURL, oldShapes, oid) {
    var s = new CanvasState(canvas,dataURL, oid);
    console.log("Init Called for "+oid);
    //oldShapes = JSON.parse(oldShapes);
// JSON.parse did not work so moved to eval however that has some security risks
//    oldShapes = eval('(' + oldShapes + ')');
    console.log(oldShapes);
    console.log(oldShapes.length);
    for (var i = 0; i < oldShapes.length; i++) {
        oldShape = oldShapes[i];
        console.log(oldShape);
        console.log("X:"+oldShape.x+"Y:"+oldShape.y+"W:"+oldShape.w+"H:"+oldShape.h+" Fill:"+oldShape.fill);
        s.addShape(new Shape(oldShape.x,oldShape.y,oldShape.w,oldShape.h,oldShape.fill, oldShape));
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
CanvasState.prototype.zoomOut = function() {
    if (parseFloat(this.scale).toFixed(1) > 0.1) {
        this.scale = this.scale - 0.1;
        this.valid = false; 
    } else {
        alert("Cannot scale below 10%")
    }
}

// Shrink the canvas dimensions by 10% fixed value, later that 
// can be made configurable
CanvasState.prototype.zoomIn = function() {
    if (parseFloat(this.scale).toFixed(1) < 3.0) {
        this.scale = this.scale + 0.1;
        this.valid = false; 
    } else {
        alert("Cannot scale above 300%")
    }
}

CanvasState.prototype.saveShapes = function() {
    var shapes = this.shapes; 
    var oid = this.oid;

    console.log(JSON.stringify(shapes));
    for (var i = 0; i < shapes.length; i++) {
        var shape = shapes[i];
            
        console.log(Object.prototype.toString.call(shape));
        console.log("X:"+shape.x+" Y:"+shape.y+" W:"+shape.w+" H:"+shape.h);
        console.log(JSON.parse(JSON.stringify(shape)));
        console.log(JSON.stringify(shape));
    }
    console.log('POST /app/'+oid);
    res = { 'anno' : shapes };
    console.log('POST anno contents: ' + JSON.stringify(res));
    $.post('/books/page/anno/'+oid, res, function(data) {
        mychkstatus(data, "Annotations saved successfully.", 
            "Error saving annotations.");
    }, "json");
    //post('/books/page/anno/'+oid, JSON.stringify(shapes));
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

