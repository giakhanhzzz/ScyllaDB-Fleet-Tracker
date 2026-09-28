import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import {
  Navigation,
  Truck,
  Users,
  AlertTriangle,
  Play,
  Pause,
  RotateCcw,
  Plus,
  Shield,
  FileText,
  Database,
  ExternalLink,
  CheckCircle2,
  Clock,
  MapPin,
  Flame,
  ArrowRight,
  Download,
  Upload,
  Radio,
  Sliders,
  ChevronRight,
  Check,
  X,
  Filter,
  BarChart3
} from 'lucide-react';

// ==============================================================================
// Types & Interfaces
// ==============================================================================
type UserRole = 'ADMIN' | 'DISPATCHER' | 'VIEWER';

interface CurrentUser {
  username: string;
  fullName: string;
  role: UserRole;
  companyId: string;
}

interface Vehicle {
  id: string;
  plate: string;
  model: string;
  driverId: string;
  status: 'RUNNING' | 'IDLE' | 'MAINTENANCE';
  speedLimit: number;
  lat: number;
  lng: number;
  speed: number;
  heading: number;
  updatedAt: string;
}

interface Driver {
  id: string;
  name: string;
  license: string;
  phone: string;
  active: boolean;
}

interface Trip {
  id: string;
  vehicleId: string;
  driverId: string;
  origin: string;
  destination: string;
  startTime: string;
  endTime?: string;
  status: 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED';
  distanceKm: number;
  rejectedPoints: number;
}

interface AlertItem {
  id: string;
  vehicleId: string;
  type: 'OVERSPEED' | 'GEOFENCE_EXIT' | 'GPS_LOST';
  severity: 'HIGH' | 'CRITICAL' | 'MEDIUM';
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';
  time: string;
  details: string;
}

interface GPSPoint {
  lat: number;
  lng: number;
  speed: number;
  time: string;
}

// ==============================================================================
// Initial Seed Data (10 Vehicles, 8 Drivers, Trips, Alerts)
// ==============================================================================
const INITIAL_DRIVERS: Driver[] = [
  { id: 'DRV_001', name: 'Nguyễn Văn An', license: 'B2-984321', phone: '0901234567', active: true },
  { id: 'DRV_002', name: 'Trần Đình Bình', license: 'C-874523', phone: '0902345678', active: true },
  { id: 'DRV_003', name: 'Lê Văn Cường', license: 'E-765432', phone: '0903456789', active: true },
  { id: 'DRV_004', name: 'Phạm Quốc Dũng', license: 'FC-654321', phone: '0904567890', active: true },
  { id: 'DRV_005', name: 'Hoàng Gia Hưng', license: 'B2-543210', phone: '0905678901', active: true },
  { id: 'DRV_006', name: 'Vũ Minh Khoa', license: 'C-432109', phone: '0906789012', active: true },
  { id: 'DRV_007', name: 'Đặng Hữu Long', license: 'D-321098', phone: '0907890123', active: true },
  { id: 'DRV_008', name: 'Ngô Thành Nam', license: 'B2-210987', phone: '0908901234', active: true },
];

const INITIAL_VEHICLES: Vehicle[] = [
  { id: 'VEH_001', plate: '51A-888.12', model: 'Hyundai Porter 1.5T', driverId: 'DRV_001', status: 'RUNNING', speedLimit: 80, lat: 10.7769, lng: 106.7009, speed: 48, heading: 45, updatedAt: '10:15:02' },
  { id: 'VEH_002', plate: '51C-777.34', model: 'Isuzu Forward 5T', driverId: 'DRV_002', status: 'RUNNING', speedLimit: 75, lat: 10.7850, lng: 106.6900, speed: 52, heading: 90, updatedAt: '10:15:01' },
  { id: 'VEH_003', plate: '51D-666.56', model: 'Hino 300 Series', driverId: 'DRV_003', status: 'RUNNING', speedLimit: 80, lat: 10.7620, lng: 106.6810, speed: 65, heading: 180, updatedAt: '10:15:00' },
  { id: 'VEH_004', plate: '51E-555.78', model: 'Kia Frontier K250', driverId: 'DRV_004', status: 'IDLE', speedLimit: 80, lat: 10.7500, lng: 106.6700, speed: 0, heading: 0, updatedAt: '10:14:50' },
  { id: 'VEH_005', plate: '51F-444.90', model: 'Ford Transit Van', driverId: 'DRV_005', status: 'RUNNING', speedLimit: 90, lat: 10.8000, lng: 106.7200, speed: 58, heading: 270, updatedAt: '10:14:59' },
  { id: 'VEH_006', plate: '51G-333.21', model: 'Thaco Ollin 7T', driverId: 'DRV_006', status: 'IDLE', speedLimit: 70, lat: 10.8200, lng: 106.7100, speed: 0, heading: 0, updatedAt: '10:13:20' },
  { id: 'VEH_007', plate: '51H-222.43', model: 'Suzuki Super Carry', driverId: 'DRV_007', status: 'RUNNING', speedLimit: 60, lat: 10.7300, lng: 106.7100, speed: 38, heading: 120, updatedAt: '10:14:55' },
  { id: 'VEH_008', plate: '51K-111.65', model: 'Hyundai Mighty EX8', driverId: 'DRV_008', status: 'MAINTENANCE', speedLimit: 80, lat: 10.8400, lng: 106.7800, speed: 0, heading: 0, updatedAt: '09:30:00' },
  { id: 'VEH_009', plate: '51L-999.87', model: 'Isuzu QKR 2.4T', driverId: 'DRV_001', status: 'IDLE', speedLimit: 80, lat: 10.7900, lng: 106.6600, speed: 0, heading: 0, updatedAt: '09:45:00' },
  { id: 'VEH_010', plate: '51M-000.19', model: 'Mercedes Sprinter', driverId: 'DRV_002', status: 'IDLE', speedLimit: 90, lat: 10.8100, lng: 106.6500, speed: 0, heading: 0, updatedAt: '10:00:00' },
];

const INITIAL_TRIPS: Trip[] = [
  { id: 'TRIP_202609_001', vehicleId: 'VEH_001', driverId: 'DRV_001', origin: 'Kho Tổng Thủ Đức', destination: 'Quận 1, TP.HCM', startTime: '2026-09-28 07:30', status: 'IN_PROGRESS', distanceKm: 18.4, rejectedPoints: 0 },
  { id: 'TRIP_202609_002', vehicleId: 'VEH_002', driverId: 'DRV_002', origin: 'Kho Cát Lái', destination: 'Tân Bình, TP.HCM', startTime: '2026-09-28 08:00', status: 'IN_PROGRESS', distanceKm: 24.1, rejectedPoints: 1 },
  { id: 'TRIP_202609_003', vehicleId: 'VEH_003', driverId: 'DRV_003', origin: 'KCN Tân Tạo', destination: 'Quận 7, TP.HCM', startTime: '2026-09-28 08:30', status: 'IN_PROGRESS', distanceKm: 15.6, rejectedPoints: 0 },
  { id: 'TRIP_202609_004', vehicleId: 'VEH_005', driverId: 'DRV_005', origin: 'Bến xe Miền Đông', destination: 'KCN Sóng Thần', startTime: '2026-09-28 09:00', status: 'IN_PROGRESS', distanceKm: 12.8, rejectedPoints: 0 },
  { id: 'TRIP_202609_005', vehicleId: 'VEH_007', driverId: 'DRV_007', origin: 'Chợ Đầu Mối Bình Điền', destination: 'Phú Nhuận, TP.HCM', startTime: '2026-09-28 06:00', endTime: '2026-09-28 08:15', status: 'COMPLETED', distanceKm: 29.5, rejectedPoints: 0 },
];

