/***********************
 ✅ TOTAL PRICE CALCULATION
************************/
function calculateTotal() {
    let total = 0;
    document
        .querySelectorAll('input[name="selected_services[]"]:checked')
        .forEach(el => total += parseFloat(el.dataset.price));

    document.getElementById("total").innerText = total;
    document.getElementById("total_price").value = total;
}

/***********************
 ✅ MAIN DOM READY
************************/
document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("book-slot-form");
    const dateInput = document.getElementById("slot_date");
    const hiddenTimeInput = document.getElementById("slot_time");
    const buttons = document.querySelectorAll(".slot-btn");
    const salonId = form.dataset.salonId;

    const now = new Date();
    const todayDate = now.toISOString().split("T")[0];
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();

    dateInput.min = todayDate;

    /* ------------------ HELPERS ------------------ */
    function timeToMinutes(t) {
        const [h, m] = t.split(":").map(Number);
        return h * 60 + m;
    }

    // Load slot status from backend
    function loadSlotStatus() {
        if (!dateInput.value) return;

        fetch(`/get-booked-slots/${salonId}/${dateInput.value}`)
            .then(res => res.json())
            .then(data => {
                const bookedSlots = data.bookedSlots; // array of slot times with count
                const workerCount = data.workerCount; // number of available workers

                buttons.forEach(btn => {
                    const time = btn.dataset.time;
                    const slotMinutes = timeToMinutes(time);
                    const nowMinutes = currentHour * 60 + currentMinute;

                    // reset
                    btn.classList.remove("slot-booked", "slot-available", "selected");
                    btn.disabled = false;

                    // ❌ Disable past slots today
                    if (dateInput.value === todayDate && slotMinutes <= nowMinutes) {
                        btn.disabled = true;
                        btn.classList.add("slot-booked");
                        return;
                    }

                    // ❌ Disable if slot fully booked (>= worker count)
                    const bookedCount = bookedSlots[time] || 0;
                    if (bookedCount >= workerCount) {
                        btn.disabled = true;
                        btn.classList.add("slot-booked");
                        return;
                    }

                    // 🟢 Available
                    btn.classList.add("slot-available");
                });

                // Clear hidden input if previously selected slot is no longer valid
                if (!document.querySelector(".slot-btn.selected")) {
                    hiddenTimeInput.value = "";
                }

            })
            .catch(() => {
                alert("❌ Unable to load slot details");
            });
    }

    /* ------------------ DATE CHANGE ------------------ */
    dateInput.addEventListener("change", () => {
        hiddenTimeInput.value = "";
        loadSlotStatus();
    });

    /* ------------------ SLOT BUTTON CLICK ------------------ */
    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            const selectedDate = dateInput.value;

            if (!selectedDate) {
                alert("❌ Please select date first");
                return;
            }

            if (btn.disabled) {
                alert("❌ This slot is not available");
                return;
            }

            buttons.forEach(b => b.classList.remove("selected"));
            btn.classList.add("selected");
            hiddenTimeInput.value = btn.dataset.time;
        });
    });

    /* ------------------ INITIAL LOAD ------------------ */
    if (dateInput.value) {
        loadSlotStatus();
    }

    /* ------------------ FORM VALIDATION ------------------ */
    form.addEventListener("submit", function (event) {
        const services = document.querySelectorAll('input[name="selected_services[]"]:checked');

        if (services.length === 0) {
            alert("⚠️ Please select at least one service!");
            event.preventDefault();
            return;
        }

        if (!hiddenTimeInput.value) {
            alert("⚠️ Please select a time slot!");
            event.preventDefault();
            return;
        }
    });

});
