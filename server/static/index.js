$(document).ready(_ => {
    const socketio = io.connect('http://' + document.domain + ':' + location.port);
    $("form#scan").submit(_ => {
        $("#image").attr("src", "");
        $("#decklist").hide();
        $(".loader").show();
        const file = $("#file")[0].files[0];
        if (file) {
            console.log("loading file");
            const fr = new FileReader();
            fr.onload = function () {
                const img = new Image();
                img.onload = function () {
                    const canvas = document.createElement("canvas");
                    const ctx = canvas.getContext("2d");
                    
                    // 压缩图像的最大宽度和高度
                    const maxWidth = 800;
                    const maxHeight = 800;
                    
                    let width = img.width;
                    let height = img.height;
                    
                    // 缩放图像以适应最大宽度和高度
                    if (width > maxWidth || height > maxHeight) {
                        if (width > height) {
                            height *= maxWidth / width;
                            width = maxWidth;
                        } else {
                            width *= maxHeight / height;
                            height = maxHeight;
                        }
                    }
                    
                    canvas.width = width;
                    canvas.height = height;
                    
                    // 在画布上绘制压缩后的图像
                    ctx.drawImage(img, 0, 0, width, height);
                    
                    // 将画布上的图像转换为Base64编码的字符串
                    const compressedImage = canvas.toDataURL("image/jpeg", 0.8); // 可根据需要调整压缩质量
                    
                    // 发送压缩后的图像到服务器
                    socketio.emit("scan", { "image": compressedImage, "id": socketio.id });
                };
                img.src = fr.result;
            };
            fr.readAsDataURL(file);
            $("#file")[0].value = "";
        } else {
            console.log("emit image url");
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