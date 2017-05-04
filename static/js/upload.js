var UPLOAD_URL = "/books/upload";

// List of pending files to handle when the Upload button is finally clicked.
var PENDING_FILES  = [];

// Validating Empty Field first and then start capture
function startUpload()
{
    if (document.getElementById('uploadpath').value == ""){
            alert("Fill All Fields !");
    }
    else {
            doUpload();
            $('#bgblur').css('opacity','1');
    }
}


function doUpload() {
   //alert("inside doUpload");
    $("#progress").show();
    var $progressBar   = $("#progress-bar");

    // Gray out the form.
   // $("#upload-form :input").attr("disabled", "disabled");

    // Initialize the progress bar.
    $progressBar.css({"width": "0%"});

    // Collect the form data.
    fd = collectFormData();

    // Attach the files.
    for (var i = 0, ie = PENDING_FILES.length; i < ie; i++) {
        // Collect the other form data.
        fd.append("file", PENDING_FILES[i]);
        console.log(PENDING_FILES[i]);
    }

    // invoking server over ajax call.
    fd.append("__ajax", "true");
    
    var xhr = $.ajax({
        xhr: function() {
            var xhrobj = $.ajaxSettings.xhr();
            if (xhrobj.upload) {
                xhrobj.upload.addEventListener("progress", function(event) {
                    var percent = 0;
                    var position = event.loaded || event.position;
                    var total    = event.total;
                    if (event.lengthComputable) {
                        percent = Math.ceil(position / total * 100);
                    }

                    // Set the progress bar.
                    $progressBar.css({"width": percent + "%"});
                    $progressBar.text(percent + "%");
                }, false)
            }
            return xhrobj;
        },
        url: UPLOAD_URL,
        method: "POST",
        contentType: false,
        processData: false,
        cache: false,
        data: fd,
        success: function(data) {
            $progressBar.css({"width": "100%"});
            data = JSON.parse(data);
            if (processStatus(data)) {
                 //alert("uploaded successfully..");
                 $('#upload_popup').fadeOut("slow");
                  getBooks();
                  location.reload();
            }
            else {
                window.alert(data.status);
                $("#upload-form :input").removeAttr("disabled");
                return;
            }
        },
    });
    
}


function collectFormData() {
    // Go through all the form fields and collect their names/values.
    var fd = new FormData();

    $("#upload-form :input").each(function() {
        var $this = $(this);
        var name  = $this.attr("name");
        var type  = $this.attr("type") || "";
        var value = $this.val();

        // No name = no care.
        if (name === undefined) {
            return;
        }

        // Skip the file upload box for now.
        if (type === "file") {
            return;
        }

        // Checkboxes? Only add their value if they're checked.
        if (type === "checkbox" || type === "radio") {
            if (!$this.is(":checked")) {
                return;
            }
        }

        fd.append(name, value);
    });

    return fd;
}


function handleFiles(files) {
    // Add them to the pending files list.
    for (var i = 0, ie = files.length; i < ie; i++) {
        PENDING_FILES.push(files[i]);
    }
}


