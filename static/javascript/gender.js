const scrollBtn = document.getElementById("scrollBtn");

window.addEventListener("scroll", () => {
    const scrollY = window.scrollY;
    const pageHeight = document.body.scrollHeight;
    const windowHeight = window.innerHeight;

    if (scrollY + windowHeight >= pageHeight - 10) {
        scrollBtn.style.opacity = "0";
        scrollBtn.style.pointerEvents = "none";
    } else {
        scrollBtn.style.opacity = "1";
        scrollBtn.style.pointerEvents = "auto";
    }
});
