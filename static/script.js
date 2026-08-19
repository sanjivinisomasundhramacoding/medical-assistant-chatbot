document.addEventListener("DOMContentLoaded", function () {

    const messageInput = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendBtn");
    const messages = document.getElementById("messages");
    const welcome = document.getElementById("welcome");

    const newChatBtn = document.getElementById("newChatBtn");
    const clearRecent = document.getElementById("clearRecent");

    const settingsBtn = document.getElementById("settingsBtn");
    const aboutBtn = document.getElementById("aboutBtn");

    const settingsModal = document.getElementById("settingsModal");
    const aboutModal = document.getElementById("aboutModal");

    const themeBtn = document.getElementById("themeBtn");
    const darkToggle = document.getElementById("darkToggle");

    const menuBtn = document.getElementById("menuBtn");
    const sidebar = document.getElementById("sidebar");

    const uploadBtn = document.getElementById("uploadBtn");
    const imageInput = document.getElementById("imageInput");
    const imagePreview = document.getElementById("imagePreview");

    const languageSelect = document.getElementById("languageSelect");

    const clearHistoryBtn =
        document.getElementById("clearHistoryBtn");

    const recentChats =
        document.getElementById("recentChats");

    const toast =
        document.getElementById("toast");


    /* =====================================================
       TOAST
    ===================================================== */

    function showToast(message) {

        toast.textContent = message;

        toast.classList.add("show");

        setTimeout(function () {
            toast.classList.remove("show");
        }, 2200);
    }


    /* =====================================================
       SEND MESSAGE
    ===================================================== */

    async function sendMessage() {

        const message = messageInput.value.trim();

        if (!message) {

            showToast("Please enter a question.");

            return;
        }


        addMessage(message, "user");

        messageInput.value = "";

        autoResize();

        welcome.style.display = "none";


        const loading = addMessage(
            "Thinking...",
            "bot"
        );


        try {

            const language =
                languageSelect.value || "en";


            const response = await fetch(
                "/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        message: message,
                        language: language
                    })
                }
            );


            const data = await response.json();


            loading.remove();


            addMessage(
                data.reply || "Sorry, no response received.",
                "bot"
            );


            saveRecentChat(message);

        }

        catch (error) {

            console.error(error);

            loading.remove();

            addMessage(
                "Sorry, something went wrong. Please try again.",
                "bot"
            );

        }

    }


    /* =====================================================
       ADD MESSAGE
    ===================================================== */

    function addMessage(text, type) {

        const wrapper =
            document.createElement("div");

        wrapper.className =
            "message " + type;


        if (type === "bot") {

            const icon =
                document.createElement("div");

            icon.className = "bot-icon";

            icon.innerHTML =
                '<i class="fa-solid fa-heart-pulse"></i>';

            wrapper.appendChild(icon);

        }


        const content =
            document.createElement("div");

        content.className =
            "message-content";

        content.textContent = text;


        wrapper.appendChild(content);

        messages.appendChild(wrapper);


        const chatArea =
            document.querySelector(".chat-area");

        chatArea.scrollTop =
            chatArea.scrollHeight;


        return wrapper;
    }


    /* =====================================================
       SEND BUTTON
    ===================================================== */

    sendBtn.addEventListener(
        "click",
        sendMessage
    );


    /* =====================================================
       ENTER KEY
    ===================================================== */

    messageInput.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendMessage();

            }

        }
    );


    /* =====================================================
       AUTO RESIZE TEXTAREA
    ===================================================== */

    function autoResize() {

        messageInput.style.height = "auto";

        messageInput.style.height =
            Math.min(
                messageInput.scrollHeight,
                130
            ) + "px";

    }


    messageInput.addEventListener(
        "input",
        autoResize
    );


    /* =====================================================
       SUGGESTION BUTTONS
    ===================================================== */

    document.querySelectorAll(
        ".suggestion"
    ).forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                const question =
                    button.dataset.question;

                messageInput.value =
                    question;

                autoResize();

                sendMessage();

            }
        );

    });


    /* =====================================================
       NEW CHAT
    ===================================================== */

    newChatBtn.addEventListener(
        "click",
        function () {

            messages.innerHTML = "";

            welcome.style.display = "";

            messageInput.value = "";

            autoResize();

            showToast("New chat started.");

            sidebar.classList.remove("open");

        }
    );


    /* =====================================================
       CLEAR RECENTS
    ===================================================== */

    clearRecent.addEventListener(
        "click",
        function () {

            localStorage.removeItem(
                "mediguide_recent"
            );

            renderRecentChats();

            showToast("Recent chats cleared.");

        }
    );


    /* =====================================================
       RECENT CHAT STORAGE
    ===================================================== */

    function saveRecentChat(message) {

        let recent =
            JSON.parse(
                localStorage.getItem(
                    "mediguide_recent"
                ) || "[]"
            );


        recent.unshift(message);


        recent =
            recent.slice(0, 8);


        localStorage.setItem(
            "mediguide_recent",
            JSON.stringify(recent)
        );


        renderRecentChats();

    }


    function renderRecentChats() {

        const recent =
            JSON.parse(
                localStorage.getItem(
                    "mediguide_recent"
                ) || "[]"
            );


        recentChats.innerHTML = "";


        if (recent.length === 0) {

            recentChats.innerHTML =
                '<p class="empty-recent">No recent chats</p>';

            return;

        }


        recent.forEach(function (item) {

            const button =
                document.createElement("div");

            button.className =
                "recent-item";


            button.innerHTML =
                '<i class="fa-regular fa-message"></i>' +
                '<span></span>';


            button.querySelector("span").textContent =
                item;


            button.addEventListener(
                "click",
                function () {

                    messageInput.value =
                        item;

                    autoResize();

                    messageInput.focus();

                }
            );


            recentChats.appendChild(button);

        });

    }


    renderRecentChats();


    /* =====================================================
       SETTINGS
    ===================================================== */

    settingsBtn.addEventListener(
        "click",
        function () {

            settingsModal.classList.add("show");

        }
    );


    /* =====================================================
       ABOUT
    ===================================================== */

    aboutBtn.addEventListener(
        "click",
        function () {

            aboutModal.classList.add("show");

        }
    );


    /* =====================================================
       CLOSE MODALS
    ===================================================== */

    document.querySelectorAll(
        "[data-close]"
    ).forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                const modalId =
                    button.dataset.close;

                document.getElementById(
                    modalId
                ).classList.remove("show");

            }
        );

    });


    /* =====================================================
       CLOSE MODAL WHEN CLICK OUTSIDE
    ===================================================== */

    document.querySelectorAll(
        ".modal-overlay"
    ).forEach(function (modal) {

        modal.addEventListener(
            "click",
            function (event) {

                if (event.target === modal) {

                    modal.classList.remove("show");

                }

            }
        );

    });


    /* =====================================================
       DARK MODE
    ===================================================== */

    function setDarkMode(enabled) {

        document.body.classList.toggle(
            "dark",
            enabled
        );


        darkToggle.checked = enabled;


        const icon =
            themeBtn.querySelector("i");


        if (enabled) {

            icon.className =
                "fa-solid fa-sun";

        }
        else {

            icon.className =
                "fa-solid fa-moon";

        }


        localStorage.setItem(
            "mediguide_dark",
            enabled ? "1" : "0"
        );

    }


    themeBtn.addEventListener(
        "click",
        function () {

            setDarkMode(
                !document.body.classList.contains("dark")
            );

        }
    );


    darkToggle.addEventListener(
        "change",
        function () {

            setDarkMode(
                darkToggle.checked
            );

        }
    );


    const savedDark =
        localStorage.getItem(
            "mediguide_dark"
        ) === "1";


    setDarkMode(savedDark);


    /* =====================================================
       CLEAR HISTORY
    ===================================================== */

    clearHistoryBtn.addEventListener(
        "click",
        function () {

            messages.innerHTML = "";

            localStorage.removeItem(
                "mediguide_recent"
            );

            renderRecentChats();

            welcome.style.display = "";

            settingsModal.classList.remove("show");

            showToast("Chat history cleared.");

        }
    );


    /* =====================================================
       UPLOAD IMAGE
    ===================================================== */

    uploadBtn.addEventListener(
        "click",
        function () {

            imageInput.click();

        }
    );


    imageInput.addEventListener(
        "change",
        function () {

            const file =
                imageInput.files[0];


            if (!file) {
                return;
            }


            imagePreview.innerHTML = "";


            const image =
                document.createElement("img");

            image.className =
                "preview-image";


            image.src =
                URL.createObjectURL(file);


            imagePreview.appendChild(image);


            showToast(
                "Image selected."
            );

        }
    );


    /* =====================================================
       MOBILE MENU
    ===================================================== */

    menuBtn.addEventListener(
        "click",
        function () {

            sidebar.classList.toggle(
                "open"
            );

        }
    );


    /* =====================================================
       ESCAPE KEY
    ===================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Escape") {

                settingsModal.classList.remove("show");

                aboutModal.classList.remove("show");

                sidebar.classList.remove("open");

            }

        }
    );

});
// =====================================================
// FIREBASE AUTHENTICATION
// =====================================================

window.addEventListener("firebaseUserReady", function (event) {
    const user = event.detail;

    console.log("Logged in user:", user.email);

    // User-specific recent chats
    renderRecentChats();
});


// Make recent chats user-specific
function getCurrentUserStorageKey() {
    const user = window.currentFirebaseUser;

    if (!user) {
        return null;
    }

    return "mediguide_recent_" + user.uid;
}