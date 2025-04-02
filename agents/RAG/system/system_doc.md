# 📘 Reference Guide - System Errors & Recommendations

This document helps intelligent agents identify and resolve common system-level errors. It is tailored to support Retrieval-Augmented Generation (RAG) systems and automated diagnostics.

---

## 💾 Disk Full

**Log example**:

```
[2024-12-22 06:00:45] ERROR - No space left on device: /var/log
```

**Likely cause**:

- Log files consuming disk space  
- Large or uncleaned temporary files  
- Backup files not rotated

**Recommendations**:

- Clear old logs (`logrotate`, `journalctl --vacuum-time`)  
- Remove unnecessary files from `/tmp`, `/var/cache`, etc.  
- Increase disk size or mount additional storage

---

## 🔋 Out of Memory (OOM)

**Log example**:

```
[2024-12-23 15:30:10] ERROR - Out of memory: Kill process 1234 (myapp)
```

**Likely cause**:

- Application using excessive memory  
- Memory leak or unoptimized code

**Recommendations**:

- Monitor memory usage with `htop` or `free`  
- Limit memory per process using cgroups  
- Enable swap space as fallback  
- Optimize app memory usage

---

## 🔒 Permission Denied

**Log example**:

```
[2024-12-24 08:45:01] ERROR - Permission denied: cannot access /etc/secure_file
```

**Likely cause**:

- Process does not have required permissions  
- File owned by another user/group

**Recommendations**:

- Check file ownership and permissions (`ls -l`)  
- Use `chmod` and `chown` to adjust access rights  
- Run services with proper user roles

---

## 🔁 Service Not Starting

**Log example**:

```
[2024-12-25 11:12:30] ERROR - systemd: Failed to start myapp.service
```

**Likely cause**:

- Misconfigured service file  
- Missing dependencies or incorrect exec path

**Recommendations**:

- Inspect logs with `journalctl -xe`  
- Verify service definition under `/etc/systemd/system`  
- Check `ExecStart` path and environment variables

---

## 🌐 Network Unreachable

**Log example**:

```
[2024-12-26 13:00:00] ERROR - Network is unreachable when contacting 10.0.0.5
```

**Likely cause**:

- Network misconfiguration  
- Down interface or unreachable gateway

**Recommendations**:

- Use `ping`, `ip a`, and `ip route` for diagnostics  
- Restart network service (`systemctl restart NetworkManager`)  
- Check DNS and gateway settings

---

## 🔌 Hardware Failures

**Log example**:

```
[2024-12-27 02:22:14] WARNING - SMART error: read failure on /dev/sda
```

**Likely cause**:

- Failing hard disk or memory  
- Overheating or aging hardware

**Recommendations**:

- Use tools like `smartctl`, `memtest`, or `dmesg`  
- Replace failing components proactively  
- Monitor with hardware alerting tools (e.g., `lm-sensors`)

---


