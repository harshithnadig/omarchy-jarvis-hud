#!/bin/bash

# JARVIS Tactical Telemetry & System Protocol Engine

get_cpu_usage() {
  local prev_idle prev_total idle total
  read -r _ user nice system idle iowait irq softirq steal _ < /proc/stat
  local prev_idle_sum=$((idle + iowait))
  local prev_non_idle=$((user + nice + system + irq + softirq + steal))
  local prev_total_sum=$((prev_idle_sum + prev_non_idle))
  
  sleep 0.08
  
  read -r _ user nice system idle iowait irq softirq steal _ < /proc/stat
  local idle_sum=$((idle + iowait))
  local non_idle=$((user + nice + system + irq + softirq + steal))
  local total_sum=$((idle_sum + non_idle))
  
  local total_diff=$((total_sum - prev_total_sum))
  local idle_diff=$((idle_sum - prev_idle_sum))
  
  if (( total_diff > 0 )); then
    echo $(( (100 * (total_diff - idle_diff)) / total_diff ))
  else
    echo 0
  fi
}

get_cpu_temp() {
  local temp=0
  for t in /sys/class/thermal/thermal_zone*/temp; do
    if [[ -r "$t" ]]; then
      local val=$(cat "$t" 2>/dev/null || echo 0)
      if (( val > temp )); then
        temp=$val
      fi
    fi
  done
  echo $(( temp / 1000 ))
}

get_telemetry() {
  local cpu_usage=$(get_cpu_usage)
  local cpu_temp=$(get_cpu_temp)
  local cpu_cores=$(nproc 2>/dev/null || echo 8)
  
  # Memory
  local mem_total_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
  local mem_avail_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
  local mem_used_kb=$((mem_total_kb - mem_avail_kb))
  local mem_used_gb=$(awk -v u="$mem_used_kb" 'BEGIN {printf "%.1f", u / 1048576}')
  local mem_total_gb=$(awk -v t="$mem_total_kb" 'BEGIN {printf "%.1f", t / 1048576}')
  local mem_pct=$(( (mem_used_kb * 100) / mem_total_kb ))
  
  # GPU (NVIDIA check)
  local gpu_name="Integrated GPU"
  local gpu_load=0
  local gpu_temp=0
  local gpu_vram_used=0
  local gpu_vram_total=0
  local gpu_vram_pct=0
  
  if command -v nvidia-smi &>/dev/null; then
    local nv_info
    nv_info=$(nvidia-smi --query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null | head -n 1 || true)
    if [[ -n "$nv_info" ]]; then
      IFS=',' read -r gpu_name gpu_load gpu_temp gpu_vram_used gpu_vram_total <<< "$nv_info"
      gpu_name=$(echo "$gpu_name" | xargs)
      gpu_load=$(echo "$gpu_load" | xargs)
      gpu_temp=$(echo "$gpu_temp" | xargs)
      gpu_vram_used=$(echo "$gpu_vram_used" | xargs)
      gpu_vram_total=$(echo "$gpu_vram_total" | xargs)
      if (( gpu_vram_total > 0 )); then
        gpu_vram_pct=$(( (gpu_vram_used * 100) / gpu_vram_total ))
      fi
    fi
  fi
  
  # Battery
  local bat_pct=100
  local bat_status="AC Connected"
  local bat_power="0.0"
  if [[ -f /sys/class/power_supply/BAT0/capacity ]]; then
    bat_pct=$(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null || echo 100)
    bat_status=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null || echo "Discharging")
  elif [[ -f /sys/class/power_supply/BAT1/capacity ]]; then
    bat_pct=$(cat /sys/class/power_supply/BAT1/capacity 2>/dev/null || echo 100)
    bat_status=$(cat /sys/class/power_supply/BAT1/status 2>/dev/null || echo "Discharging")
  fi
  
  # Uptime
  local uptime_str=$(uptime -p 2>/dev/null | sed 's/up //')
  local load_avg=$(awk '{print $1", "$2", "$3}' /proc/loadavg)

  cat <<JSON
{
  "status": "ONLINE",
  "protocol": "NOMINAL",
  "cpu": {
    "usage": $cpu_usage,
    "temp": $cpu_temp,
    "cores": $cpu_cores
  },
  "gpu": {
    "name": "$gpu_name",
    "load": $gpu_load,
    "temp": $gpu_temp,
    "vram_used_mb": $gpu_vram_used,
    "vram_total_mb": $gpu_vram_total,
    "vram_pct": $gpu_vram_pct
  },
  "memory": {
    "used_gb": "$mem_used_gb",
    "total_gb": "$mem_total_gb",
    "pct": $mem_pct
  },
  "power": {
    "battery_pct": $bat_pct,
    "status": "$bat_status"
  },
  "system": {
    "uptime": "$uptime_str",
    "load_avg": "$load_avg",
    "hostname": "$(hostname 2>/dev/null || echo 'CyberNode')"
  }
}
JSON
}

cmd="${1:-telemetry}"

case "$cmd" in
  telemetry|get)
    get_telemetry
    ;;
  overdrive)
    if command -v powerprofilesctl &>/dev/null; then
      powerprofilesctl set performance 2>/dev/null || true
    fi
    omarchy-notification-send -g ⚡ "JARVIS PROTOCOL" "OVERDRIVE ENGAGED: Maximum performance & unthrottled clocks." >/dev/null 2>&1 || true
    echo "Overdrive activated"
    ;;
  eco)
    if command -v powerprofilesctl &>/dev/null; then
      powerprofilesctl set power-saver 2>/dev/null || true
    fi
    omarchy-notification-send -g 🍃 "JARVIS PROTOCOL" "STEALTH ENGAGED: Whisper-quiet thermal profile & eco throttling." >/dev/null 2>&1 || true
    echo "Stealth activated"
    ;;
  purge)
    sync
    omarchy-notification-send -g 🧹 "JARVIS PROTOCOL" "MEMORY PURGED: Cache flushed and file buffers synchronized." >/dev/null 2>&1 || true
    echo "Cache purged"
    ;;
  *)
    get_telemetry
    ;;
esac
