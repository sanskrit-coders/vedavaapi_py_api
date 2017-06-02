// Initially based on (likely) https://github.com/simonsarris/Canvas-tutorials/blob/master/shapes.js By Simon Sarris, modified heavily by deshmup.

// Constructor for Rectangle objects.
// Returns what is mainly a data container.
// For now they will just be defined as rectangles.
function Rectangle(x, y, w, h, annotationNode) {
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
    this.fill = 'rgba(0,255,0,.2)';
    this.stroke = '#FFFF00';
    this.fontType = 'normal';
    this.fontPoints = this.h - 10;
    this.fontName = 'Arial Unicode MS';
    this.font = this.fontType + " " + this.fontPoints + "pt " + this.fontName;
    this.fillStyle = 'black';
    this.displayTextAbove = false;
    this.annotationNode = annotationNode;
    this.modified = false;
    this.deleted = false;
    if (this.annotationNode == undefined) {
        this.annotationNode = makeJsonObjectNode(makeImageAnnotation(this));
        this.modified = true;
    }
}

Rectangle.prototype = {
    updateBounds: function (x, y, w, h) {
        if (x != undefined) {
            this.x = x;
        }
        if (y != undefined) {
            this.y = y;
        }
        if (w != undefined) {
            this.w = w;
        }
        if (h != undefined) {
            this.h = h;
        }
        this.updateImageAnnotationBounds();
        this.modified = true;
    },
    updateImageAnnotationBounds: function () {
        var rectangle = this.annotationNode.content.targets[0].rectangle;
        rectangle.x1 = this.x;
        rectangle.y1 = this.y;
        rectangle.w = this.w;
        rectangle.h = this.h;

    },
    getText: function () {
        if (this.annotationNode.children.length == 0) {
            return null;
        } else {
            return this.annotationNode.children[0].content.content.text;
        }
    },
    getTextOrEmpty: function () {
        var text = this.getText();
        if (text != null) {
            return text;
        } else {
            return "";
        }
    },

    setText: function (text) {
        if (this.annotationNode.children.length == 0) {
            this.annotationNode.children[0] = makeJsonObjectNode(makeTextAnnotation(text));
        }
        this.annotationNode.children[0].content.content.text = text;
        this.modified = true;
    },

    markDeleted: function () {
        this.changeStateTo('user_deleted');
        this.resetDisplayText();
        this.deleted = true;
    },

    // Draws this shape to a given context with different stroke and fill
    draw: function (ctx) {
        if (this.deleted) {
            // Dont draw
            return;
        } else if (this.getTextOrEmpty() === "") {
            this.stroke = 'rgba(255,0,0,1)';
            this.fill = 'rgba(0,255,0,.3)';
        } else {
            this.stroke = 'rgba(255,0,0,1)';
            this.fill = 'rgba(255,255,255,.9)';
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
        // console.log(this.getTextOrEmpty());
        if (this.displayTextAbove == true) {
            ctx.fillText(this.getTextOrEmpty(), this.x, this.y);
        } else {
            ctx.fillText(this.getTextOrEmpty(), this.x, this.y + this.fontPoints + 4);
        }
    },

    fitTextInRectangle: function() {

    },

    print: function () {
        console.log(this);
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
        return this.annotationNode.content.source.type;
    },

    // change state of the shape
    changeStateTo: function (newState) {
        this.modified = true;
        this.annotationNode.content.source.type = newState;
        if (this.annotationNode.children.length > 0) {
            this.annotationNode.children[0].content.source.type = newState;
        }
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

