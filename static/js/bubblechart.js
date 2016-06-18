function createRsrc(rsrcdb, id, type) {
    var r = rsrcdb[id];
    if (r != null)
        return r;

    var name = id.replace(/(:.*):[AB]$/, '$1');
    r = rsrcdb[id] = { 'id': id, 'name': name, 'type': type, 'isLogical':0, 'children': [] };
    
    if (type == 'POOL') {
        r.children.push({'id': 'Volumes-'+id, 'type': 'VOL', 'label':'Volumes', 'isLogical':1,'name' : 'Volumes-'+id, 'children' : []});
        r.children.push({'id': 'Drives-'+id, 'type': 'DRIVE', 'label':'Drives', 'isLogical':1, 'name' : 'Drives-'+id, 'children' : []});

        var ctlrid = id.split(':').pop();
        ctlr = createRsrc(rsrcdb, 'CTLR:' + ctlrid, 'CTLR');
        ctlr.children.push(r);
    }
    return r;
}

function setRsrcAttr(rsrcdb, r, attr, val)
{
    if (attr == 'container') {
        if (r.type == 'VOL') {
            if ('owner' in r) {
                ctlrid = r.owner.split(':').pop();
                p = createRsrc(rsrcdb, val + ":" + ctlrid, 'POOL');
                p.children[0].children.push(r);
            }
            else r[attr] = val;
        }
        else if(r.type == 'CTLR'){
            p = createRsrc(rsrcdb, val, 'ARRAY');
            p.children.push(r);
        }
    }
    else if (attr == 'owner') {
        if (r.type == 'DRIVE') {
            ctlrid = r.id.split(':').pop();
            parent_pool = createRsrc(rsrcdb, val + ":" + ctlrid, 'POOL');
            parent_pool.children[1].children.push(r);
        }
        else if (r.type == 'VOL') {
            if ('container' in r) {
                var pool = r.container;
                ctlrid = val.split(':').pop();
                p = createRsrc(rsrcdb, pool + ":" + ctlrid, 'POOL');
                p.children[0].children.push(r);
            }
            else r[attr] = val;
        }
    }
    else r[attr] = val;
}

function createTree(collection)
{
    var root=null;
    var rsrcdb = { 'id': '', 'name': '', 'children': [ ] }; 
    for (var i=0; i < collection.length; i++) 
    {
        var type = collection[i].RSRC_TYPE_S;
        var id = type + ':' + collection[i].RSRC_ID_S;
        var o = collection[i];
        if (type.startsWith('#')) {
            continue;
        }
        if (type == 'POOL' || type == 'DRIVE') {
            var rA = createRsrc(rsrcdb, id + ":A", type);
            setRsrcAttr(rsrcdb, rA, o.RSRC_ATTR_S, o.RSRC_VALUE_S);
            var rB = createRsrc(rsrcdb, id + ":B", type);
            setRsrcAttr(rsrcdb, rB, o.RSRC_ATTR_S, o.RSRC_VALUE_S);
        }
        else if (type != 'FC') {
            var r = createRsrc(rsrcdb, id, type);
            setRsrcAttr(rsrcdb, r, o.RSRC_ATTR_S, o.RSRC_VALUE_S);
            if (type == 'ARRAY' && root == null)
                root = r;
        }
    }
    if (! root)
        return root;

    var npools = 0;
    $.each(root.children, function(idx, ctlr) {
        for (var i = ctlr.children.length - 1; i >= 0; i--) {
            var pool = ctlr.children[i]; 
            // Pool has no volumes owned by this controller? 
            // Remove the pool from this controller
            if (pool.children[0].children.length == 0) {
                ctlr.children.splice(i, 1);
                continue;
            }
            //console.log("Showing pool " + pool.id);
            ++ npools;
        }
    });

    $.each(rsrcdb, function(idx, r) {
        var desc = r.name + ":\n";
        $.each(r, function(key, value ) {
            if (! key.match("id|type|name|isLogical|children"))
                desc += "  " + key + ":\t" + value + "\n";
        });
        r['desc'] = desc;
        //console.log(desc);
        r['noname'] = (r.type == 'POOL' && npools <= 8) ? 1 : 0;
    });

    return root;
}

