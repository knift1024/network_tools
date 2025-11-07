import subprocess
import platform
import re

def get_network_info():
    """Retrieves basic network information (IP, Gateway, DNS) for the primary adapter."""
    info = {
        "ip_address": "N/A",
        "subnet_mask": "N/A",
        "default_gateway": "N/A",
        "dns_servers": [],
        "adapter_name": "N/A",
        "connection_type": "N/A", # Wired/Wireless
        "status": "Disconnected"
    }

    if platform.system() == "Windows":
        try:
            # Get IP config details
            result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, encoding='cp950', check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            output = result.stdout

            # Store all adapter info first
            all_adapters_info = []
            current_adapter_info = None

            # Regex patterns to extract information
            adapter_header_pattern = re.compile(r"^(乙太網路卡|無線區域網路介面卡|不明的介面卡) (.+?):$", re.MULTILINE)
            ip_pattern = re.compile(r"IPv4 位址[ .]+: (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
            subnet_pattern = re.compile(r"子網路遮罩[ .]+: (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
            # Simplified gateway pattern to just find an IPv4 address on a line that might be a gateway
            ipv4_pattern = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
            dns_line_pattern = re.compile(r"DNS 伺服器[ .]+: (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
            media_state_pattern = re.compile(r"媒體狀態[ .]+: (.+)")
            description_pattern = re.compile(r"描述[ .]+: (.+)")

            lines = output.splitlines()
            expecting_ipv4_gateway = False
            expecting_additional_dns = False # New flag for DNS
            for i, line in enumerate(lines):
                adapter_match = adapter_header_pattern.match(line)
                if adapter_match:
                    if current_adapter_info:
                        all_adapters_info.append(current_adapter_info)
                    
                    current_adapter_info = {
                        "adapter_name": f"{adapter_match.group(1)} {adapter_match.group(2)}",
                        "ip_address": "N/A",
                        "subnet_mask": "N/A",
                        "default_gateway": "N/A",
                        "dns_servers": [],
                        "connection_type": "無線" if "無線區域網路" in adapter_match.group(1) else "有線",
                        "status": "N/A"
                    }
                    expecting_ipv4_gateway = False # Reset for new adapter
                    expecting_additional_dns = False # Reset for new adapter
                    continue

                if current_adapter_info:
                    # Gateway parsing logic
                    if "預設閘道" in line:
                        gateway_match = ipv4_pattern.search(line)
                        if gateway_match and not gateway_match.group(1).startswith("fe80::"):
                            current_adapter_info["default_gateway"] = gateway_match.group(1)
                        else:
                            expecting_ipv4_gateway = True
                    elif expecting_ipv4_gateway:
                        gateway_match = ipv4_pattern.search(line)
                        if gateway_match:
                            current_adapter_info["default_gateway"] = gateway_match.group(1)
                        expecting_ipv4_gateway = False

                    # DNS parsing logic
                    dns_match = dns_line_pattern.search(line)
                    if dns_match:
                        current_adapter_info["dns_servers"].append(dns_match.group(1))
                        expecting_additional_dns = True # Expect more DNS on next lines
                    elif expecting_additional_dns:
                        ipv4_match = ipv4_pattern.search(line)
                        if ipv4_match:
                            current_adapter_info["dns_servers"].append(ipv4_match.group(1))
                        else:
                            expecting_additional_dns = False # Stop expecting if line doesn't contain IP

                    ip_match = ip_pattern.search(line)
                    if ip_match: current_adapter_info["ip_address"] = ip_match.group(1)
                    subnet_match = subnet_pattern.search(line)
                    if subnet_match: current_adapter_info["subnet_mask"] = subnet_match.group(1)
                    media_state_match = media_state_pattern.search(line)
                    if media_state_match: current_adapter_info["status"] = media_state_match.group(1).strip()
            
            if current_adapter_info:
                all_adapters_info.append(current_adapter_info)

            # Prioritize connected adapters with an IPv4 address
            for adapter in all_adapters_info:
                # An adapter is considered active if it has an IPv4 address and is not explicitly marked as 'Media disconnected'
                is_connected = adapter["ip_address"] != "N/A" and adapter["status"] != "媒體已中斷連線"
                if is_connected:
                    info.update(adapter)
                    info["status"] = "已連線"
                    break

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error getting network info: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during network info parsing: {e}")
    else:
        # Placeholder for Linux/macOS (using ifconfig/ip addr)
        info["adapter_name"] = "非 Windows 系統"
        info["status"] = "未支援"

    return info

def ping_host(host, count=4, timeout=1000):
    """Pings a host and returns success status and latency."""
    result = {"success": False, "latency": "N/A", "error": ""}
    param = "-n" if platform.system() == "Windows" else "-c"
    timeout_param = "-w" if platform.system() == "Windows" else "-W"
    
    # Convert timeout to seconds for non-Windows systems if it's in ms
    actual_timeout = str(timeout) if platform.system() == "Windows" else str(int(timeout / 1000))

    try:
        command = ["ping", param, str(count), timeout_param, actual_timeout, host]
        process = subprocess.run(command, capture_output=True, text=True, encoding='cp950', check=False, creationflags=subprocess.CREATE_NO_WINDOW) # check=False to handle non-zero exit codes gracefully
        output = process.stdout
        stderr = process.stderr

        # Determine success based on output content, not just returncode
        if platform.system() == "Windows":
            if "回覆自" in output or "Reply from" in output:
                if "目的地主機無法連線" in output or "Destination host unreachable" in output:
                    result["error"] = "目的地主機無法連線 (來自本機的回覆)"
                elif "要求等候逾時" in output or "Request timed out" in output:
                    result["error"] = "要求等候逾時"
                elif "已遺失 = 0 (0% 遺失)" in output:
                    result["success"] = True
                    latency_match = re.search(r"平均 = (\d+)ms", output)
                    if latency_match:
                        result["latency"] = f"{latency_match.group(1)}ms"
                    else:
                        single_latency_match = re.search(r"時間=(\d+)ms", output)
                        if single_latency_match:
                            result["latency"] = f"{single_latency_match.group(1)}ms"
                elif "已遺失 = 4 (100% 遺失)" in output: # Assuming count=4
                    result["error"] = "100% 封包遺失 (目標主機無回應)"
                else:
                    # Some packets received, but not 0% loss, or other partial success
                    # If '回覆自' is present and no explicit failure, consider it success for now
                    result["success"] = True 
                    latency_match = re.search(r"平均 = (\d+)ms", output)
                    if latency_match:
                        result["latency"] = f"{latency_match.group(1)}ms"
                    else:
                        single_latency_match = re.search(r"時間=(\d+)ms", output)
                        if single_latency_match:
                            result["latency"] = f"{single_latency_match.group(1)}ms"
            elif "要求等候逾時" in output or "Request timed out" in output:
                result["error"] = "要求等候逾時"
            elif "無法找到主機" in output or "could not find host" in output:
                result["error"] = "無法找到主機"
            elif "一般失敗" in output or "General failure" in output:
                result["error"] = "一般失敗 (可能網路不通)"
            elif "Destination host unreachable" in output or "目的主機無法連線" in output:
                result["error"] = "目的主機無法連線"
            else:
                # Fallback for other non-success cases
                result["error"] = f"Ping 失敗或未知錯誤. Stdout: {output.strip()} Stderr: {stderr.strip()}"
        else:
            # Linux/macOS output parsing
            if "bytes from" in output:
                result["success"] = True
                latency_match = re.search(r"min/avg/max/mdev = [\d.]+/([\d.]+)/", output)
                if latency_match:
                    result["latency"] = f"{latency_match.group(1)}ms"
            else:
                result["error"] = f"Ping 失敗或未知錯誤. Stdout: {output.strip()} Stderr: {stderr.strip()}"

    except FileNotFoundError:
        result["error"] = "Ping 命令未找到，請確認系統環境變數設定。"
    except Exception as e:
        result["error"] = f"發生未知錯誤: {e}"

    return result



def tracert_host(host, max_hops=30):
    """Performs a traceroute to a host and returns the hops."""
    hops = []
    # Force IPv4 on Windows with -4 flag
    command_name = "tracert" if platform.system() == "Windows" else "traceroute"
    param_flags = ["-d"] if platform.system() == "Windows" else ["-n"]
    max_hops_param = "-h" if platform.system() == "Windows" else "-m"

    try:
        command = [command_name, *param_flags, max_hops_param, str(max_hops), host]
        if platform.system() == "Windows":
            command.insert(1, "-4") # Insert -4 flag for IPv4 tracert on Windows

        process = subprocess.run(command, capture_output=True, text=True, encoding='cp950', check=False, creationflags=subprocess.CREATE_NO_WINDOW) # check=False to handle non-zero exit codes gracefully
        output = process.stdout
        stderr = process.stderr

        if process.returncode != 0:
            hops.append({"num": "Error", "ip": f"Tracert 命令執行失敗 (Exit Code: {process.returncode}). Stderr: {stderr.strip()}", "latency": "N/A"})
            return hops

        if platform.system() == "Windows":
            # Windows tracert output parsing for IPv4
            for line in output.splitlines():
                if "Tracing route to" in line or "追蹤" in line:
                    continue
                if "over a maximum of" in line or "在最多" in line:
                    continue
                
                # Match lines with hop number, multiple latencies, and an IP address
                match = re.search(r"^\s*(\d+)\s+([<\d.]+\s*ms|\*)\s+([<\d.]+\s*ms|\*)\s+([<\d.]+\s*ms|\*)\s+([\d.]+)", line)
                if match:
                    hop_num = int(match.group(1))
                    ip = match.group(5)
                    latency_values = [m for m in match.groups()[1:4] if m != '*']
                    latency = latency_values[0] if latency_values else "N/A"
                    hops.append({"num": hop_num, "ip": ip, "latency": latency})
                elif re.match(r"^\s*(\d+)\s+\*", line): # Handle lines with all asterisks
                    hop_num = int(re.match(r"^\s*(\d+)", line).group(1))
                    hops.append({"num": hop_num, "ip": "要求等候逾時", "latency": "N/A"})
        else:
            # Linux/macOS traceroute output parsing
            for line in output.splitlines():
                match = re.match(r"^\s*(\d+)\s+([\w.-]+)\s+\((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\)\s+([\d.]+)\s*ms", line)
                if match:
                    hop_num = int(match.group(1))
                    ip = match.group(3)
                    latency = f"{match.group(4)}ms"
                    hops.append({"num": hop_num, "ip": ip, "latency": latency})
                elif re.match(r"^\s*(\d+)\s+\*", line):
                    hops.append({"num": len(hops) + 1, "ip": "Request timed out", "latency": "N/A"})

    except FileNotFoundError:
        hops.append({"num": "Error", "ip": "Tracert 命令未找到，請確認系統環境變數設定。", "latency": "N/A"})
    except Exception as e:
        hops.append({"num": "Error", "ip": f"發生未知錯誤: {e}", "latency": "N/A"})

    return hops

# Example usage (for testing purposes)
if __name__ == "__main__":
    print("\n--- Network Info ---")
    net_info = get_network_info()
    for k, v in net_info.items():
        print(f"{k}: {v}")

    print("\n--- Ping Google.com ---")
    ping_result = ping_host("www.google.com", count=4, timeout=1000)
    print(ping_result)

    print("\n--- Ping 8.8.8.8 ---")
    ping_result_ip = ping_host("8.8.8.8", count=4, timeout=1000)
    print(ping_result_ip)

    print("\n--- Tracert Google.com ---")
    tracert_result = tracert_host("www.google.com", max_hops=10)
    for hop in tracert_result:
        print(hop)
