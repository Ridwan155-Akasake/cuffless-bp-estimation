// Toggle mobile nav menu
const menuToggle = document.getElementById("menu-toggle");
const navMenu = document.getElementById("nav-menu");
if (menuToggle && navMenu) {
  menuToggle.addEventListener("click", () => {
    navMenu.classList.toggle("active");
  });
}

// Navigation or Responsive Logic
function toggleMenu() {
  document.querySelector(".nav-menu")?.classList.toggle("active");
}

// You can call appropriate init functions based on current page
window.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("recordTableBody")) loadDataRecords();
});

//theme toggle fucntion
function toggleTheme() {
  const body = document.body;
  body.classList.toggle("dark-theme");

  // Optionally, save the theme preference in localStorage
  if (body.classList.contains("dark-theme")) {
    localStorage.setItem("theme", "dark");
  } else {
    localStorage.setItem("theme", "light");
  }
}

// Load the user's preferred theme on page load
window.onload = function () {
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "dark") {
    document.body.classList.add("dark-theme");
  }
}



//-----------------------------//
//    Collection & Measure     //
//-----------------------------//

// Function to fetch the latest sensor data (heart rate, SPO2)
async function fetchSensorData(event) {
  event.preventDefault(); // Prevent the button from reloading the page

  console.log("Frontend: Fetching latest sensor data...");

  try {
    // Fetch the latest data from the backend
    const response = await fetch('https://io-t-ppg-bp-monitor-backend.vercel.app/api/ppgData/latest');
    const data = await response.json();

    // Check if there is an error in the response
    if (data.error) {
      console.error("Frontend: Error -", data.error);
      return;
    }

    // Display the heart rate and SPO2 on the page
    document.getElementById('sensor-heart-rate').innerText = `${data.heartRate} BPM`;
    document.getElementById('sensor-oxygen-level').innerText = `${data.spo2}%`;

    // Show the sensor section
    document.getElementById('sensor-section').style.display = 'block';

    // Get the IR and RED values
    const irValues = data.ir;
    const redValues = data.red;
    console.log("Frontend: IR Values -", irValues);
    console.log("Frontend: RED Values -", redValues);

    // Store them in localStorage for later use
    localStorage.setItem('spo2', data.spo2);
    localStorage.setItem('heartRate', data.heartRate);
    localStorage.setItem('irValues', JSON.stringify(irValues));
    localStorage.setItem('redValues', JSON.stringify(redValues));

    console.log("Frontend: IR and RED values stored in localStorage.");

    // IR Graph
    const irCtx = document.getElementById('irGraph').getContext('2d');
    const irChart = new Chart(irCtx, {
      type: 'line',
      data: {
        labels: Array.from({ length: irValues.length }, (_, i) => i + 1),
        datasets: [{
          label: 'IR Values',
          data: irValues,
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1,
          fill: false,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            title: {
              display: true,
              text: 'Sample (Index)',
            },
          },
          y: {
            title: {
              display: true,
              text: 'IR Sensor Values',
            },
            beginAtZero: false,
            suggestedMin: Math.min(...irValues) - 50,
            suggestedMax: Math.max(...irValues) + 50,
            ticks: {
              stepSize: 10,
            },
          },
        },
      },
    });

    // RED Graph
    const redCtx = document.getElementById('redGraph').getContext('2d');
    const redChart = new Chart(redCtx, {
      type: 'line',
      data: {
        labels: Array.from({ length: redValues.length }, (_, i) => i + 1),
        datasets: [{
          label: 'RED Values',
          data: redValues,
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 1,
          fill: false,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            title: {
              display: true,
              text: 'sample (Index)',
            },
          },
          y: {
            title: {
              display: true,
              text: 'RED Sensor Values',
            },
            beginAtZero: false,
            suggestedMin: Math.min(...redValues) - 50,
            suggestedMax: Math.max(...redValues) + 50,
            ticks: {
              stepSize: 10,
            },
          },
        },
      },
    });

    console.log("Frontend: IR and RED graphs rendered successfully.");

  } catch (error) {
    console.error('Frontend: Error fetching data:', error);
  }
}



// Function to convert feet and inches to cm
function convertHeightToCm(feet, inches) {
  const cmFromFeet = feet * 30.48;  // Convert feet to cm
  const cmFromInches = inches * 2.54;  // Convert inches to cm
  return cmFromFeet + cmFromInches;  // Return total height in cm
}

// Function to calculate BMI
function calculateBMI(weight, heightInCm) {
  const heightInM = heightInCm / 100;  // Convert height to meters
  const bmi = weight / (heightInM * heightInM);  // Calculate BMI
  return bmi.toFixed(2);  // Return BMI with two decimal points
}

