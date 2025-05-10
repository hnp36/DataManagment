// Global variables
let surgeriesData = [];
let patientsData = [];
let surgeonsData = [];

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
  // Load initial data
  await loadPatients();
  await loadSurgeons();
  await loadAllSurgeries();
  
  // Set default dates
  const today = new Date().toISOString().split('T')[0];
  document.querySelector('input[name="surgeryDate"]').value = today;
  document.getElementById('roomDateFilter').value = today;
  document.getElementById('surgeonDateFilter').value = today;
  
  // Setup event listeners
  setupEventListeners();
});

// Load patients from API
async function loadPatients() {
  try {
    const response = await fetch('http://localhost:8000/api/patients');
    if (!response.ok) throw new Error('Failed to load patients');
    
    const data = await response.json();
    patientsData = data.patients || [];
    
    // Populate patient dropdowns
    const patientSelects = [
      document.getElementById('surgeryPatientSelect'),
      document.getElementById('patientFilter')
    ];
    
    patientSelects.forEach(select => {
      select.innerHTML = '<option value="">Select Patient</option>';
      patientsData.forEach(patient => {
        const option = document.createElement('option');
        option.value = patient.id;
        option.textContent = `${patient.name} (ID: ${patient.id})`;
        select.appendChild(option);
      });
    });
    
  } catch (error) {
    showMessage(`Error loading patients: ${error.message}`, false);
    console.error('Error loading patients:', error);
  }
}

// Load surgeons from API
async function loadSurgeons() {
  try {
    const response = await fetch('http://localhost:8000/api/surgeons');
    if (!response.ok) throw new Error('Failed to load surgeons');
    
    const data = await response.json();
    surgeonsData = data.surgeons || [];
    
    // Populate surgeon dropdowns
    const surgeonSelects = [
      document.getElementById('surgeonSelect'),
      document.getElementById('surgeonFilter')
    ];
    
    surgeonSelects.forEach(select => {
      select.innerHTML = '<option value="">Select Surgeon</option>';
      surgeonsData.forEach(surgeon => {
        const option = document.createElement('option');
        option.value = surgeon.id;
        option.textContent = `${surgeon.first_name} ${surgeon.last_name}`;
        select.appendChild(option);
      });
    });
    
  } catch (error) {
    showMessage(`Error loading surgeons: ${error.message}`, false);
    console.error('Error loading surgeons:', error);
  }
}

// Load all surgeries from API
async function loadAllSurgeries() {
  try {
    document.getElementById('surgeryLoading').classList.remove('d-none');
    
    const response = await fetch('http://localhost:8000/api/surgeries');
    if (!response.ok) throw new Error('Failed to load surgeries');
    
    const data = await response.json();
    surgeriesData = data.surgeries || [];
    
    // Update all views
    displaySurgeriesByRoom();
    displaySurgeriesBySurgeon();
    displaySurgeriesByPatient();
    
  } catch (error) {
    showMessage(`Error loading surgeries: ${error.message}`, false);
    console.error('Error loading surgeries:', error);
  } finally {
    document.getElementById('surgeryLoading').classList.add('d-none');
  }
}

// Setup event listeners
function setupEventListeners() {
  // Form submission
  document.getElementById('bookSurgeryForm').addEventListener('submit', bookSurgery);
  
  // Filter buttons
  document.getElementById('filterByRoomBtn').addEventListener('click', displaySurgeriesByRoom);
  document.getElementById('filterBySurgeonBtn').addEventListener('click', displaySurgeriesBySurgeon);
  document.getElementById('filterByPatientBtn').addEventListener('click', displaySurgeriesByPatient);
  
  // Cancel surgery confirmation
  document.getElementById('confirmCancelBtn').addEventListener('click', confirmCancelSurgery);
  
  // Tab change events to refresh data
  document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
    tab.addEventListener('shown.bs.tab', function() {
      if (this.id === 'by-room-tab') displaySurgeriesByRoom();
      if (this.id === 'by-surgeon-tab') displaySurgeriesBySurgeon();
      if (this.id === 'by-patient-tab') displaySurgeriesByPatient();
    });
  });
}

