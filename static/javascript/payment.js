const payButton = document.getElementById("pay-button");
console.log("Key:", razorpayKey);
console.log("Amount:", platformFee);
console.log("Order:", razorpayOrderId);
console.log("Success URL:", paymentSuccessUrl);

const razorpayOptions = {
    key: razorpayKey,
    amount: Math.round(Number(platformFee) * 100),
    currency: "INR",
    name: "Gloora Salon Booking",
    description: `Platform Fee (₹${platformFee})`,
    order_id: razorpayOrderId,

    handler(response) {

        console.log("PAYMENT SUCCESS");
        console.log(response);

        submitPayment(response);
    },

    modal: {
        ondismiss() {
            console.log("PAYMENT POPUP CLOSED");
        }
    }
};

const rzp = new Razorpay(razorpayOptions);

rzp.on("payment.failed", function(response) {

    console.log("PAYMENT FAILED");

    console.log(response.error);

    alert(
        response.error.description ||
        "Payment Failed"
    );
});

if (payButton) {

    payButton.addEventListener("click", (e) => {

        e.preventDefault();

        console.log("OPENING PAYMENT");

        rzp.open();
    });
}





function submitPayment(response) {
    const form = document.createElement("form");

    form.method = "POST";
    form.action = paymentSuccessUrl;

    form.innerHTML = `
        <input type="hidden" name="razorpay_payment_id" value="${response.razorpay_payment_id}">
        <input type="hidden" name="razorpay_order_id" value="${response.razorpay_order_id}">
        <input type="hidden" name="razorpay_signature" value="${response.razorpay_signature}">
    `;

    document.body.appendChild(form);
    form.submit();
}



function parseSlotDateTime(date, time) {
    return new Date(`${date}T${time}:00`);
}

function playSlotAlert() {
    if (alertSound) {
        alertSound.currentTime = 0;
        alertSound.loop = true;

        alertSound.play().catch(() => {
            console.log("Autoplay blocked.");
        });
    }

    alert("⏰ Reminder!\nYour salon appointment is in 15 minutes.");
}

function scheduleSlotReminder(date, time) {
    const appointmentTime = parseSlotDateTime(date, time);
    const reminderTime = appointmentTime.getTime() - (15 * 60 * 1000);

    const delay = reminderTime - Date.now();

    if (delay <= 0) return;

    localStorage.setItem("slotAlertTime", reminderTime);

    setTimeout(playSlotAlert, delay);
}

(function restoreReminder() {
    const savedTime = Number(localStorage.getItem("slotAlertTime"));

    if (!savedTime) return;

    const delay = savedTime - Date.now();

    if (delay > 0) {
        setTimeout(playSlotAlert, delay);
    }
})();


window.addEventListener("click", () => {
    if (alertSound) {
        alertSound.loop = false;
    }
});


document.querySelectorAll("ul li").forEach((li) => {
    li.addEventListener("click", () => {
        const date = li.querySelector(".date-value")?.textContent;
        const timeRange = li.querySelector(".time-value")?.textContent;

        if (!date || !timeRange) return;

        const start = timeRange.split("-")[0].trim();

        const reminderTime = new Date(
            parseSlotDateTime(date, start).getTime() - 15 * 60 * 1000
        );

        alert(
            `⏰ Salon Appointment Reminder\n\n` +
            `📅 Date: ${date}\n` +
            `🕒 Slot: ${timeRange}\n\n` +
            `🔔 Recommended Alarm Time: ${reminderTime.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit"
            })}`
        );
    });
});