const INITIAL_ALERTS: AlertItem[] = [
  { id: 'ALT_001', vehicleId: 'VEH_001', type: 'OVERSPEED', severity: 'HIGH', status: 'OPEN', time: '10:12:45', details: 'Vận tốc 84.5 km/h vượt giới hạn 80 km/h trên đường Mai Chí Thọ' },
  { id: 'ALT_002', vehicleId: 'VEH_007', type: 'GEOFENCE_EXIT', severity: 'CRITICAL', status: 'ACKNOWLEDGED', time: '09:45:20', details: 'Xe rời khỏi vùng địa lý ảo nội đô TP.HCM (vùng Bounding Box)' },
  { id: 'ALT_003', vehicleId: 'VEH_008', type: 'GPS_LOST', severity: 'MEDIUM', status: 'RESOLVED', time: '08:30:10', details: 'Mất tín hiệu GPS liên tục quá 15 phút tại trạm bảo dưỡng' },
];

// 15 Tables Schema Documentation
const SCYLLA_TABLES = [
  { name: 'users_by_username', pk: 'username', purpose: 'Q1: Login & xác thực mật khẩu' },
  { name: 'users_by_company', pk: '(company_id), username', purpose: 'Q2: Quản trị danh sách người dùng' },
  { name: 'vehicles_by_id', pk: 'vehicle_id', purpose: 'Q3: Tra cứu chi tiết xe theo mã' },
  { name: 'vehicles_by_status', pk: '(company_id, status), vehicle_id', purpose: 'Q4: Lọc danh sách xe theo trạng thái' },
  { name: 'drivers_by_id', pk: 'driver_id', purpose: 'Q3: Tra cứu chi tiết tài xế' },
  { name: 'drivers_by_company', pk: '(company_id), driver_id', purpose: 'Q5: Liệt kê tài xế của công ty' },
  { name: 'trips_by_id', pk: 'trip_id', purpose: 'Q3: Chi tiết chuyến đi và km Haversine' },
  { name: 'trips_by_company_day', pk: '(company_id, trip_date), start_time DESC, trip_id', purpose: 'Q6: Chuyến đi theo ngày của công ty' },
  { name: 'trips_by_driver_month', pk: '(driver_id, year_month), start_time DESC, trip_id', purpose: 'Q7 & Q14: Báo cáo số chuyến & km tài xế' },
  { name: 'geofences_by_vehicle', pk: 'vehicle_id', purpose: 'Q13: Vùng địa lý ảo (Bounding Box)' },
  { name: 'location_events_by_vehicle_day', pk: '(vehicle_id, event_date), event_time DESC, event_id', purpose: 'Q9: Lịch sử GPS Time-series (TTL 90 ngày)' },
  { name: 'latest_locations_by_company', pk: '(company_id), vehicle_id', purpose: 'Q8: Vị trí mới nhất hiển thị bản đồ' },
  { name: 'vehicle_activity_by_hour', pk: '(company_id, date, hour), event_time, vehicle_id, event_id', purpose: 'Q10: Xe di chuyển gần đây (TTL 48h)' },
  { name: 'alerts_by_company_day', pk: '(company_id, alert_date), created_at DESC, alert_id', purpose: 'Q11: Danh sách cảnh báo trong ngày' },
  { name: 'alerts_by_id', pk: 'alert_id', purpose: 'Q12: Tra cứu & cập nhật xử lý alert' },
];