function plot_bubblechart(filepath)
{
	
	var dataObj = new Array();
	var innerDataObj = {};
	var j =0;
	
	// To get arrayprofile.csv data
	
	$.get('/workloads/getarrayprofiledata?filepath='+filepath, function(csvdata){
		
		var lines = csvdata.split("\n");
		var revlines= new Array();
		for(var k=lines.length-1;k>0;k--)
		{
			if(lines[k]!="")
			{
				revlines[j]=lines[k];
				j = parseInt(j + 1);
			}
		}
		j=0;
		var items = lines[0].split(",");
		for(var i=0;i<revlines.length-1;i++)
		{
			j = parseInt(i + 1);
			if(revlines[j]!="")
			{
				items = revlines[j].split(",");
				innerDataObj = {};
				innerDataObj["RSRC_TYPE_S"] = items[0];
				innerDataObj["RSRC_ID_S"] = items[1];
				innerDataObj["RSRC_ATTR_S"] = items[2];
				innerDataObj["RSRC_VALUE_S"] = items[3];
				dataObj[i]= innerDataObj;	
			}
		}
		
		data = createTree(dataObj);
		var root = data;
		
		var diameter = 1320,
			format = d3.format(",d"),
			color = d3.scale.category20c();

		var bubble = d3.layout.pack()
			.sort(null)
			.size([diameter, diameter])
			.padding(1.5);
			
		var svg = d3.select("body").append("svg")
			.attr("width", diameter)
			.attr("height", diameter)
			.attr("class", "bubble")
			.call(d3.behavior.zoom().on("zoom", redraw))
			.append("g").attr("class", "group2");
			
		function clickOnCircleFunc(){
		  d3.event.preventDefault();
		  d3.event.stopPropagation();
		  $this = $(this);
		  if(d3.event.target.nodeName === "text" || d3.event.target.nodeName === "tspan"){
			var asdf = $(this).attr('data-classname');
			$this = $('circle[data-classname="'+asdf+'"]');
		  }
			if ($this.attr('data-select') !== "active") {
			  $this.attr('data-select','active').css('fill', '#3182bd');
			}
			else {
			  $this.attr('data-select','inactive').css('fill', '#ff4719');
			}
		}

		function redraw() {
		  svg.attr("transform", "translate(" + d3.event.translate + ")" + " scale(" + d3.event.scale + ")");
		}
		
       var pack = d3.layout.pack()
           .padding(10)
           .size([700, 700])
           .value(function(d) {return d.children.length+1;})
		   
       var focus = root,
       nodes = pack.nodes(root);
   
       var handlers = {'color': color_picker};
	   var margin = {top: 20, right: 70, bottom: 30, left: 15.5};
	   
       svg.append("g")
		   .attr("transform", "translate(" + margin.left  + "," + margin.top + ")")
		   .selectAll("circle")
           .data(nodes)
           .enter().append("svg:circle")
           .attr("class", function(d) { return d.parent ? d.children ? "node" : "node node--leaf" : "node node--root"; })
           .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
		   .attr("r", function(d) { return d.r;})
           .style("fill", function(d) {  return d.children ? handlers['color'](d)(d.depth) : null; })
           .append("svg:title")
           .text(function(d){
						if(d.isLogical==1) {
							return d.label;
						}
                        else {
                            return d.desc;
                        }
						});
   
       svg.append("g").selectAll("text")
           .data(nodes)
           .enter().append("text")
           .attr("class", "label")
           .attr("transform", function(d) { return "translate(" + (d.x+margin.left) + "," + (d.y+margin.top) + ")"; })
           .style("fill-opacity", function(d) {return d.type === "POOL" ? 1 : 0; })
           .style("display", function(d) { return d.noname == 1 ? null : "none"; })
           .text(function(d) { return d.name; });  
		
		svg.append("g")
		.on("mousedown",clickOnCircleFunc).on("touchstart",clickOnCircleFunc)
		.attr("class", "nodecircle")
		.style("fill", '#ff4719');
		
		svg.append("g")
		.on("mousedown",clickOnCircleFunc).on("touchstart",clickOnCircleFunc)
		.attr("text-anchor", "middle")
		.attr("class", "nodetext");
	});
}

function color_picker(d) {
    var type = d.type;
    if (type == 'VOL')
        return d3.scale.linear()
            .domain([1, 5])
            .range(["hsl(120,80%,80%)", "hsl(152,30%,20%)"])
            .interpolate(d3.interpolateHcl);
    else if (type == 'DRIVE')
        return d3.scale.linear()
            .domain([1, 5])
            .range(["hsl(30,80%,100%)", "hsl(70,30%,20%)"])
            .interpolate(d3.interpolateHcl);
    else if (type == 'CTLR')
        return d3.scale.linear()
            .domain([1, 5])
            .range(["hsl(124, 80%, 84%)", "hsl(124, 80%, 84%)"])
            .interpolate(d3.interpolateHcl);
    else if (type == 'POOL')
        return d3.scale.linear()
            .domain([2, 5])
            .range(["hsl(64, 63%, 86%)", "hsl(75,51%,90%)"])
            .interpolate(d3.interpolateHcl);
    else
        return d3.scale.linear()
            .domain([-1, 5])
            .range(["hsl(221, 51%, 95%)", "hsl(221,51%,80%)"])
            .interpolate(d3.interpolateHcl);
}

