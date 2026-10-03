"use strict";

const byId = (id) => document.getElementById(id);
const utcToday = () => new Date().toISOString().slice(0, 10);
let token = "";
let user = null;
let vehicles = [];
let drivers = [];
let latest = [];
let selectedVehicle = "";
let editingVehicleId = "";
let editingDriverId = "";
let historyPoints = [];
let nextHistoryOffset = null;
let map = null;
let markers = null;
let track = null;
let mapFitted = false;
let timer = null;
let refreshing = false;

function setText(id, value) {
  byId(id).textContent = value == null ? "—" : String(value);
}
function message(value, error = false) {
  byId("message").textContent = value;
  byId("message").classList.toggle("error", error);
}
function element(tag, className, value) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (value != null) item.textContent = String(value);
  return item;
}
function formatTime(value) {
  if (!value) return "Chưa có";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString("vi-VN", {timeZone: "Asia/Ho_Chi_Minh"});
}
function validPoint(point) {
  const lat = Number(point.lat), lng = Number(point.lng);
  return Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
}
function logout(reason = "") {
  token = "";
  user = null;
  vehicles = drivers = latest = historyPoints = [];
  selectedVehicle = editingVehicleId = editingDriverId = "";
  if (timer) clearInterval(timer);
  timer = null;
  if (map) map.remove();
  map = markers = track = null;
  mapFitted = false;
  byId("dashboard").hidden = true;
  byId("login-view").hidden = false;
  byId("logout").hidden = true;
  byId("password").value = "";
  setText("identity", "");
  setText("connection", "Chưa đăng nhập");
  setText("login-message", reason);
}
async function api(path, options = {}) {
  const headers = {...(options.headers || {})};
  if (token) headers.Authorization = "Bearer " + token;
  const response = await fetch(path, {...options, headers});
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof body?.detail === "string" ? body.detail : "Máy chủ trả lỗi " + response.status;
    if (response.status === 401 && path !== "/api/auth/login") logout("Phiên đăng nhập đã hết hạn.");
    throw new Error(detail);
  }
  return body;
}
function report(error) {
  message(error instanceof Error ? error.message : String(error), true);
}