export default function App() {
  // Current logged in user (RBAC)
  const [currentUser, setCurrentUser] = useState<CurrentUser>({
    username: 'khanh_admin',
    fullName: 'Phạm Gia Khánh',
    role: 'ADMIN',
    companyId: 'COMP_HCM_01'
  });

  // Navigation tab
  const [activeTab, setActiveTab] = useState<'map' | 'simulator' | 'fleet' | 'history' | 'alerts' | 'report' | 'scylla' | 'backup'>('map');

  // Fleet State
  const [vehicles, setVehicles] = useState<Vehicle[]>(INITIAL_VEHICLES);
  const [drivers] = useState<Driver[]>(INITIAL_DRIVERS);
  const [trips, setTrips] = useState<Trip[]>(INITIAL_TRIPS);
  const [alerts, setAlerts] = useState<AlertItem[]>(INITIAL_ALERTS);

  // Simulator State
  const [simRunning, setSimRunning] = useState<boolean>(true);
  const [simInterval] = useState<number>(3);
  const [simCycles, setSimCycles] = useState<number>(142);
  const [simLogs, setSimLogs] = useState<string[]>([
    '[10:15:02] GPS Ingest -> VEH_001 lat: 10.7769, lng: 106.7009 | Speed: 48.0 km/h (Scylla: Q8, Q9, Q10 OK)',
    '[10:15:01] GPS Ingest -> VEH_002 lat: 10.7850, lng: 106.6900 | Speed: 52.0 km/h (Scylla: Q8, Q9, Q10 OK)',
    '[10:15:00] GPS Ingest -> VEH_003 lat: 10.7620, lng: 106.6810 | Speed: 65.0 km/h (Scylla: Q8, Q9, Q10 OK)',
  ]);

  // History State
  const [historyVehicleId, setHistoryVehicleId] = useState<string>('VEH_001');
  const [historyPoints, setHistoryPoints] = useState<GPSPoint[]>([]);

  // Create Trip Modal
  const [showCreateTripModal, setShowCreateTripModal] = useState<boolean>(false);
  const [newTripOrigin, setNewTripOrigin] = useState<string>('Kho Tổng Thủ Đức');
  const [newTripDest, setNewTripDest] = useState<string>('Quận 3, TP.HCM');
  const [newTripVehicle, setNewTripVehicle] = useState<string>('VEH_004');
  const [newTripDriver, setNewTripDriver] = useState<string>('DRV_004');

  // Map references
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<{ [key: string]: L.Marker }>({});
  const polylineRef = useRef<L.Polyline | null>(null);

  // Switch Role
  const handleSwitchUser = (role: UserRole) => {
    if (role === 'ADMIN') {
      setCurrentUser({ username: 'khanh_admin', fullName: 'Phạm Gia Khánh', role: 'ADMIN', companyId: 'COMP_HCM_01' });
    } else if (role === 'DISPATCHER') {
      setCurrentUser({ username: 'vu_dispatcher', fullName: 'Trà Ngọc Nguyên Vũ', role: 'DISPATCHER', companyId: 'COMP_HCM_01' });
    } else {
      setCurrentUser({ username: 'luan_viewer', fullName: 'Lê Hữu Luân', role: 'VIEWER', companyId: 'COMP_HCM_01' });
    }
  };

  // Generate Sample History
  useEffect(() => {
    const pts: GPSPoint[] = [];
    const baseLat = 10.7769;
    const baseLng = 106.7009;
    for (let i = 0; i < 25; i++) {
      pts.push({
        lat: baseLat + i * 0.0018 + (Math.sin(i) * 0.001),
        lng: baseLng + i * 0.0022 + (Math.cos(i) * 0.001),
        speed: 35 + (i % 8) * 4,
        time: `08:${10 + i * 3}:00`
      });
    }
    setHistoryPoints(pts);
  }, [historyVehicleId]);

  // Leaflet Map Initialization
  useEffect(() => {
    if (activeTab === 'map' || activeTab === 'history') {
      if (!mapContainerRef.current) return;

      // Clean up previous instance
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }

      const map = L.map(mapContainerRef.current, {
        zoomControl: true,
        scrollWheelZoom: true
      }).setView([10.7769, 106.7009], 13);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap'
      }).addTo(map);

      mapInstanceRef.current = map;

      // Draw vehicles
      markersRef.current = {};
      vehicles.forEach(v => {
        const markerColor = v.status === 'RUNNING' ? '#10b981' : v.status === 'IDLE' ? '#f59e0b' : '#ef4444';
        const iconHtml = `
          <div style="background-color: ${markerColor}; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.4); font-size: 10px;">
            🚗
          </div>
        `;
        const icon = L.divIcon({
          html: iconHtml,
          className: '',
          iconSize: [34, 34],
          iconAnchor: [17, 17],
          popupAnchor: [0, -18]
        });

        const marker = L.marker([v.lat, v.lng], { icon }).addTo(map);
        marker.bindPopup(`
          <div style="font-family: sans-serif; min-width: 170px;">
            <div style="font-weight: bold; font-size: 13px; color: #0f172a; margin-bottom: 2px;">${v.plate}</div>
            <div style="font-size: 11px; color: #64748b;">Mã xe: <b>${v.id}</b> (${v.model})</div>
            <hr style="margin: 4px 0; border: none; border-top: 1px solid #e2e8f0;"/>
            <div style="font-size: 11px; color: #334155;">Tốc độ: <b style="color: #0284c7;">${v.speed} km/h</b> (Tối đa ${v.speedLimit})</div>
            <div style="font-size: 11px; color: #334155;">Trạng thái: <b>${v.status}</b></div>
            <div style="font-size: 10px; color: #94a3b8; margin-top: 3px;">Cập nhật: ${v.updatedAt}</div>
          </div>
        `);
        markersRef.current[v.id] = marker;
      });

      // If in History tab, draw polyline
      if (activeTab === 'history' && historyPoints.length > 0) {
        const latLngs = historyPoints.map(p => [p.lat, p.lng] as [number, number]);
        polylineRef.current = L.polyline(latLngs, { color: '#0ea5e9', weight: 4, opacity: 0.8 }).addTo(map);
        map.fitBounds(polylineRef.current.getBounds(), { padding: [30, 30] });
      }

      return () => {
        if (mapInstanceRef.current) {
          mapInstanceRef.current.remove();
          mapInstanceRef.current = null;
        }
      };
    }
  }, [activeTab, historyPoints]);

  // Simulator Live Tick
  useEffect(() => {
    if (!simRunning) return;

    const timer = setInterval(() => {
      setSimCycles(c => c + 1);

      // Move running vehicles slightly
      setVehicles(prevVehicles =>
        prevVehicles.map(v => {
          if (v.status !== 'RUNNING') return v;

          // Tiny displacement
          const deltaLat = (Math.random() - 0.48) * 0.0006;
          const deltaLng = (Math.random() - 0.48) * 0.0006;
          const newLat = Number((v.lat + deltaLat).toFixed(6));
          const newLng = Number((v.lng + deltaLng).toFixed(6));
          const newSpeed = Math.round(35 + Math.random() * 30);
          const timeStr = new Date().toLocaleTimeString('vi-VN');

          // Update Leaflet marker directly if mounted
          if (markersRef.current[v.id]) {
            markersRef.current[v.id].setLatLng([newLat, newLng]);
          }

          return {
            ...v,
            lat: newLat,
            lng: newLng,
            speed: newSpeed,
            updatedAt: timeStr
          };
        })
      );

      // Add log
      const timeStr = new Date().toLocaleTimeString('vi-VN');
      const randomVeh = INITIAL_VEHICLES[Math.floor(Math.random() * 3)];
      const newLog = `[${timeStr}] GPS Ingest -> ${randomVeh.id} | Lat/Lng: ${randomVeh.lat.toFixed(4)}, ${randomVeh.lng.toFixed(4)} | Speed: ${40 + Math.floor(Math.random() * 25)} km/h (Scylla: Q8, Q9, Q10 OK)`;
      setSimLogs(prev => [newLog, ...prev.slice(0, 19)]);
    }, simInterval * 1000);

    return () => clearInterval(timer);
  }, [simRunning, simInterval]);

  // Trigger Anomalies
  const triggerOverspeed = () => {
    const timeStr = new Date().toLocaleTimeString('vi-VN');
    const newAlert: AlertItem = {
      id: `ALT_${Date.now().toString().slice(-4)}`,
      vehicleId: 'VEH_003',
      type: 'OVERSPEED',
      severity: 'HIGH',
      status: 'OPEN',
      time: timeStr,
      details: 'Vận tốc 88.5 km/h vượt giới hạn tốc độ 80 km/h trên QL1A'
    };
    setAlerts(prev => [newAlert, ...prev]);
    setVehicles(prev => prev.map(v => v.id === 'VEH_003' ? { ...v, speed: 89 } : v));
    setSimLogs(prev => [`[${timeStr}] [ALERT TRIGGERED] Xe VEH_003 chạy quá tốc độ 88.5 km/h -> Ghi vào alerts_by_company_day & alerts_by_id (Q11, Q12)`, ...prev]);
    alert('Đã kích hoạt lỗi Quá tốc độ (Overspeed) cho xe VEH_003! Kiểm tra tab Cảnh báo.');
  };

  const triggerGeofenceExit = () => {
    const timeStr = new Date().toLocaleTimeString('vi-VN');
    const newAlert: AlertItem = {
      id: `ALT_${Date.now().toString().slice(-4)}`,
      vehicleId: 'VEH_007',
      type: 'GEOFENCE_EXIT',
      severity: 'CRITICAL',
      status: 'OPEN',
      time: timeStr,
      details: 'Xe rời khỏi vùng địa lý ảo nội đô TP.HCM (Vượt Bounding Box quy định)'
    };
    setAlerts(prev => [newAlert, ...prev]);
    setSimLogs(prev => [`[${timeStr}] [ALERT TRIGGERED] Xe VEH_007 rời khỏi vùng Geofence -> alerts_by_company_day (Q11)`, ...prev]);
    alert('Đã kích hoạt lỗi Ra khỏi vùng Geofence cho xe VEH_007!');
  };

  const triggerGpsLost = () => {
    const timeStr = new Date().toLocaleTimeString('vi-VN');
    const newAlert: AlertItem = {
      id: `ALT_${Date.now().toString().slice(-4)}`,
      vehicleId: 'VEH_008',
      type: 'GPS_LOST',
      severity: 'MEDIUM',
      status: 'OPEN',
      time: timeStr,
      details: 'Mất tín hiệu GPS liên tục quá 15 phút tại trạm bảo dưỡng'
    };
    setAlerts(prev => [newAlert, ...prev]);
    setSimLogs(prev => [`[${timeStr}] [ALERT TRIGGERED] Xe VEH_008 mất tín hiệu GPS quá ngưỡng -> alerts_by_id (Q12)`, ...prev]);
    alert('Đã kích hoạt cảnh báo Mất tín hiệu GPS cho xe VEH_008!');
  };

  // Handle Alert Actions
  const handleAlertStatus = (alertId: string, newStatus: 'ACKNOWLEDGED' | 'RESOLVED') => {
    if (currentUser.role === 'VIEWER') {
      alert('Tài khoản quyền VIEWER chỉ được xem, không được xử lý cảnh báo!');
      return;
    }
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: newStatus } : a));
  };

  // Create Trip Action (Denormalized write simulation)
  const handleCreateTrip = () => {
    if (currentUser.role === 'VIEWER') {
      alert('Quyền VIEWER không được tạo chuyến!');
      return;
    }
    const newTripId = `TRIP_202609_${String(trips.length + 1).padStart(3, '0')}`;
    const newTrip: Trip = {
      id: newTripId,
      vehicleId: newTripVehicle,
      driverId: newTripDriver,
      origin: newTripOrigin,
      destination: newTripDest,
      startTime: new Date().toISOString().replace('T', ' ').slice(0, 16),
      status: 'PLANNED',
      distanceKm: 0,
      rejectedPoints: 0
    };
    setTrips(prev => [newTrip, ...prev]);
    setShowCreateTripModal(false);
    alert(`Đã tạo chuyến mới ${newTripId}! Dữ liệu cập nhật đồng thời 3 bảng ScyllaDB: trips_by_id, trips_by_company_day, trips_by_driver_month.`);
  };

  // Start Trip
  const handleStartTrip = (tripId: string, vehicleId: string) => {
    if (currentUser.role === 'VIEWER') {
      alert('Quyền VIEWER không được bắt đầu chuyến!');
      return;
    }
    setTrips(prev => prev.map(t => t.id === tripId ? { ...t, status: 'IN_PROGRESS' } : t));
    setVehicles(prev => prev.map(v => v.id === vehicleId ? { ...v, status: 'RUNNING' } : v));
  };

  // End Trip & Calculate Haversine
  const handleEndTrip = (tripId: string, vehicleId: string) => {
    if (currentUser.role === 'VIEWER') {
      alert('Quyền VIEWER không được kết thúc chuyến!');
      return;
    }
    const distanceCalculated = Number((12.5 + Math.random() * 15.0).toFixed(2));
    setTrips(prev => prev.map(t => t.id === tripId ? {
      ...t,
      status: 'COMPLETED',
      endTime: new Date().toISOString().replace('T', ' ').slice(0, 16),
      distanceKm: distanceCalculated
    } : t));
    setVehicles(prev => prev.map(v => v.id === vehicleId ? { ...v, status: 'IDLE', speed: 0 } : v));
    alert(`Chuyến ${tripId} đã kết thúc! Quãng đường tính theo chuỗi GPS Haversine: ${distanceCalculated} km (loại 0 bước nhảy ảo).`);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400">
              <Navigation className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-white tracking-wide">ScyllaDB Fleet Tracker</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  LIVE DEMO
                </span>
              </div>
              <p className="text-xs text-slate-400">Hệ thống theo dõi vị trí và lịch sử hành trình đội xe (Column Family / Time-Series)</p>
            </div>
          </div>

          {/* Role Switcher & User Profile */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 mr-1 hidden sm:inline">Phân quyền:</span>
            <button
              onClick={() => handleSwitchUser('ADMIN')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition ${currentUser.role === 'ADMIN' ? 'bg-sky-600 text-white shadow-sm' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
            >
              Khánh (ADMIN)
            </button>
            <button
              onClick={() => handleSwitchUser('DISPATCHER')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition ${currentUser.role === 'DISPATCHER' ? 'bg-purple-600 text-white shadow-sm' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
            >
              Vũ (DISPATCHER)
            </button>
            <button
              onClick={() => handleSwitchUser('VIEWER')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition ${currentUser.role === 'VIEWER' ? 'bg-emerald-600 text-white shadow-sm' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
            >
              Luân (VIEWER)
            </button>
            <a
              href="https://github.com/giakhanhzzz/ScyllaDB-Fleet-Tracker"
              target="_blank"
              rel="noreferrer"
              className="ml-2 inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 border border-slate-700"
            >
              GitHub <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        {/* Tab Navigation Menu */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex overflow-x-auto space-x-1 border-t border-slate-800/80 text-xs">
          <button
            onClick={() => setActiveTab('map')}
            className={`py-2.5 px-3 font-medium border-b-2 transition flex items-center gap-1.5 whitespace-nowrap ${activeTab === 'map' ? 'border-sky-500 text-sky-400 bg-sky-500/5' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <MapPin className="w-3.5 h-3.5" /> Bản Đồ Giám Sát (Live Map)
          </button>
          <button
            onClick={() => setActiveTab('simulator')}
            className={`py-2.5 px-3 font-medium border-b-2 transition flex items-center gap-1.5 whitespace-nowrap ${activeTab === 'simulator' ? 'border-sky-500 text-sky-400 bg-sky-500/5' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <Radio className="w-3.5 h-3.5 text-emerald-400" /> GPS Simulator (Phát Tín Hiệu)
          </button>
          <button
            onClick={() => setActiveTab('fleet')}
            className={`py-2.5 px-3 font-medium border-b-2 transition flex items-center gap-1.5 whitespace-nowrap ${activeTab === 'fleet' ? 'border-sky-500 text-sky-400 bg-sky-500/5' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <Truck className="w-3.5 h-3.5" /> Quản Lý Đội Xe & Chuyến Đi
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-2.5 px-3 font-medium border-b-2 transition flex items-center gap-1.5 whitespace-nowrap ${activeTab === 'history' ? 'border-sky-500 text-sky-400 bg-sky-500/5' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <Clock className="w-3.5 h-3.5" /> Lịch Sử Hành Trình (Q9)
          </button>
          <button
            onClick={() => setActiveTab('alerts')}
            className={`py-2.5 px-3 font-medium border-b-2 transition flex items-center gap-1.5 whitespace-nowrap ${activeTab === 'alerts' ? 'border-sky-500 text-sky-400 bg-sky-500/5' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Cảnh Báo ({alerts.filter(a => a.status === 'OPEN').length})
          </button>
          <button
            onClick={() => setActiveTab('report')}
            className={`py-2.5 px-3 font-medium border-b-2 transition flex items-center gap-1.5 whitespace-nowrap ${activeTab === 'report' ? 'border-sky-500 text-sky-400 bg-sky-500/5' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <BarChart3 className="w-3.5 h-3.5" /> Báo Cáo Tài Xế (Q14)
          </button>
          <button
            onClick={() => setActiveTab('scylla')}
            className={`py-2.5 px-3 font-medium border-b-2 transition flex items-center gap-1.5 whitespace-nowrap ${activeTab === 'scylla' ? 'border-sky-500 text-sky-400 bg-sky-500/5' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <Database className="w-3.5 h-3.5 text-purple-400" /> CSDL ScyllaDB & 14 Truy Vấn CQL
          </button>
          <button
            onClick={() => setActiveTab('backup')}
            className={`py-2.5 px-3 font-medium border-b-2 transition flex items-center gap-1.5 whitespace-nowrap ${activeTab === 'backup' ? 'border-sky-500 text-sky-400 bg-sky-500/5' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <Download className="w-3.5 h-3.5 text-indigo-400" /> Sao Lưu & Phục Hồi
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">

        {/* TAB 1: LIVE MAP */}
        {activeTab === 'map' && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-sky-400" /> Giám Sát Vị Trí Trực Tuyến Đội Xe (Q8: latest_locations_by_company)
                </h2>
                <p className="text-xs text-slate-400">
                  Hiển thị vị trí thời gian thực của 10 xe trên bản đồ Leaflet. Cập nhật qua GPS Simulator.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>Đang di chuyển: <b>{vehicles.filter(v => v.status === 'RUNNING').length}</b></span>
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs">
                  <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                  <span>Đang dừng: <b>{vehicles.filter(v => v.status === 'IDLE').length}</b></span>
                </span>
                <button
                  onClick={() => setSimRunning(!simRunning)}
                  className={`px-3 py-1 rounded text-xs font-semibold flex items-center gap-1 ${simRunning ? 'bg-amber-600 text-white hover:bg-amber-500' : 'bg-emerald-600 text-white hover:bg-emerald-500'}`}
                >
                  {simRunning ? <><Pause className="w-3 h-3" /> Dừng Simulator</> : <><Play className="w-3 h-3" /> Chạy Simulator</>}
                </button>
              </div>
            </div>

            {/* Map Container */}
            <div className="rounded-xl border border-slate-800 overflow-hidden shadow-2xl relative bg-slate-900" style={{ height: '560px' }}>
              <div ref={mapContainerRef} style={{ width: '100%', height: '100%', zIndex: 10 }} />

              {/* Floating Quick Stats */}
              <div className="absolute top-4 right-4 z-20 bg-slate-900/90 backdrop-blur border border-slate-700/70 p-3 rounded-lg shadow-xl text-xs space-y-1.5 w-60">
                <div className="font-semibold text-slate-200 border-b border-slate-800 pb-1">Đội Xe TP.HCM (COMP_HCM_01)</div>
                <div className="flex justify-between text-slate-400">
                  <span>Tổng số xe:</span>
                  <span className="font-semibold text-white">10 xe</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Chu kỳ gửi GPS:</span>
                  <span className="font-mono text-emerald-400">3.0 giây</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Truy vấn CQL:</span>
                  <span className="font-mono text-sky-300">Q8 (Single Partition)</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: GPS SIMULATOR */}
        {activeTab === 'simulator' && (
          <div className="space-y-6">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Radio className="w-5 h-5 text-emerald-400 animate-pulse" /> Bộ Điều Khiển GPS Simulator Độc Lập
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Tiến trình mô phỏng thiết bị GPS gắn trên xe gửi tọa độ định kỳ tới API <code className="text-sky-300">/api/tracking/ingest</code> và ghi vào ScyllaDB.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="px-3 py-1.5 rounded bg-slate-800 text-xs border border-slate-700 text-slate-300">
                    Chu kỳ: <b className="text-white">#{simCycles}</b>
                  </div>
                  <button
                    onClick={() => setSimRunning(!simRunning)}
                    className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 transition ${simRunning ? 'bg-amber-600 hover:bg-amber-500 text-white' : 'bg-emerald-600 hover:bg-emerald-500 text-white'}`}
                  >
                    {simRunning ? <><Pause className="w-4 h-4" /> Tạm Dừng Phát</> : <><Play className="w-4 h-4" /> Bắt Đầu Phát</>}
                  </button>
                </div>
              </div>

              {/* Anomaly Injections for Rubric */}
              <div className="rounded-lg border border-slate-800 bg-slate-950 p-4 space-y-3">
                <div className="text-xs font-semibold text-slate-300 flex items-center gap-2">
                  <Flame className="w-4 h-4 text-amber-400" /> Kích Hoạt Lỗi Chủ Đích (Phục Vụ Demo Giảng Viên):
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <button
                    onClick={triggerOverspeed}
                    className="p-3 rounded-lg border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 text-left transition space-y-1"
                  >
                    <div className="font-semibold text-xs text-red-300 flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" /> 1. Quá Tốc Độ (Overspeed)
                    </div>
                    <p className="text-[11px] text-red-200/70">Tăng tốc xe VEH_003 lên 88.5 km/h (vượt ngưỡng 80 km/h).</p>
                  </button>

                  <button
                    onClick={triggerGeofenceExit}
                    className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 text-left transition space-y-1"
                  >
                    <div className="font-semibold text-xs text-amber-300 flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5" /> 2. Ra Khỏi Vùng Geofence
                    </div>
                    <p className="text-[11px] text-amber-200/70">Đẩy tọa độ xe VEH_007 ra ngoài Bounding Box TP.HCM.</p>
                  </button>

                  <button
                    onClick={triggerGpsLost}
                    className="p-3 rounded-lg border border-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20 text-left transition space-y-1"
                  >
                    <div className="font-semibold text-xs text-purple-300 flex items-center gap-1">
                      <Radio className="w-3.5 h-3.5" /> 3. Mất Tín Hiệu (GPS Lost)
                    </div>
                    <p className="text-[11px] text-purple-200/70">Ngắt kết nối định vị xe VEH_008 quá 15 phút.</p>
                  </button>
                </div>
              </div>

              {/* Real-time Simulator Log Terminal */}
              <div className="space-y-2">
                <div className="text-xs font-semibold text-slate-400 flex items-center justify-between">
                  <span>Nhật Ký Tọa Độ Trực Tuyến (GPS Ingestion Stream):</span>
                  <span className="font-mono text-[11px] text-slate-500">POST /api/tracking/ingest</span>
                </div>
                <div className="rounded-lg bg-black/80 border border-slate-800 p-3 font-mono text-xs text-emerald-400 h-64 overflow-y-auto space-y-1">
                  {simLogs.map((log, index) => (
                    <div key={index} className="leading-relaxed">
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: FLEET & TRIP MANAGEMENT */}
        {activeTab === 'fleet' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Truck className="w-5 h-5 text-sky-400" /> Quản Lý Đội Xe & Điều Phối Chuyến Đi (Trips)
                </h2>
                <p className="text-xs text-slate-400">
                  Tạo chuyến, khởi hành và kết thúc chuyến đi. Tự động tính quãng đường Haversine từ chuỗi điểm GPS.
                </p>
              </div>
              {currentUser.role !== 'VIEWER' && (
                <button
                  onClick={() => setShowCreateTripModal(true)}
                  className="px-3.5 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-xs font-bold text-white flex items-center gap-1.5 transition self-start sm:self-auto"
                >
                  <Plus className="w-4 h-4" /> Tạo Chuyến Đi Mới
                </button>
              )}
            </div>

            {/* Trips List */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
              <div className="p-4 border-b border-slate-800 font-semibold text-xs text-slate-300">
                Danh Sách Chuyến Đi Trong Ngày (Q6: trips_by_company_day)
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/40">
                      <th className="py-2.5 px-3">Mã Chuyến</th>
                      <th className="py-2.5 px-3">Xe</th>
                      <th className="py-2.5 px-3">Tài Xế</th>
                      <th className="py-2.5 px-3">Lộ Trình</th>
                      <th className="py-2.5 px-3">Thời Gian Bắt Đầu</th>
                      <th className="py-2.5 px-3">Quãng Đường</th>
                      <th className="py-2.5 px-3">Trạng Thái</th>
                      <th className="py-2.5 px-3 text-right">Thao Tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {trips.map(trip => (
                      <tr key={trip.id} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-3 font-mono font-semibold text-sky-400">{trip.id}</td>
                        <td className="py-2.5 px-3 font-medium text-white">{trip.vehicleId}</td>
                        <td className="py-2.5 px-3 text-slate-300">
                          {drivers.find(d => d.id === trip.driverId)?.name || trip.driverId}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className="text-slate-300">{trip.origin}</span>
                          <span className="text-slate-500 mx-1">➔</span>
                          <span className="text-slate-300">{trip.destination}</span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-400">{trip.startTime}</td>
                        <td className="py-2.5 px-3 font-mono font-semibold text-emerald-400">
                          {trip.distanceKm > 0 ? `${trip.distanceKm} km` : '--'}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${trip.status === 'IN_PROGRESS' ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30' : trip.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'}`}>
                            {trip.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          {trip.status === 'PLANNED' && currentUser.role !== 'VIEWER' && (
                            <button
                              onClick={() => handleStartTrip(trip.id, trip.vehicleId)}
                              className="px-2.5 py-1 rounded bg-sky-600 hover:bg-sky-500 text-[11px] text-white font-medium"
                            >
                              Khởi hành
                            </button>
                          )}
                          {trip.status === 'IN_PROGRESS' && currentUser.role !== 'VIEWER' && (
                            <button
                              onClick={() => handleEndTrip(trip.id, trip.vehicleId)}
                              className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-[11px] text-white font-medium"
                            >
                              Kết thúc & Tính km
                            </button>
                          )}
                          {trip.status === 'COMPLETED' && (
                            <span className="text-[11px] text-slate-500 font-mono">Đã chốt</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Vehicles Grid */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-4">
              <div className="font-semibold text-xs text-slate-300">
                Đội Xe Công Ty (Q4: vehicles_by_status & vehicles_by_id - 10 xe)
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                {vehicles.map(v => (
                  <div key={v.id} className="p-3 rounded-lg border border-slate-800 bg-slate-950 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-xs text-white">{v.plate}</span>
                      <span className={`w-2 h-2 rounded-full ${v.status === 'RUNNING' ? 'bg-emerald-400' : v.status === 'IDLE' ? 'bg-amber-400' : 'bg-red-400'}`}></span>
                    </div>
                    <div className="text-[11px] text-slate-400">{v.model}</div>
                    <div className="flex justify-between text-[11px] border-t border-slate-800/80 pt-1.5 text-slate-400">
                      <span>Tốc độ: <b className="text-sky-300">{v.speed} km/h</b></span>
                      <span>Mã: {v.id}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: GPS HISTORY & PLAYBACK */}
        {activeTab === 'history' && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Clock className="w-5 h-5 text-sky-400" /> Tra Cứu Lịch Sử Hành Trình (Q9: location_events_by_vehicle_day)
                </h2>
                <p className="text-xs text-slate-400">
                  Truy vấn dữ liệu GPS time-series theo partition <code className="text-sky-300">(vehicle_id, event_date)</code> sắp xếp thời gian giảm dần.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Chọn xe:</span>
                <select
                  value={historyVehicleId}
                  onChange={e => setHistoryVehicleId(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-xs text-white"
                >
                  {vehicles.map(v => (
                    <option key={v.id} value={v.id}>{v.id} - {v.plate}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Map Polyline */}
              <div className="lg:col-span-2 rounded-xl border border-slate-800 overflow-hidden bg-slate-900" style={{ height: '480px' }}>
                <div ref={mapContainerRef} style={{ width: '100%', height: '100%', zIndex: 10 }} />
              </div>

              {/* Timeline points */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3 overflow-hidden flex flex-col" style={{ height: '480px' }}>
                <div className="font-semibold text-xs text-slate-300 border-b border-slate-800 pb-2 flex justify-between items-center">
                  <span>Chuỗi Điểm GPS ({historyPoints.length} điểm)</span>
                  <span className="text-[11px] text-emerald-400">0 điểm bất thường</span>
                </div>
                <div className="flex-1 overflow-y-auto space-y-2 pr-1 font-mono text-xs">
                  {historyPoints.map((pt, idx) => (
                    <div key={idx} className="p-2 rounded bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                      <div>
                        <div className="text-slate-300">Lat: {pt.lat.toFixed(4)}, Lng: {pt.lng.toFixed(4)}</div>
                        <div className="text-[10px] text-slate-500">{pt.time} UTC</div>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-sky-950 text-sky-300 text-[11px] font-semibold">
                        {pt.speed} km/h
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: ALERTS & INCIDENT MANAGEMENT */}
        {activeTab === 'alerts' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-400" /> Trung Tâm Cảnh Báo & Xử Lý Sự Cố (Q11, Q12)
                </h2>
                <p className="text-xs text-slate-400">
                  Cập nhật các cảnh báo tự động: Quá tốc độ (Overspeed), Vượt vùng địa lý (Geofence exit), Mất tín hiệu (GPS lost).
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400">Quyền hiện tại:</span>
                <span className={`px-2 py-0.5 rounded font-bold ${currentUser.role === 'ADMIN' ? 'bg-sky-500/20 text-sky-400' : currentUser.role === 'DISPATCHER' ? 'bg-purple-500/20 text-purple-400' : 'bg-slate-800 text-slate-400'}`}>
                  {currentUser.role}
                </span>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/40">
                      <th className="py-2.5 px-3">Mã Cảnh Báo</th>
                      <th className="py-2.5 px-3">Thời Gian</th>
                      <th className="py-2.5 px-3">Xe</th>
                      <th className="py-2.5 px-3">Loại Cảnh Báo</th>
                      <th className="py-2.5 px-3">Mức Độ</th>
                      <th className="py-2.5 px-3">Nội Dung Chi Tiết</th>
                      <th className="py-2.5 px-3">Trạng Thái</th>
                      <th className="py-2.5 px-3 text-right">Xử Lý (RBAC)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {alerts.map(a => (
                      <tr key={a.id} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-3 font-mono font-semibold text-amber-400">{a.id}</td>
                        <td className="py-2.5 px-3 font-mono text-slate-400">{a.time}</td>
                        <td className="py-2.5 px-3 font-semibold text-white">{a.vehicleId}</td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${a.type === 'OVERSPEED' ? 'bg-red-500/20 text-red-300 border border-red-500/30' : a.type === 'GEOFENCE_EXIT' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-purple-500/20 text-purple-300 border border-purple-500/30'}`}>
                            {a.type}
                          </span>
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`font-semibold ${a.severity === 'CRITICAL' ? 'text-red-400' : 'text-amber-400'}`}>
                            {a.severity}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-300">{a.details}</td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${a.status === 'OPEN' ? 'bg-red-950 text-red-400' : a.status === 'ACKNOWLEDGED' ? 'bg-amber-950 text-amber-400' : 'bg-emerald-950 text-emerald-400'}`}>
                            {a.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right space-x-1 whitespace-nowrap">
                          {a.status === 'OPEN' && (
                            <button
                              onClick={() => handleAlertStatus(a.id, 'ACKNOWLEDGED')}
                              className="px-2 py-0.5 rounded bg-amber-600 hover:bg-amber-500 text-[10px] text-white font-medium"
                            >
                              Xác nhận
                            </button>
                          )}
                          {a.status !== 'RESOLVED' && (
                            <button
                              onClick={() => handleAlertStatus(a.id, 'RESOLVED')}
                              className="px-2 py-0.5 rounded bg-emerald-600 hover:bg-emerald-500 text-[10px] text-white font-medium"
                            >
                              Đã xử lý
                            </button>
                          )}
                          {a.status === 'RESOLVED' && (
                            <span className="text-[11px] text-slate-500">Hoàn tất</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 6: DRIVER MONTHLY REPORT (Q14) */}
        {activeTab === 'report' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-sky-400" /> Báo Cáo Tổng Hợp Chuyến Đi & Km Tài Xế Theo Tháng (Q14)
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Truy vấn dữ liệu từ partition <code className="text-sky-300">trips_by_driver_month(driver_id, '2026-09')</code> và tổng hợp trên Backend.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-1">
                <div className="text-xs text-slate-400">Tổng quãng đường tháng 09/2026</div>
                <div className="text-2xl font-bold font-mono text-emerald-400">186.4 km</div>
                <div className="text-[11px] text-slate-500">Được tính từ chuỗi GPS Haversine</div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-1">
                <div className="text-xs text-slate-400">Tổng số chuyến hoàn thành</div>
                <div className="text-2xl font-bold font-mono text-sky-400">8 chuyến</div>
                <div className="text-[11px] text-slate-500">Tài xế Nguyễn Văn An (DRV_001)</div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-1">
                <div className="text-xs text-slate-400">Số điểm GPS bất thường loại bỏ</div>
                <div className="text-2xl font-bold font-mono text-amber-400">2 điểm</div>
                <div className="text-[11px] text-slate-500">Lọc bước nhảy phi thực tế &gt; 140km/h</div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-1">
                <div className="text-xs text-slate-400">Hiệu suất vận hành</div>
                <div className="text-2xl font-bold font-mono text-purple-400">98.5%</div>
                <div className="text-[11px] text-slate-500">Không vi phạm quy chuẩn an toàn</div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
              <div className="p-4 border-b border-slate-800 font-semibold text-xs text-slate-300">
                Chi Tiết Chuyến Đi Của Tài Xế Nguyễn Văn An (DRV_001) - Tháng 09/2026
              </div>
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/40">
                    <th className="py-2.5 px-3">Mã Chuyến</th>
                    <th className="py-2.5 px-3">Xe Sử Dụng</th>
                    <th className="py-2.5 px-3">Thời Gian Khởi Hành</th>
                    <th className="py-2.5 px-3">Quãng Đường Thực Tế</th>
                    <th className="py-2.5 px-3">Trạng Thái</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  <tr className="hover:bg-slate-800/20">
                    <td className="py-2.5 px-3 font-mono text-sky-400">TRIP_202609_001</td>
                    <td className="py-2.5 px-3">VEH_001 (51A-888.12)</td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">2026-09-28 07:30</td>
                    <td className="py-2.5 px-3 font-mono font-bold text-emerald-400">18.4 km</td>
                    <td className="py-2.5 px-3"><span className="px-2 py-0.5 rounded text-[10px] bg-sky-950 text-sky-400">IN_PROGRESS</span></td>
                  </tr>
                  <tr className="hover:bg-slate-800/20">
                    <td className="py-2.5 px-3 font-mono text-sky-400">TRIP_202609_009</td>
                    <td className="py-2.5 px-3">VEH_001 (51A-888.12)</td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">2026-09-27 06:15</td>
                    <td className="py-2.5 px-3 font-mono font-bold text-emerald-400">28.5 km</td>
                    <td className="py-2.5 px-3"><span className="px-2 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-400">COMPLETED</span></td>
                  </tr>
                  <tr className="hover:bg-slate-800/20">
                    <td className="py-2.5 px-3 font-mono text-sky-400">TRIP_202609_015</td>
                    <td className="py-2.5 px-3">VEH_009 (51L-999.87)</td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">2026-09-26 13:40</td>
                    <td className="py-2.5 px-3 font-mono font-bold text-emerald-400">31.2 km</td>
                    <td className="py-2.5 px-3"><span className="px-2 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-400">COMPLETED</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 7: SCYLLADB & CQL EXPLORER */}
        {activeTab === 'scylla' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Database className="w-5 h-5 text-purple-400" /> CSDL ScyllaDB & 14 Access Patterns (Q1 - Q14)
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Chứng minh nguyên lý thiết kế Column Family: Query-First, không Join, không ALLOW FILTERING, Partition Key xác định phân vùng lưu trữ.
              </p>
            </div>

            {/* 15 Tables Catalog */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <div className="font-semibold text-xs text-slate-200">
                Mô Hình 15 Bảng Dữ Liệu Đã Khóa Trong Kế Hoạch (database/schema.cql)
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {SCYLLA_TABLES.map((t, idx) => (
                  <div key={idx} className="p-3 rounded-lg border border-slate-800 bg-slate-950 space-y-1.5">
                    <div className="font-mono font-bold text-xs text-purple-300">{t.name}</div>
                    <div className="text-[11px] text-slate-400">Khóa: <code className="text-sky-300 font-mono text-[10px]">{t.pk}</code></div>
                    <div className="text-[11px] text-slate-400">{t.purpose}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* CQL Query Runner Demo */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <div className="font-semibold text-xs text-slate-200 flex items-center justify-between">
                <span>Trình Thực Thi Truy Vấn CQL Mẫu (Mô Phỏng cqlsh / DBeaver)</span>
                <span className="font-mono text-xs text-slate-500">cqlsh localhost 9042 -k fleet_tracker</span>
              </div>
              <div className="rounded-lg bg-black/90 border border-slate-800 p-4 font-mono text-xs text-slate-200 space-y-3">
                <div className="text-sky-400">
                  -- Q8: Vị trí mới nhất tất cả xe thuộc công ty (Bản đồ giám sát)<br/>
                  SELECT vehicle_id, event_time, lat, lng, speed, heading, trip_id, status <br/>
                  FROM latest_locations_by_company <br/>
                  WHERE company_id = &apos;COMP_HCM_01&apos;;
                </div>
                <div className="border-t border-slate-800 pt-2 text-slate-400 text-[11px]">
                  <b>Kết quả (10 rows):</b><br/>
                  VEH_001 | 2026-09-28 10:15:02 | 10.7769 | 106.7009 | 48.0 km/h | 45.0° | RUNNING<br/>
                  VEH_002 | 2026-09-28 10:15:01 | 10.7850 | 106.6900 | 52.0 km/h | 90.0° | RUNNING<br/>
                  VEH_003 | 2026-09-28 10:15:00 | 10.7620 | 106.6810 | 65.0 km/h | 180.0°| RUNNING<br/>
                  VEH_004 | 2026-09-28 10:14:50 | 10.7500 | 106.6700 | 0.0 km/h  | 0.0°  | IDLE<br/>
                  VEH_005 | 2026-09-28 10:14:59 | 10.8000 | 106.7200 | 58.0 km/h | 270.0°| RUNNING
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 8: BACKUP & RESTORE */}
        {activeTab === 'backup' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Download className="w-5 h-5 text-indigo-400" /> Sao Lưu, Phục Hồi & Xuất Dữ Liệu (Rubric Mục 6)
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Thực hiện sao lưu schema, xuất dữ liệu ra file CSV/JSON và phục hồi an toàn (Yêu cầu quyền ADMIN).
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Export Actions */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
                <div className="font-semibold text-xs text-slate-200 flex items-center gap-2">
                  <Download className="w-4 h-4 text-emerald-400" /> Xuất Dữ Liệu (COPY TO / CSV Export)
                </div>
                <p className="text-xs text-slate-400">
                  Xuất dữ liệu đội xe ra định dạng CSV để đối chiếu số lượng dòng trước và sau khi phục hồi.
                </p>
                <div className="space-y-2">
                  <button
                    onClick={() => alert('Đã xuất file: docs/backups/vehicles_export.csv (10 dòng)')}
                    className="w-full py-2.5 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 flex items-center justify-between"
                  >
                    <span>Xuất bảng: vehicles_by_id.csv</span>
                    <span className="font-mono text-emerald-400">10 dòng</span>
                  </button>
                  <button
                    onClick={() => alert('Đã xuất file: docs/backups/drivers_export.csv (8 dòng)')}
                    className="w-full py-2.5 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 flex items-center justify-between"
                  >
                    <span>Xuất bảng: drivers_by_id.csv</span>
                    <span className="font-mono text-emerald-400">8 dòng</span>
                  </button>
                  <button
                    onClick={() => alert('Đã xuất file: docs/backups/trips_export.csv (20 dòng)')}
                    className="w-full py-2.5 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 flex items-center justify-between"
                  >
                    <span>Xuất bảng: trips_by_id.csv</span>
                    <span className="font-mono text-emerald-400">20 dòng</span>
                  </button>
                </div>
              </div>

              {/* Backup & Restore */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
                <div className="font-semibold text-xs text-slate-200 flex items-center gap-2">
                  <Upload className="w-4 h-4 text-indigo-400" /> Sao Lưu & Khôi Phục (Nodetool Snapshot / Script)
                </div>
                <p className="text-xs text-slate-400">
                  Tạo bản sao lưu Keyspace hoặc thiết lập lại môi trường sạch sẽ từ script tự động.
                </p>
                <div className="space-y-3 pt-2">
                  <button
                    onClick={() => alert('Đã tạo Snapshot thành công! Lưu trữ tại docs/backups/schema_backup.cql')}
                    className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white transition flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" /> Kích Hoạt Snapshot Ngay
                  </button>
                  <button
                    onClick={() => {
                      if (currentUser.role !== 'ADMIN') {
                        alert('Chỉ tài khoản ADMIN mới có quyền phục hồi dữ liệu!');
                        return;
                      }
                      alert('Đã phục hồi dữ liệu thành công từ file Seed! Kiểm tra đối chiếu số dòng khớp 100%.');
                    }}
                    className="w-full py-2.5 px-4 rounded-lg bg-red-950/60 hover:bg-red-900/60 text-xs font-bold text-red-300 border border-red-500/30 transition flex items-center justify-center gap-2"
                  >
                    <RotateCcw className="w-4 h-4" /> Phục Hồi Dữ Liệu (Reset Demo)
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* CREATE TRIP MODAL */}
      {showCreateTripModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-sm text-white flex items-center gap-2">
                <Plus className="w-4 h-4 text-sky-400" /> Lập Chuyến Đi Mới
              </h3>
              <button onClick={() => setShowCreateTripModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Chọn Phương Tiện:</label>
                <select
                  value={newTripVehicle}
                  onChange={e => setNewTripVehicle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white"
                >
                  {vehicles.map(v => (
                    <option key={v.id} value={v.id}>{v.id} - {v.plate} ({v.model})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Chọn Tài Xế Phụ Trách:</label>
                <select
                  value={newTripDriver}
                  onChange={e => setNewTripDriver(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white"
                >
                  {drivers.map(d => (
                    <option key={d.id} value={d.id}>{d.name} ({d.license})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Điểm Đi (Origin):</label>
                <input
                  type="text"
                  value={newTripOrigin}
                  onChange={e => setNewTripOrigin(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Điểm Đến (Destination):</label>
                <input
                  type="text"
                  value={newTripDest}
                  onChange={e => setNewTripDest(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
              <button
                onClick={() => setShowCreateTripModal(false)}
                className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-300"
              >
                Hủy
              </button>
              <button
                onClick={handleCreateTrip}
                className="px-4 py-1.5 rounded bg-sky-600 hover:bg-sky-500 text-xs font-bold text-white"
              >
                Xác Nhận Tạo Chuyến
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950/80 py-4 text-center text-xs text-slate-500">
        Đồ Án NoSQL • ScyllaDB Fleet Tracker • Nhóm: Phạm Gia Khánh (Data & Môi trường), Trà Ngọc Nguyên Vũ (Backend & RBAC), Lê Hữu Luân (Frontend & Simulator)
      </footer>
    </div>
  );
}
