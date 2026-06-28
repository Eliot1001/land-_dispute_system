function filterCases(status) {
    let cards = document.querySelectorAll(".case-card");

    cards.forEach(card => {
        if (status === "all") {
            card.style.display = "block";
        } else {
            if (card.classList.contains(status)) {
                card.style.display = "block";
            } else {
                card.style.display = "none";
            }
        }
    });
}

function submitCase() {
    alert("Dispute submitted successfully!");
}

function updateCase() {
    alert("Case updated successfully!");
}