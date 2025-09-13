document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("recommendation-form");

    form.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent page refresh

        // Collect form data
        const formData = {
            sex: parseInt(document.getElementById("sex").value),
            age: parseInt(document.getElementById("age").value),
            height: parseFloat(document.getElementById("height").value),
            weight: parseFloat(document.getElementById("weight").value),
            hypertension: parseInt(document.getElementById("hypertension").value),
            diabetes: parseInt(document.getElementById("diabetes").value),
            level: parseInt(document.getElementById("level").value),
            fitness_goal: parseInt(document.getElementById("fitness_goal").value),
            fitness_type: parseInt(document.getElementById("fitness_type").value)
        };

        // Send data to Flask backend
        fetch("/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            console.log("Received Response:", data); // Debugging step

            if (data.error) {
                alert("Error: " + data.error);
            } else {
                window.location.href = `/recommend?exercises=${encodeURIComponent(data.exercises)}&diet=${encodeURIComponent(data.diet)}&equipment=${encodeURIComponent(data.equipment)}`;
            }
        })
        .catch(error => console.error("Error:", error));
    });
});
