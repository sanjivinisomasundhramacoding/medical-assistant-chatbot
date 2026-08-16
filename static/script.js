async function sendMessage() {
    const input = document.getElementById("user-input");
    const message = input.value.trim();

    if (message === "") {
        return;
    }

    const chatBox = document.getElementById("chat-box");

    chatBox.innerHTML += `
        <p><b>You:</b> ${message}</p>
    `;

    input.value = "";

    const response = await fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: message
        })
    });

    const data = await response.json();

    chatBox.innerHTML += `
        <p><b>Assistant:</b> ${data.reply}</p>
    `;

    chatBox.scrollTop = chatBox.scrollHeight;
}