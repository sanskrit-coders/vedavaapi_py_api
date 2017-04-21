function serialize(obj){
    var k = Object.keys(obj);
    var s = "";
    for(var i=0;i<k.length;i++) {
        s += k[i] + "=" + encodeURIComponent(obj[k[i]]);
        if (i != k.length -1) s += "&";
    }
    return s;
};


// Validating Empty Field
function check_empty() {
if (document.getElementById('wlname').value == "" || document.getElementById('ipadd').value == "") {
alert("Fill All Fields !");
} else {
    
}

//document.getElementById('form_popup').submit();
//code for row content 

var workloadname = document.getElementById('wlname').value;
var ipaddress = document.getElementById('ipadd').value
var viewdiv =  document.getElementById("viewcontent");
  var plot_params = {workloadname,ipaddress};
  //var data=serialize(plot_params);
  $.get('/addnew?wlname=' +workloadname+'&ipadd='+ipaddress, function(data){
        //$plotdiv.html(data);
       // $(".hourglass").hide();
      alert(data);
     $('#viewcontent').html(data);
     
    });
 


var table=document.getElementById('table-list');
var tbody=document.getElementsByTagName('TBODY')[0];
var row=document.createElement('TR');
var cell1=document.createElement('TD');
var cell2=document.createElement('TD');
var cell3=document.createElement('TD');
var cell4=document.createElement('TD');




var cell1value='';
cell1value+='<input type="checkbox" />';
var cell2value='';
cell2value+='Two';
var cell3value='';
cell3value+='Three';
var cell4value='';
cell4value+='Four';


cell1.innerHTML=cell1value;
cell2.innerHTML=cell2value;
cell3.innerHTML=cell3value;
cell4.innerHTML=cell4value;

row.appendChild(cell1);
row.appendChild(cell2);
row.appendChild(cell3);
row.appendChild(cell4);

tbody.appendChild(row);

alert("Form Submitted Successfully...");
div_hide();
}
}
//Function To Display Popup
function div_show() {
document.getElementById('abc').style.display = "block";
}
//Function to Hide Popup
function div_hide(){
document.getElementById('abc').style.display = "none";
}


function div_refresh()
{
   alert("refresh");
    var path = "/tmp/traceserver/public/splunk/";
   $.get('/listworkloads?path=' +path, function(data){
      
      alert(data);
    
     
    });
 
}