function makeMap() {
  map = L.map("map").setView([10.7769, 106.7009], 11);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 18
  }).addTo(map);
  markers = L.layerGroup().addTo(map);
}
function drawMap() {
  if (!map) return;
  markers.clearLayers();
  const bounds = [];
  for (const vehicle of vehicles) {
    const point = latest.find((row) => row.vehicle_id === vehicle.vehicle_id);
    if (!point || !validPoint(point)) continue;
    const position = [Number(point.lat), Number(point.lng)];
    bounds.push(position);
    const marker = L.circleMarker(position, {
      radius: vehicle.vehicle_id === selectedVehicle ? 10 : 7,
      color: vehicle.status === "RUNNING" ? "#087d67" : "#42697d",
      fillOpacity: 0.9, weight: 2
    }).addTo(markers);
    const popup = element("div", "", vehicle.plate + " · " + vehicle.vehicle_id + " · " + formatTime(point.event_time));
    marker.bindPopup(popup);
    marker.on("click", () => selectVehicle(vehicle.vehicle_id).catch(report));
  }
  setText("map-summary", bounds.length + " xe có tọa độ (kiểm tra thời gian cập nhật)");
  if (bounds.length && !mapFitted) {
    map.fitBounds(bounds, {padding: [30, 30], maxZoom: 13});
    mapFitted = true;
  }
}
function renderVehicles() {
  const list = byId("vehicle-list");
  list.replaceChildren();
  const status = byId("status-filter").value;
  const shown = vehicles.filter((vehicle) => !status || vehicle.status === status);
  if (!shown.length) list.append(element("p", "muted", "Không có xe trong bộ lọc này."));
  for (const vehicle of shown) {
    const point = latest.find((row) => row.vehicle_id === vehicle.vehicle_id);
    const button = element("button", "vehicle-item" + (vehicle.vehicle_id === selectedVehicle ? " selected" : ""));
    button.type = "button";
    button.append(element("strong", "", vehicle.plate + " · " + vehicle.vehicle_id));
    button.append(element("small", "", vehicle.model + " · " + vehicle.status));
    button.append(element("small", "", point ? Number(point.speed).toFixed(1) + " km/h · " + formatTime(point.event_time) : "Chưa có GPS"));
    button.addEventListener("click", () => selectVehicle(vehicle.vehicle_id).catch(report));
    list.append(button);
  }
  setText("vehicle-count", vehicles.length);
}
function canWrite() {
  return user && (user.role === "ADMIN" || user.role === "DISPATCHER");
}
function fillDriverChoices(selected = "") {
  const select = byId("vehicle-driver");
  select.replaceChildren();
  const none = element("option", "", "Chưa gán");
  none.value = "";
  select.append(none);
  for (const driver of drivers.filter((row) => row.active)) {
    const option = element("option", "", driver.full_name + " · " + driver.driver_id);
    option.value = driver.driver_id;
    select.append(option);
  }
  select.value = selected || "";
}
function fillTripChoices() {
  const vehicleSelect = byId("trip-vehicle");
  const driverSelect = byId("trip-driver");
  const selected = vehicleSelect.value;
  vehicleSelect.replaceChildren();
  driverSelect.replaceChildren();
  for (const vehicle of vehicles.filter((row) =>
    row.current_driver_id && row.status !== "INACTIVE" && row.status !== "MAINTENANCE" &&
    drivers.some((driver) => driver.driver_id === row.current_driver_id && driver.active))) {
    const option = element("option", "", vehicle.plate + " · " + vehicle.vehicle_id);
    option.value = vehicle.vehicle_id;
    vehicleSelect.append(option);
  }
  vehicleSelect.value = Array.from(vehicleSelect.options).some((option) => option.value === selected)
    ? selected : vehicleSelect.options[0]?.value || "";
  const vehicle = vehicles.find((row) => row.vehicle_id === vehicleSelect.value);
  const driver = drivers.find((row) => row.driver_id === vehicle?.current_driver_id);
  if (driver) {
    const option = element("option", "", driver.full_name + " · " + driver.driver_id);
    option.value = driver.driver_id;
    driverSelect.append(option);
  }
  byId("trip-form").querySelector('button[type="submit"]').disabled = !driver;
}
function newVehicle() {
  editingVehicleId = "";
  byId("vehicle-form").reset();
  byId("vehicle-id").disabled = false;
  fillDriverChoices();
  byId("vehicle-admin").open = true;
}
function editVehicle() {
  const vehicle = vehicles.find((row) => row.vehicle_id === selectedVehicle);
  if (!vehicle) return;
  editingVehicleId = vehicle.vehicle_id;
  byId("vehicle-id").value = vehicle.vehicle_id;
  byId("vehicle-id").disabled = true;
  byId("vehicle-plate").value = vehicle.plate;
  byId("vehicle-model").value = vehicle.model;
  byId("vehicle-status").value = vehicle.status;
  byId("vehicle-speed").value = vehicle.speed_limit;
  fillDriverChoices(vehicle.current_driver_id);
  byId("vehicle-admin").open = true;
}
function newDriver() {
  editingDriverId = "";
  byId("driver-form").reset();
  byId("driver-id").disabled = false;
  byId("driver-admin").open = true;
}
function editDriver(driver) {
  editingDriverId = driver.driver_id;
  byId("driver-id").value = driver.driver_id;
  byId("driver-id").disabled = true;
  byId("driver-name").value = driver.full_name;
  byId("driver-license").value = driver.license_number;
  byId("driver-phone").value = driver.phone;
  byId("driver-admin").open = true;
}
function renderDrivers() {
  const list = byId("driver-list");
  list.replaceChildren();
  setText("driver-count", drivers.length);
  fillDriverChoices(byId("vehicle-driver").value);
  if (!drivers.length) list.append(element("p", "muted", "Chưa có tài xế."));
  for (const driver of drivers) {
    const item = element("div", "item");
    item.append(element("strong", "", driver.full_name + " · " + driver.driver_id));
    item.append(element("small", "", driver.license_number + " · " + (driver.active ? "Đang làm việc" : "Ngừng")));
    if (canWrite()) {
      const actions = element("div", "item-actions");
      const edit = element("button", "", "Sửa");
      edit.type = "button";
      edit.addEventListener("click", () => editDriver(driver));
      const toggle = element("button", "", driver.active ? "Khóa" : "Kích hoạt");
      toggle.type = "button";
      toggle.addEventListener("click", async () => {
        toggle.disabled = true;
        try {
          await api("/api/fleet/drivers/" + encodeURIComponent(driver.driver_id), {
            method: "PATCH", headers: {"Content-Type": "application/json"},
            body: JSON.stringify({active: !driver.active})
          });
          await loadDrivers();
          message("Đã cập nhật tài xế trong CSDL.");
        } catch (error) {
          report(error);
          toggle.disabled = false;
        }
      });
      actions.append(edit, toggle);
      item.append(actions);
    }
    list.append(item);
  }
}
async function loadFleet() {
  vehicles = await api("/api/fleet/vehicles");
  byId("status-filter").value = "";
  renderVehicles();
  drawMap();
  fillTripChoices();
}
async function loadDrivers() {
  drivers = await api("/api/fleet/drivers");
  renderDrivers();
  fillTripChoices();
}
function renderHistory() {
  const list = byId("history-list");
  list.replaceChildren();
  if (track) map.removeLayer(track);
  track = null;
  const route = historyPoints.filter(validPoint).map((point) => [Number(point.lat), Number(point.lng)]);
  if (route.length) {
    track = L.polyline(route, {color: "#e98945", weight: 4}).addTo(map);
    if (route.length > 1) map.fitBounds(track.getBounds(), {padding: [30, 30], maxZoom: 14});
    else map.setView(route[0], 13);
  }
  setText("history-summary", historyPoints.length + " bản ghi GPS ngày " + byId("history-date").value + " (UTC).");
  if (!historyPoints.length) list.append(element("p", "muted", "Không có GPS cho ngày này."));
  for (const point of historyPoints.slice(-12).reverse()) {
    const item = element("div", "item");
    item.append(element("strong", "", formatTime(point.event_time) + " · " + Number(point.speed).toFixed(1) + " km/h"));
    item.append(element("small", "", Number(point.lat).toFixed(5) + ", " + Number(point.lng).toFixed(5)));
    list.append(item);
  }
  byId("history-more").hidden = nextHistoryOffset == null || nextHistoryOffset > 10000;
}
async function loadHistory(more = false) {
  if (!selectedVehicle || !byId("history-date").value) return;
  const offset = more ? nextHistoryOffset : 0;
  if (offset == null) return;
  const requestKey = selectedVehicle + "|" + byId("history-date").value;
  const params = new URLSearchParams({vehicle_id: selectedVehicle, date_str: byId("history-date").value, limit: "2000", offset: String(offset)});
  byId("history-more").disabled = true;
  try {
  const result = await api("/api/tracking/history?" + params);
  if (requestKey !== selectedVehicle + "|" + byId("history-date").value) return;
  historyPoints = more ? historyPoints.concat(result.points) : result.points;
  nextHistoryOffset = result.next_offset;
  renderHistory();
  } finally {
    byId("history-more").disabled = false;
  }
}
async function selectVehicle(vehicleId) {
  selectedVehicle = vehicleId;
  const vehicle = vehicles.find((item) => item.vehicle_id === vehicleId);
  byId("vehicle-edit").disabled = !vehicle;
  const point = latest.find((item) => item.vehicle_id === vehicleId);
  setText("selected-vehicle", vehicle ? vehicle.plate + " · " + vehicleId : vehicleId);
  if (point?.event_time) byId("history-date").value = point.event_time.slice(0, 10);
  byId("history-load").disabled = false;
  renderVehicles();
  drawMap();
  await loadHistory();
}
function renderSimpleList(containerId, rows, describe, emptyText) {
  const list = byId(containerId);
  list.replaceChildren();
  if (!rows.length) list.append(element("p", "muted", emptyText));
  for (const row of rows) {
    const item = element("div", "item");
    const [title, detail] = describe(row);
    item.append(element("strong", "", title));
    item.append(element("small", "", detail));
    list.append(item);
  }
}
async function loadTrips() {
  const rows = await api("/api/fleet/trips?trip_date=" + encodeURIComponent(byId("trip-date").value));
  setText("trip-count", rows.length);
  renderSimpleList("trip-list", rows, (row) => [
    row.trip_id + " · " + row.status,
    row.vehicle_id + " · " + row.origin + " → " + row.destination + " · " + formatTime(row.start_time)
  ], "Không có chuyến trong ngày đã chọn.");
}
async function loadAlerts() {
  const rows = await api("/api/tracking/alerts?date_str=" + encodeURIComponent(byId("alert-date").value));
  const list = byId("alert-list");
  list.replaceChildren();
  if (!rows.length) list.append(element("p", "muted", "Không có cảnh báo trong ngày đã chọn."));
  for (const row of rows) {
    const item = element("div", "item");
    item.append(element("strong", "", row.alert_type + " · " + row.vehicle_id + " · " + row.status));
    item.append(element("small", "", row.details + " · " + formatTime(row.created_at)));
    if (user.role !== "VIEWER" && row.status !== "RESOLVED") {
      const actions = element("div", "item-actions");
      for (const status of (row.status === "OPEN" ? ["ACKNOWLEDGED", "RESOLVED"] : ["RESOLVED"])) {
        const button = element("button", "", status === "ACKNOWLEDGED" ? "Xác nhận" : "Đã xử lý");
        button.type = "button";
        button.addEventListener("click", async () => {
          button.disabled = true;
          try {
            await api("/api/tracking/alerts/action", {
              method: "POST", headers: {"Content-Type": "application/json"},
              body: JSON.stringify({alert_id: String(row.alert_id), status})
            });
            await loadAlerts();
            message("Đã cập nhật cảnh báo trong CSDL.");
          } catch (error) {
            report(error);
            button.disabled = false;
          }
        });
        actions.append(button);
      }
      item.append(actions);
    }
    list.append(item);
  }
}
async function loadUsers() {
  const rows = await api("/api/users");
  const list = byId("user-list");
  list.replaceChildren();
  if (!rows.length) list.append(element("p", "muted", "Chưa có tài khoản."));
  for (const row of rows) {
    const item = element("div", "item");
    item.append(element("strong", "", row.full_name + " · " + row.username));
    item.append(element("small", "", row.role + " · " + (row.active ? "Hoạt động" : "Đã khóa")));
    const actions = element("div", "item-actions");
    const role = element("select");
    role.setAttribute("aria-label", "Vai trò của " + row.username);
    for (const value of ["ADMIN", "DISPATCHER", "VIEWER"]) {
      const option = element("option", "", value);
      option.value = value;
      role.append(option);
    }
    role.value = row.role;
    role.disabled = row.username === user.username;
    role.addEventListener("change", async () => {
      try {
        await api("/api/users/" + encodeURIComponent(row.username), {
          method: "PATCH", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({role: role.value})
        });
        await loadUsers();
        message("Đã cập nhật quyền trong CSDL.");
      } catch (error) {
        role.value = row.role;
        report(error);
      }
    });
    const toggle = element("button", "", row.active ? "Khóa" : "Kích hoạt");
    toggle.type = "button";
    toggle.disabled = row.username === user.username;
    toggle.addEventListener("click", async () => {
      toggle.disabled = true;
      try {
        await api("/api/users/" + encodeURIComponent(row.username), {
          method: "PATCH", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({active: !row.active})
        });
        await loadUsers();
        message("Đã cập nhật tài khoản trong CSDL.");
      } catch (error) {
        report(error);
        toggle.disabled = false;
      }
    });
    actions.append(role, toggle);
    item.append(actions);
    list.append(item);
  }
}
async function refreshLatest() {
  if (!token || refreshing) return;
  refreshing = true;
  try {
    const [points, moving] = await Promise.all([
      api("/api/tracking/latest"),
      api("/api/tracking/recent-moving?minutes=15")
    ]);
    latest = points;
    setText("moving-count", moving.length);
    renderVehicles();
    drawMap();
    setText("connection", "Đang đọc CSDL");
  } catch (error) {
    if (token) {
      report(error);
      setText("connection", "Mất kết nối CSDL");
    }
  } finally {
    refreshing = false;
  }
}
async function refreshAll() {
  const [health, fleet, driverRows] = await Promise.all([
    api("/api/health"), api("/api/fleet/vehicles"), api("/api/fleet/drivers")
  ]);
  vehicles = fleet;
  drivers = driverRows;
  renderDrivers();
  fillTripChoices();
  if (user.role === "ADMIN") await loadUsers();
  await Promise.all([loadTrips(), loadAlerts(), refreshLatest()]);
  setText("connection", "ScyllaDB " + health.release_version);
  message("Dữ liệu được đọc qua API; bản đồ tự làm mới GPS mỗi 5 giây.");
}

