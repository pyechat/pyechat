"""System information utility for PyeChat.
Provides a get_sysinfo() function that returns a formatted single-line string describing
client, OS, CPU, memory, storage and uptime.
"""
import platform
import shutil
import time
import os

try:
    import psutil
    _HAS_PSUTIL = True
except Exception:
    _HAS_PSUTIL = False

from datetime import timedelta

CLIENT_NAME = "PyeChat"
CLIENT_VERSION = "0.1.0"

def _read_os_release():
    info = {}
    try:
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if '=' in line:
                    k, v = line.rstrip().split('=', 1)
                    info[k] = v.strip('"')
    except Exception:
        pass
    return info

def _format_bytes(bytes_val):
    for unit in ['B','KB','MB','GB','TB']:
        if abs(bytes_val) < 1024.0:
            return f"{bytes_val:3.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"

def _uptime_text():
    try:
        if _HAS_PSUTIL:
            secs = int(time.time() - psutil.boot_time())
        else:
            with open('/proc/uptime', 'r') as f:
                secs = int(float(f.readline().split()[0]))
        delta = timedelta(seconds=secs)
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        s = []
        if days: s.append(f"{days}d")
        if hours: s.append(f"{hours}h")
        if minutes: s.append(f"{minutes}m")
        s.append(f"{seconds}s")
        return ' '.join(s)
    except Exception:
        return "unknown"


def get_sysinfo():
    # Client
    client = f"{CLIENT_NAME} {CLIENT_VERSION}"

    # OS
    os_text = platform.system()
    try:
        if os_text == 'Linux':
            r = _read_os_release()
            pretty = r.get('PRETTY_NAME') or f"{r.get('NAME', 'Linux')} {r.get('VERSION', '')}".strip()
            os_text = pretty
        else:
            os_text = f"{os_text} {platform.release()}"
    except Exception:
        pass

    # CPU
    cpu_text = 'Unknown CPU'
    try:
        if _HAS_PSUTIL:
            cpu_info = platform.processor() or ''
            if not cpu_info:
                cpu_info = ' '.join(platform.uname())
            freq = psutil.cpu_freq()
            freq_s = f"{freq.max/1000:.2f}GHz" if freq and freq.max else ''
            cpu_text = f"{platform.machine()} {freq_s}".strip()
        else:
            cpu_text = platform.processor() or platform.machine()
    except Exception:
        pass

    # Memory
    mem_text = 'unknown'
    try:
        if _HAS_PSUTIL:
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()
            mem_text = f"Physical: {vm.total/1024**3:.1f} GiB Total ({vm.available/1024**3:.1f} GiB Free) Swap: {swap.total/1024**3:.1f} GiB Total ({swap.free/1024**3:.1f} GiB Free)"
        else:
            # Parse /proc/meminfo
            meminfo = {}
            with open('/proc/meminfo') as f:
                for line in f:
                    k, v = line.split(':')
                    meminfo[k.strip()] = v.strip()
            total_k = float(meminfo.get('MemTotal','0 kB').split()[0])
            free_k = float(meminfo.get('MemAvailable',meminfo.get('MemFree','0 kB')).split()[0])
            swap_k = float(meminfo.get('SwapTotal','0 kB').split()[0])
            swap_free_k = float(meminfo.get('SwapFree','0 kB').split()[0])
            mem_text = f"Physical: {total_k/1024**1:.1f} MiB Total ({free_k/1024**1:.1f} MiB Free) Swap: {swap_k/1024**1:.1f} MiB Total ({swap_free_k/1024**1:.1f} MiB Free)"
    except Exception:
        pass

    # Storage
    storage_text = 'unknown'
    try:
        st = shutil.disk_usage('/')
        total = st.total
        used = st.used
        free = st.free
        storage_text = f"{used/1024**3:.1f} GB / {total/1024**3:.1f} GB ({free/1024**3:.1f} GB Free)"
    except Exception:
        pass

    # Uptime
    uptime = _uptime_text()

    # Assemble
    parts = [f"Client: {client}", f"OS: {os_text}", f"CPU: {cpu_text}", f"Memory: {mem_text}", f"Storage: {storage_text}", f"Uptime: {uptime}"]
    return ' • '.join(parts)
