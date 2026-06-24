/***********************
 ✅ TOTAL & PLATFORM FEE CALCULATION
************************/
function calculateTotal() {

    let total = 0;

    const selectedServices = document.querySelectorAll(
        'input[name="selected_services[]"]:checked'
    );

    selectedServices.forEach(el => {
        total += parseFloat(el.dataset.price || 0);
    });

    const platformFee = selectedServices.length * 10;

    document.getElementById("total").innerText = total.toFixed(2);

    const platformFeeElement = document.getElementById("platform_fee");
    if (platformFeeElement) {
        platformFeeElement.innerText = platformFee;
    }

    // Hidden input sent to backend (salon charges only)
    document.getElementById("total_price").value = total;

    const duration = selectedServices.length * 30;

    document.getElementById("duration").innerText =
    duration;
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

    dateInput.min = todayDate;

    let bookedSlots = {};
    let workerCount = 0;

    /* ------------------ HELPERS ------------------ */

    function getCurrentMinutes() {
        const current = new Date();
        return current.getHours() * 60 + current.getMinutes();
    }

    function timeToMinutes(t) {
        const [h, m] = t.split(":").map(Number);
        return h * 60 + m;
    }

    function minutesToTime(minutes) {
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;

        return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
    }

    function getSelectedServiceCount() {
        return document.querySelectorAll(
            'input[name="selected_services[]"]:checked'
        ).length;
    }

    // Generate required 30-minute slots
    function getRequiredSlots(startTime, serviceCount) {

        const startMinutes = timeToMinutes(startTime);
        const slots = [];

        for (let i = 0; i < serviceCount; i++) {
            slots.push(
                minutesToTime(startMinutes + (i * 30))
            );
        }

        return slots;
    }

    /* ------------------ UPDATE BUTTON STATES ------------------ */

    function updateSlotButtons() {

        const serviceCount = Math.max(getSelectedServiceCount(), 1);

        buttons.forEach(btn => {

            const time = btn.dataset.time;
            const slotMinutes = timeToMinutes(time);

            btn.classList.remove(
                "slot-booked",
                "slot-available"
            );

            btn.disabled = false;

            // Disable past slots for today
            if (
                dateInput.value === todayDate &&
                slotMinutes <= getCurrentMinutes()
            ) {
                btn.disabled = true;
                btn.classList.add("slot-booked");
                return;
            }

            // Generate consecutive required slots
            const requiredSlots = getRequiredSlots(
                time,
                serviceCount
            );

            // Prevent bookings beyond 10:00 PM
            const lastSlotMinutes =
                timeToMinutes(
                    requiredSlots[requiredSlots.length - 1]
                ) + 30;

            if (lastSlotMinutes > (22 * 60)) {
                btn.disabled = true;
                btn.classList.add("slot-booked");
                return;
            }

            // Check worker availability
            const unavailable = requiredSlots.some(slot => {
                return (bookedSlots[slot] || 0) >= workerCount;
            });

            if (unavailable) {
                btn.disabled = true;
                btn.classList.add("slot-booked");
                return;
            }

            btn.classList.add("slot-available");
        });

        // Clear selection only if selected slot became invalid
        const selectedBtn = document.querySelector(
            ".slot-btn.selected"
        );

        if (selectedBtn && selectedBtn.disabled) {
            selectedBtn.classList.remove("selected");
            hiddenTimeInput.value = "";
        }
    }

    /* ------------------ LOAD SLOT STATUS ------------------ */

    function loadSlotStatus() {

        if (!dateInput.value) return;

        fetch(`/get-booked-slots/${salonId}/${dateInput.value}`)
    .then(res => res.json())
    .then(data => {

        bookedSlots = data.bookedSlots || {};

        // Ensure worker count is always at least 1
        workerCount = Math.max(
            parseInt(data.workerCount || 1),
            1
        );

        console.log("Booked Slots:", bookedSlots);
        console.log("Worker Count:", workerCount);

        updateSlotButtons();
    })
    .catch(error => {
        console.error("Error loading slots:", error);
        alert("❌ Unable to load slot details");
    });
    }

    /* ------------------ SERVICE CHANGE ------------------ */

    document
        .querySelectorAll('input[name="selected_services[]"]')
        .forEach(cb => {

            cb.addEventListener("change", () => {

                calculateTotal();

                if (dateInput.value) {
                    updateSlotButtons();
                }
            });
        });

    /* ------------------ DATE CHANGE ------------------ */

    dateInput.addEventListener("change", () => {

        hiddenTimeInput.value = "";

        buttons.forEach(btn => {
            btn.classList.remove("selected");
        });

        loadSlotStatus();
    });

    /* ------------------ SLOT BUTTON CLICK ------------------ */
let selectedSlots = [];

buttons.forEach(btn => {

    btn.addEventListener("click", () => {

        const serviceCount = getSelectedServiceCount();

        if (serviceCount === 0) {
            alert("⚠️ Please select service first");
            return;
        }

        if (btn.disabled) {
            return;
        }

        const slotTime = btn.dataset.time;

        // Remove slot if already selected
        if (btn.classList.contains("selected")) {

            btn.classList.remove("selected");

            selectedSlots = selectedSlots.filter(
                t => t !== slotTime
            );

        } else {

            // Limit based on selected services
            if (selectedSlots.length >= serviceCount) {

                alert(
                    `You can select only ${serviceCount} slot(s)`
                );

                return;
            }

            btn.classList.add("selected");

            selectedSlots.push(slotTime);
        }

        hiddenTimeInput.value =
            selectedSlots.join(",");
    });

});
    /* ------------------ INITIAL LOAD ------------------ */

    calculateTotal();

    if (dateInput.value) {
        loadSlotStatus();
    }

    /* ------------------ FORM VALIDATION ------------------ */

    form.addEventListener("submit", function (event) {

        const services = document.querySelectorAll(
            'input[name="selected_services[]"]:checked'
        );

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