byId("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  setText("login-message", "");
  try {
    const login = await api("/api/auth/login", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({username: byId("username").value.trim(), password: byId("password").value})
    });
    token = login.access_token;
    user = await api("/api/auth/me");
    byId("login-view").hidden = true;
    byId("dashboard").hidden = false;
    byId("logout").hidden = false;
    byId("users-panel").hidden = user.role !== "ADMIN";
    byId("vehicle-edit").hidden = !canWrite();
    byId("vehicle-admin").hidden = !canWrite();
    byId("driver-admin").hidden = !canWrite();
    byId("trip-admin").hidden = !canWrite();
    setText("identity", user.full_name + " · " + user.role);
    makeMap();
    map.invalidateSize();
    await refreshAll();
    timer = setInterval(refreshLatest, 5000);
  } catch (error) {
    if (!user) logout(error.message);
    else report(error);
  } finally {
    button.disabled = false;
  }
});
byId("logout").addEventListener("click", () => logout());
byId("vehicle-edit").addEventListener("click", editVehicle);
byId("vehicle-new").addEventListener("click", newVehicle);
byId("driver-new").addEventListener("click", newDriver);
byId("vehicle-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  const vehicleId = byId("vehicle-id").value.trim();
  const payload = {
    plate: byId("vehicle-plate").value.trim(),
    model: byId("vehicle-model").value.trim(),
    current_driver_id: byId("vehicle-driver").value || null,
    status: byId("vehicle-status").value,
    speed_limit: Number(byId("vehicle-speed").value)
  };
  if (!editingVehicleId) payload.vehicle_id = vehicleId;
  try {
    await api("/api/fleet/vehicles" + (editingVehicleId ? "/" + encodeURIComponent(editingVehicleId) : ""), {
      method: editingVehicleId ? "PATCH" : "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    newVehicle();
    byId("vehicle-admin").open = false;
    await loadFleet();
    message("Đã lưu xe trong CSDL.");
  } catch (error) {
    report(error);
  } finally {
    button.disabled = false;
  }
});
byId("driver-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  const payload = {
    full_name: byId("driver-name").value.trim(),
    license_number: byId("driver-license").value.trim(),
    phone: byId("driver-phone").value.trim()
  };
  if (!editingDriverId) payload.driver_id = byId("driver-id").value.trim();
  try {
    await api("/api/fleet/drivers" + (editingDriverId ? "/" + encodeURIComponent(editingDriverId) : ""), {
      method: editingDriverId ? "PATCH" : "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    newDriver();
    byId("driver-admin").open = false;
    await loadDrivers();
    message("Đã lưu tài xế trong CSDL.");
  } catch (error) {
    report(error);
  } finally {
    button.disabled = false;
  }
});
byId("trip-vehicle").addEventListener("change", fillTripChoices);
byId("trip-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    await api("/api/fleet/trips", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        trip_id: byId("trip-id").value.trim(),
        vehicle_id: byId("trip-vehicle").value,
        driver_id: byId("trip-driver").value,
        origin: byId("trip-origin").value.trim(),
        destination: byId("trip-destination").value.trim()
      })
    });
    byId("trip-form").reset();
    fillTripChoices();
    byId("trip-admin").open = false;
    byId("trip-date").value = utcToday();
    await loadTrips();
    message("Đã tạo chuyến PLANNED trong CSDL.");
  } catch (error) {
    report(error);
  } finally {
    button.disabled = !byId("trip-driver").value;
  }
});
byId("user-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    await api("/api/users", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        username: byId("new-username").value.trim(),
        password: byId("new-password").value,
        full_name: byId("new-fullname").value.trim(),
        role: byId("new-role").value
      })
    });
    byId("user-form").reset();
    await loadUsers();
    message("Đã tạo tài khoản trong CSDL.");
  } catch (error) {
    report(error);
  } finally {
    button.disabled = false;
  }
});
byId("refresh").addEventListener("click", () => refreshAll().catch(report));
byId("status-filter").addEventListener("change", renderVehicles);
byId("history-load").addEventListener("click", () => loadHistory().catch(report));
byId("history-more").addEventListener("click", () => loadHistory(true).catch(report));
byId("history-date").addEventListener("change", () => loadHistory().catch(report));
byId("trip-date").addEventListener("change", () => loadTrips().catch(report));
byId("alert-date").addEventListener("change", () => loadAlerts().catch(report));
byId("history-date").value = utcToday();
byId("trip-date").value = utcToday();
byId("alert-date").value = utcToday();
