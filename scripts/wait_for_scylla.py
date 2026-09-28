#!/usr/bin/env python3
"""
ScyllaDB Fleet Tracker - Wait & Verification Script for ScyllaDB Node (Phase 1)
Author: Nhom Do An NoSQL (Khanh, Vu, Luan)

Chuc nang:
- Kiem tra ket noi den ScyllaDB node (mac dinh localhost:9042)
- Su dung driver chinh thuc: cassandra-driver
- Thu lai (retry) theo chu ky trong khi container khoi dong
- Doc thong tin cluster tu bang system.local de xac nhan node hoat dong hoan toan
"""

import os
import sys
import time
import socket

def check_socket_ready(host: str, port: int, timeout_sec: float = 2.0) -> bool:
    """Kiem tra xem port TCP 9042 da mo va chap nhan ket noi hay chua."""
    try:
        with socket.create_connection((host, port), timeout=timeout_sec):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def verify_scylla_connection(host: str = "localhost", port: int = 9042, max_retries: int = 30, retry_delay: int = 2):
    print("=" * 65)
    print(" [P1 CHECK] KIEM TRA KET NOI SCYLLADB BANG CASSANDRA-DRIVER")
    print(f" Target Host: {host} | Port: {port}")
    print("=" * 65)

    # 1. Kiem tra import driver
    try:
        import cassandra
        from cassandra.cluster import Cluster, NoHostAvailable
        from cassandra.policies import DCAwareRoundRobinPolicy
        print(f"[OK] Da import cassandra-driver thanh cong (phien ban: {cassandra.__version__})")
    except ImportError as e:
        print("[FAIL] Khong the import 'cassandra-driver'.")
        print(f" Chi tiet loi: {e}")
        print(" Huong dan khac phuc:")
        print("   pip install cassandra-driver")
        print("   (Hoac kiem tra moi truong Laragon Python 3.13 da co san driver)")
        return False

    # 2. Vong lap cho port TCP mo va Scylla native transport san sang
    print(f"\n[INFO] Dang doi port {host}:{port} san sang...")
    tcp_ready = False
    for attempt in range(1, max_retries + 1):
        if check_socket_ready(host, port):
            tcp_ready = True
            print(f"[OK] Port TCP {host}:{port} da mo (Lan thu {attempt}/{max_retries})")
            break
        print(f" ... Dang cho Scylla khoi dong ({attempt}/{max_retries})...")
        time.sleep(retry_delay)

    if not tcp_ready:
        print(f"\n[FAIL] Khong the ket noi toi port TCP {host}:{port} sau {max_retries * retry_delay}s.")
        print(" Nguyen nhan thuong gap:")
        print("   1. Docker Desktop Engine chua bat hoac dang bi dung (Stopped).")
        print("   2. Container 'scylla-node' chua duoc khoi dong ('docker compose up -d').")
        print("   3. Port 9042 bi firewall chan hoac bi chiem boi service khac.")
        return False

    # 3. Ket noi CQL Protocol qua cassandra-driver
    print(f"\n[INFO] Dang thiet lap CQL Session toi ScyllaDB qua cassandra-driver...")
    cluster = None
    session = None
    cql_connected = False

    for attempt in range(1, 15):
        try:
            cluster = Cluster(
                contact_points=[host],
                port=port,
                connect_timeout=10,
                control_connection_timeout=10
            )
            session = cluster.connect()
            cql_connected = True
            print(f"[OK] Ket noi CQL Native Protocol thanh cong o lan thu {attempt}!")
            break
        except NoHostAvailable as e:
            print(f" ... Scylla dang khoi tao CQL transport (Lan thu {attempt}/15)...")
            time.sleep(3)
        except Exception as e:
            print(f" ... Dang thu lai vi loi: {e}")
            time.sleep(3)

    if not cql_connected or session is None:
        print("\n[FAIL] Khong the mo CQL Session den ScyllaDB.")
        return False

    # 4. Truy van metadata tu system.local
    try:
        print("\n[INFO] Dang truy van thong tin node tu system.local...")
        row = session.execute("SELECT cluster_name, release_version, data_center, rack FROM system.local").one()
        if row:
            print("-" * 65)
            print(f"  Cluster Name    : {row.cluster_name}")
            print(f"  Release Version : {row.release_version}")
            print(f"  Datacenter      : {getattr(row, 'data_center', 'default')}")
            print(f"  Rack            : {getattr(row, 'rack', 'default')}")
            print("-" * 65)

        # Truy van danh sach keyspace he thong
        rows_ks = session.execute("SELECT keyspace_name FROM system_schema.keyspaces")
        ks_names = [r.keyspace_name for r in rows_ks]
        print(f"  System Keyspaces: {', '.join(ks_names)}")
        print("-" * 65)
        print("[SUCCESS] Phase 1 - ScyllaDB Node va Driver da san sang 100%!")
        return True

    except Exception as e:
        print(f"[FAIL] Loi khi truy van system metadata: {e}")
        return False
    finally:
        if cluster:
            cluster.shutdown()

if __name__ == "__main__":
    target_host = os.getenv("SCYLLA_HOST", "localhost")
    target_port = int(os.getenv("SCYLLA_PORT", "9042"))

    success = verify_scylla_connection(host=target_host, port=target_port)
    sys.exit(0 if success else 1)