// Function to commit collected data (Systolic and Diastolic BP)
async function commitCollectedData(event) {
  event.preventDefault(); // Prevent default form submission

  const age = parseInt(document.getElementById('c-age').value);
  const gender = document.getElementById('c-gender').value;
  const feet = parseInt(document.getElementById('c-feet').value);
  const inches = parseInt(document.getElementById('c-inches').value);
  const weight = parseInt(document.getElementById('c-weight').value);
  const systolic = parseInt(document.getElementById('c-systolic').value);
  const diastolic = parseInt(document.getElementById('c-diastolic').value);

  // Validate inputs (basic validation)
  if (isNaN(age) || !gender || isNaN(feet) || isNaN(inches) || isNaN(weight) || isNaN(systolic) || isNaN(diastolic)) {
    alert("Please fill all the fields with valid data.");
    return;
  }

  // Convert feet and inches to cm
  const heightInCm = convertHeightToCm(feet, inches);

  // Calculate BMI
  const bmi = calculateBMI(weight, heightInCm);

  // Log the collected data
  console.log("Frontend: Data Collected for update -", { age, gender, heightInCm, weight, bmi, systolic, diastolic });

  try {
    // Send the updated data to the backend (update URL)
    const updateResponse = await fetch('https://io-t-ppg-bp-monitor-backend.vercel.app/api/mergeData/latest', { // Updated URL
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userAge: age,
        userGender: gender,
        userHeight: heightInCm,
        userWeight: weight,
        userBmi: bmi,
        systolic_BP: systolic,
        diastolic_BP: diastolic,
      }),
    });

    const updateData = await updateResponse.json();

    // Check if the backend returns an error
    if (updateData.error) {
      console.error("Frontend: Error updating data -", updateData.error);
      alert("Error updating data. Please try again.");
      return;
    }

    console.log("Frontend: Data updated successfully -", updateData);
    alert("Data successfully committed!");

  } catch (error) {
    console.error('Frontend: Error committing data:', error);
    alert("Error committing data. Please try again.");
  }
}

// Function to send the data and get blood pressure prediction
async function measureBP(event) {
  event.preventDefault(); // Prevent the default form submission

  // Get values from localStorage and form inputs
  const irValues = JSON.parse(localStorage.getItem('irValues'));
  const redValues = JSON.parse(localStorage.getItem('redValues'));
  const heartRate = localStorage.getItem('heartRate');
  const spo2 = localStorage.getItem('spo2');
  const age = parseInt(document.getElementById('age').value);
  const gender = document.getElementById('gender').value;
  const weight = parseInt(document.getElementById('weight').value);
  const feet = parseInt(document.getElementById('c-feet').value);
  const inches = parseInt(document.getElementById('c-inches').value);

  // Validate inputs
  if (!irValues || !redValues || isNaN(age) || !gender || isNaN(weight) || isNaN(feet) || isNaN(inches)) {
    alert("Please fill all the fields with valid data.");
    return;
  }

  // Convert feet and inches to cm
  const heightInCm = convertHeightToCm(feet, inches);

  // Calculate BMI
  const bmi = calculateBMI(weight, heightInCm);

  try {
    // Send the collected data to the backend for BP prediction
    //const response = await fetch('http://127.0.0.1:5000/predict', { // Flask API endpoint
    const response = await fetch('https://akasake-bp-monitor-api.hf.space/predict', { // Flask API endpoint
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ir: irValues,  // Send the IR values
        red: redValues,  // Send the RED values
        userAge: age,  // Send age
        userGender: gender,  // Send gender
        userHeight: heightInCm,  // Send height
        userWeight: weight,  // Send weight
        heartRate: heartRate,  // Send heart rate
        spo2: spo2,  // Send SPO2
        userBmi: bmi  // Send BMI
      }),
    });


    console.log(response);
    const data = await response.json();
    console.log(data);

    // Handle errors if any
    if (data.error) {
      console.error('Error:', data.error);
      alert("Error during prediction. Please try again.");
      return;
    }

    // Assuming the API returns a prediction object with systolic and diastolic BP
    const prediction = data.prediction[0];  // Flatten the nested array
    console.log("Prediction:", prediction);

    // Extract the systolic and diastolic values separately
    const systolicBP = prediction[0] !== undefined ? parseInt(prediction[0]) : 'N/A';
    const diastolicBP = prediction[1] !== undefined ? parseInt(prediction[1]) : 'N/A';

    // Display the predicted values on the page
    document.getElementById('bp-systolic').innerText = `${systolicBP} mmHg`;
    document.getElementById('bp-diastolic').innerText = `${diastolicBP} mmHg`;



    // Show the BP results section
    document.getElementById('bp-results').style.display = 'block';

  } catch (error) {
    console.error('Error calling the API:', error);
    alert("Error calling the prediction API. Please try again.");
  }
}


//-----------------------------//
//           AllData           //
//-----------------------------//

document.addEventListener("DOMContentLoaded", () => {

  const tableBody = document.getElementById("data-table-body");
  const totalCount = document.getElementById("total-count");

  // Fetch all the data from the backend (update URL)
  fetch("https://io-t-ppg-bp-monitor-backend.vercel.app/api/finalData") // Updated URL
    .then(response => response.json())
    .then(data => {
      totalCount.textContent = data.length;

      if (data.length === 0) {
        document.getElementById("no-data").style.display = "block";
        document.getElementById("data-table-section").style.display = "none";
      } else {
        document.getElementById("no-data").style.display = "none";
        document.getElementById("data-table-section").style.display = "block";

        // Loop through the fetched data and add rows to the table
        data.forEach(record => {
          const row = document.createElement("tr");

          const userBmiValue = !isNaN(record.userBmi) ? parseFloat(record.userBmi).toFixed(2) : 'N/A';

          row.innerHTML = `
            <td>${record.serialNumber || 'N/A'}</td>
            <td>${record.userAge || 'N/A'}</td>
            <td>${record.userGender || 'N/A'}</td>
            <td>${record.userHeight ? record.userHeight.toFixed(2) : 'N/A'}</td>
            <td>${record.userWeight || 'N/A'}</td>
            <td>${userBmiValue}</td>
            <td>${record.heartRate || 'N/A'}</td>
            <td>${record.spo2 || 'N/A'}</td>
            <td>${record.systolic_BP || 'N/A'}</td>
            <td>${record.diastolic_BP || 'N/A'}</td>
          `;
          tableBody.appendChild(row);
        });
      }
    })
    .catch(error => {
      console.error('Error fetching data:', error);
    });

  // Refresh the page on clicking refresh button
  document.getElementById("refresh-button").addEventListener("click", () => {
    window.location.reload();
  });
});