// Book a new surgery
async function bookSurgery(e) {
  e.preventDefault();
  
  const form = e.target;
  const loading = document.getElementById('surgeryLoading');
  const successMsg = document.getElementById('surgerySuccessMsg');
  const errorMsg = document.getElementById('surgeryErrorMsg');
  
  // Show loading, hide messages
  loading.classList.remove('d-none');
  successMsg.classList.add('d-none');
  errorMsg.classList.add('d-none');
  
  // Prepare data
  const formData = new FormData(form);
  const surgeryData = {
    patient_id: parseInt(formData.get('patientId')),
    surgeon_id: parseInt(formData.get('surgeonId')),
    surgery_type: formData.get('surgeryType'),
    room_number: formData.get('roomNumber'),
    surgery_date: formData.get('surgeryDate'),
    start_time: formData.get('startTime'),
    estimated_duration: parseInt(formData.get('duration')),
    notes: formData.get('notes'),
    status: 'Scheduled'
  };
  
  try {
    const response = await fetch('http://localhost:8000/api/surgeries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(surgeryData)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Failed to book surgery');
    }
    
    // Show success and reset form
    showMessage('Surgery booked successfully!', true);
    form.reset();
    
    // Refresh data
    await loadAllSurgeries();
    
  } catch (error) {
    showMessage(`Error: ${error.message}`, false);
    console.error('Error booking surgery:', error);
  } finally {
    loading.classList.add('d-none');
  }
}

// Display surgeries filtered by room
function displaySurgeriesByRoom() {
  const roomFilter = document.getElementById('roomFilter').value;
  const dateFilter = document.getElementById('roomDateFilter').value;
  
  let filteredSurgeries = [...surgeriesData];
  
  // Apply filters
  if (roomFilter) {
    filteredSurgeries = filteredSurgeries.filter(s => s.room_number === roomFilter);
  }
  if (dateFilter) {
    filteredSurgeries = filteredSurgeries.filter(s => s.surgery_date === dateFilter);
  }
  
  const tableBody = document.getElementById('roomSurgeryTable');
  renderSurgeries(filteredSurgeries, tableBody, 'room');
}

// Display surgeries filtered by surgeon
function displaySurgeriesBySurgeon() {
  const surgeonFilter = document.getElementById('surgeonFilter').value;
  const dateFilter = document.getElementById('surgeonDateFilter').value;
  
  let filteredSurgeries = [...surgeriesData];
  
  // Apply filters
  if (surgeonFilter) {
    filteredSurgeries = filteredSurgeries.filter(s => s.surgeon_id == surgeonFilter);
  }
  if (dateFilter) {
    filteredSurgeries = filteredSurgeries.filter(s => s.surgery_date === dateFilter);
  }
  
  const tableBody = document.getElementById('surgeonSurgeryTable');
  renderSurgeries(filteredSurgeries, tableBody, 'surgeon');
}

// Display surgeries filtered by patient
function displaySurgeriesByPatient() {
  const patientFilter = document.getElementById('patientFilter').value;
  
  let filteredSurgeries = [...surgeriesData];
  
  // Apply filter
  if (patientFilter) {
    filteredSurgeries = filteredSurgeries.filter(s => s.patient_id == patientFilter);
  }
  
  const tableBody = document.getElementById('patientSurgeryTable');
  renderSurgeries(filteredSurgeries, tableBody, 'patient');
}

