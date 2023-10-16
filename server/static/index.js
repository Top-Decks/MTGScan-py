

$(document).ready(_ => {
    const socketio = io.connect('http://' + document.domain + ':' + location.port);
    $("form#scan").submit(_ => {  // send the image to the server
        $("#image").attr("src", "");
        $("#decklist").hide();
        $(".loader").show();
        const file = $("#file")[0].files[0];
        if (file) {
            const fr = new FileReader();
            fr.readAsBinaryString(file);
            fr.addEventListener("load", function () {
                console.log("emit scan event");
                console.log(btoa(fr.result));
                socketio.emit("scan", { "image": btoa(fr.result) , "id": socketio.id });
            }, false);
            $("#file")[0].value = "";
        }
        else {
            socketio.emit("scan", { "image": $("#url").val(), "id": socketio.id });
            $("#url")[0].value = "";
        }
        return false;
    });
    socketio.on("scan_result", msg => { // get the decklist from the server
        console.log("on scan result")
        $(".loader").hide();
        let deck = "";
        for (const card in msg.deck) {
            deck += `${msg.deck[card]} ${card}\n`;
        }
        $("#decklist").text(deck.slice(0, -1));
        $("#decklist").show();
        $("#image").attr("src", "data:image/png;base64, " + msg.image);
        // console.log(msg);
    });
});