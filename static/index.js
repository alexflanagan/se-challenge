/*global window*/
/*global document*/
/*global YUI*/

function animateOverlay(cfg) {
    'use strict';
    YUI().use('node', 'anim', function (Y) {
        var nodeName, animDef, anim;

        nodeName = (cfg.sample ? '#sample_overlay' : "#overlay");
        Y.one(nodeName).setStyle("zIndex", 1);

        animDef = {
            to: { opacity: (cfg.hide ? 0 : 1) },
            node: nodeName,
            duration: 1,
            easing: 'easeBothStrong'
        };

        anim = new Y.Anim(animDef);
        anim.run();
    });
}

function drag(e) {
    'use strict';
    e.dataTransfer.setData("uploadData", e.target.id);
}

function drop(e) {
    'use strict';
    var data = e.dataTransfer.getData("uploadData");
    if (data === '') {
        return;
    }

    e.preventDefault();
    e.target.appendChild(document.getElementById(data));
    animateOverlay({ sample: true });
}



YUI().use('node', 'event', 'uploader', 'uploader-html5', function (Y) {
    'use strict';
    Y.Uploader = Y.UploaderHTML5;

    var uploader = new Y.Uploader({
        width: "100%",
        height: "100%",
        dragAndDropArea: "#uploader",
        fileFieldName: "spreadsheet",
        multipleFiles: false,
        uploadURL: ['//', window.location.host, '/upload'].join(''),
        simLimit: 1,
        withCredentials: false,
        selectButtonLabel: ''
    });

    uploader.after("fileselect", function () {
        uploader.uploadAll();
    });

    uploader.after("uploadcomplete", function showTable(e) {
        Y.one("#sample_overlay").setContent(e.data);
        animateOverlay({ sample: false, hide: true });
        animateOverlay({ sample: true, hide: false });
    });

    function init() {
        uploader.render("#uploader");
        Y.one(".yui3-button").hide();
    }

    Y.on("domready", init);
});