// Render surgeries in a table
function renderSurgeries(surgeries, tableBody, viewType) {
  if (surgeries.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="${viewType === 'room' ? 8 : 7}" class="text-center">No surgeries found</td></tr>`;
    return;
  }
  
  let html = '';
  
  surgeries.forEach(surgery => {
    // Get patient and surgeon names
    const patient = patientsData.find(p => p.id === surgery.patient_id) || {};
    const surgeon = surgeonsData.find(s => s.id === surgery.surgeon_id) || {};
    
    const patientName = patient.name || `Patient ID: ${surgery.patient_id}`;
    const surgeonName = surgeon.first_name ? `${surgeon.first_name} ${surgeon.last_name}` : `Surgeon ID: ${surgery.surgeon_id}`;
    
    // Format date/time
    const formattedDate = new Date(surgery.surgery_date).toLocaleDateString();
    const formattedTime = formatTime(surgery.start_time);
    const endTime = calculateEndTime(surgery.start_time, surgery.estimated_duration);
    
    // Status badge
    const statusBadge = `<span class="badge ${getStatusBadgeClass(surgery.status)}">${surgery.status}</span>`;
    
    // Action buttons
    const actions = `
      <button class="btn btn-sm btn-outline-danger cancel-btn" data-id="${surgery.id}">
        Cancel
      </button>
    `;
    
    // Create row based on view type
    if (viewType === 'room') {
      html += `
        <tr>
          <td>${surgery.room_number}</td>
          <td>${patientName}</td>
          <td>${surgery.surgery_type}</td>
          <td>${formattedDate} ${formattedTime}-${endTime}</td>
          <td>${surgery.estimated_duration} hrs</td>
          <td>${surgeonName}</td>
          <td>${statusBadge}</td>
          <td>${actions}</td>
        </tr>
      `;
    } else if (viewType === 'surgeon') {
      html += `
        <tr>
          <td>${surgeonName}</td>
          <td>${patientName}</td>
          <td>${surgery.surgery_type}</td>
          <td>${surgery.room_number}</td>
          <td>${formattedDate} ${formattedTime}-${endTime}</td>
          <td>${statusBadge}</td>
          <td>${actions}</td>
        </tr>
      `;
    } else if (viewType === 'patient') {
      html += `
        <tr>
          <td>${patientName}</td>
          <td>${surgery.surgery_type}</td>
          <td>${surgeonName}</td>
          <td>${surgery.room_number}</td>
          <td>${formattedDate} ${formattedTime}-${endTime}</td>
          <td>${statusBadge}</td>
          <td>${actions}</td>
        </tr>
      `;
    }
  });
  
  tableBody.innerHTML = html;
  
  // Add event listeners to cancel buttons
  document.querySelectorAll('.cancel-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      document.getElementById('surgeryIdToCancel').value = this.dataset.id;
      const modal = new bootstrap.Modal(document.getElementById('cancelSurgeryModal'));
      modal.show();
    });
  });
}

// Confirm cancel surgery
async function confirmCancelSurgery() {
  const surgeryId = document.getElementById('surgeryIdToCancel').value;
  const modal = bootstrap.Modal.getInstance(document.getElementById('cancelSurgeryModal'));
  
  try {
    document.getElementById('surgeryLoading').classList.remove('d-none');
    
    const response = await fetch(`http://localhost:8000/api/surgeries/${surgeryId}/cancel`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'Cancelled' })
    });
    
    if (!response.ok) throw new Error('Failed to cancel surgery');
    
    showMessage('Surgery cancelled successfully', true);
    modal.hide();
    await loadAllSurgeries();
    
  } catch (error) {
    showMessage(`Error: ${error.message}`, false);
    console.error('Error cancelling surgery:', error);
  } finally {
    document.getElementById('surgeryLoading').classList.add('d-none');
  }
}

// Helper function to format time
function formatTime(timeString) {
  if (!timeString) return '';
  if (typeof timeString === 'string' && timeString.includes(':')) {
    return timeString.substring(0, 5); // Return HH:MM format
  }
  return timeString;
}

// Helper function to calculate end time
function calculateEndTime(startTime, duration) {
  if (!startTime || !duration) return '';
  
  // Parse start time
  const [hours, minutes] = startTime.split(':').map(Number);
  
  // Calculate end time
  const endHours = hours + parseInt(duration);
  const formattedHours = endHours % 24; // Handle overflow
  return `${formattedHours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

// Helper function to get status badge class
function getStatusBadgeClass(status) {
  switch(status) {
    case 'Completed': return 'bg-success';
    case 'In Progress': return 'bg-warning text-dark';
    case 'Cancelled': return 'bg-danger';
    default: return 'bg-primary';
  }
}

// Helper function to show messages
function showMessage(message, isSuccess) {
  const successMsg = document.getElementById('surgerySuccessMsg');
  const errorMsg = document.getElementById('surgeryErrorMsg');
  
  if (isSuccess) {
    successMsg.textContent = message;
    successMsg.classList.remove('d-none');
    errorMsg.classList.add('d-none');
    
    // Hide after 3 seconds
    setTimeout(() => {
      successMsg.classList.add('d-none');
    }, 3000);
  } else {
    errorMsg.textContent = message;
    errorMsg.classList.remove('d-none');
    successMsg.classList.add('d-none');
  }
}