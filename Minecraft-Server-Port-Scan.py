import socket
import psutil
from colorama import init, Fore, Style
import pyfiglet
import time
from mcstatus import JavaServer
import threading
import speedtest
import requests
import os

# Initialize colorama
init()

# Global list to keep track of open ports
open_ports_global = []
delay_between_threads = 0.1

# Function to check if a port is open
def check_port(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            sock.connect((ip, port))
            return True
    except (socket.timeout, socket.error):
        return False

# Function to check the status of a Minecraft server
def check_minecraft_server_status(ip, port):
    try:
        server = JavaServer.lookup(f"{ip}:{port}")
        status = server.status()
        print(Fore.GREEN + f"The Minecraft server at {ip}:{port} is online. Players: {status.players.online}" + Style.RESET_ALL)
        return True
    except Exception as e:
        print(Fore.RED + f"The Minecraft server at {ip}:{port} is offline or not responding. Error: {e}" + Style.RESET_ALL)
        return False

# Function that performs port scanning using threading
def threaded_port_scan(ip, port, open_ports_local):
    if check_minecraft_server_status(ip, port):
        open_ports_local.add(port) 

# Function to estimate scan duration
def estimate_scan_duration(start_port, end_port):
    total_ports = end_port - start_port + 1
    estimated_time = total_ports * delay_between_threads
    minutes, seconds = divmod(estimated_time, 60)
    return int(minutes), int(seconds)

# Function that manages threading and performs ping test every 500 ports
def manage_threads(ip, start_port, end_port, open_ports, delay_between_threads=0.1):
    threads = []
    port_count = 0  
    for port in range(start_port, end_port + 1):
        thread = threading.Thread(target=threaded_port_scan, args=(ip, port, open_ports))
        threads.append(thread)
        thread.start()
        port_count += 1
        if port_count % 100 - 1 == 0 :   # Every 100 ports, perform a ping test
            time.sleep(0.2)  # Sleep for 3 seconds after the ping test
        time.sleep(delay_between_threads)

    # We wait until all threads have finished their work
    for thread in threads:
        thread.join()

# Function to display text slowly
def display_slowly(text, delay=0.001):  # Increased delay for better readability
    for character in text:
        print(character, end='', flush=True)
        time.sleep(delay)
    print()

# Function to print open ports in a table and count both open and closed ports
def print_ports_table(open_ports, start_port, end_port):
    open_ports_count = 0
    closed_ports_count = 0
    display_slowly(Fore.CYAN + "\nTarget Ip: " + Fore.GREEN + target_ip, 0.01)
    display_slowly(Fore.CYAN + "Ports Status:" + Style.RESET_ALL, 0.01)
    display_slowly(Fore.GREEN + "PORT\tSTATUS" + Style.RESET_ALL, 0.01)
    for port in range(start_port, end_port + 1):
        if port in open_ports:
            display_slowly  (Fore.GREEN + f"{port}\tOpen" + Style.RESET_ALL, 0.01)
            open_ports_count += 1
        else:
            closed_ports_count += 1
    display_slowly(Fore.CYAN + f"\nOpen Ports Count: {Fore.GREEN}{open_ports_count}" + Style.RESET_ALL, 0.01)
    display_slowly(Fore.CYAN + f"Closed Ports Count: {Fore.RED}{closed_ports_count}" + Style.RESET_ALL, 0.01)

# Function to get server status
def get_server_status(target_ip):
    try:
        response = requests.get(f"https://api.mcsrvstat.us/3/{target_ip}")
        response.raise_for_status()
        
        data = response.json()
        online = data.get("ping")
        ip = data.get("ip")
        port = data.get("port")
        
        if online is not None and ip and port:
            return f"Server at {ip}:{port} is {'online' if online else 'offline'}."
        else:
            return "Could not determine the server status."
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except requests.exceptions.ConnectionError as conn_err:
        return f"Connection error occurred: {conn_err}"
    except requests.exceptions.Timeout as timeout_err:
        return f"Timeout error occurred: {timeout_err}"
    except requests.exceptions.RequestException as req_err:
        return f"An error occurred: {req_err}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# Main execution
while True:
    # Initialize speedtest client
    st = speedtest.Speedtest()

    # Get initial data usage
    initial_data_usage = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv

    # Perform speed test
    download_speed = st.download()
    upload_speed = st.upload()
    ping_result = st.results.ping

    # Clear the list of open ports
    open_ports_global = set()

    # Display banner with delay
    line = "<-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=->\n"
    os.system("cls")
    display_slowly(Fore.RED + line , 0.001)
    banner_text = "Minecraft Server Port Scan"
    display_slowly(Fore.RED + pyfiglet.figlet_format(banner_text) + Style.RESET_ALL)
    display_slowly(Fore.RED + line , 0.001)

    # Determine color based on ping value
    ping_color = Fore.GREEN if ping_result < 100 else Fore.YELLOW if ping_result <= 400 else Fore.RED

    # Determine color based on download speed
    download_color = Fore.GREEN if download_speed / 1024 / 1024 > 50 else Fore.YELLOW if download_speed / 1024 / 1024 >= 10 else Fore.RED

    # Determine color based on upload speed
    upload_color = Fore.GREEN if upload_speed / 1024 / 1024 > 30 else Fore.YELLOW if upload_speed / 1024 / 1024 >= 5 else Fore.RED

    # Display speed test results with delay
    display_slowly(Fore.CYAN + f"Download speed: {download_color}{download_speed / 1024 / 1024:.2f}{Fore.CYAN} Mbps" + Style.RESET_ALL, 0.01)
    display_slowly(Fore.CYAN + f"Upload speed: {upload_color}{upload_speed / 1024 / 1024:.2f}{Fore.CYAN} Mbps" + Style.RESET_ALL, 0.01)
    display_slowly(Fore.CYAN + f"Ping: {ping_color}{ping_result}{Fore.CYAN} ms" + Style.RESET_ALL, 0.01)

    # Get user input with delay
    target_ip = input(Fore.MAGENTA + "𝘌𝘯𝘵𝘦𝘳 𝘛𝘩𝘦 𝘐𝘱 𝘖𝘳 𝘏𝘰𝘴𝘵𝘯𝘢𝘮𝘦 𝘖𝘧 𝘛𝘩𝘦 𝘚𝘦𝘳𝘷𝘦𝘳: " + Style.RESET_ALL)
    server_status = get_server_status(target_ip)
    if server_status is not None and "error" not in server_status:
        print(Fore.GREEN + f"The server at the IP address you provided is online." + Style.RESET_ALL)
    else:
        print(Fore.RED + f"The server at the IP address you provided is offline or not responding." + Style.RESET_ALL)
    start_port = int(input(Fore.MAGENTA + "Enter the start port number: " + Style.RESET_ALL))
    end_port = int(input(Fore.MAGENTA + "Enter the end port number: " + Style.RESET_ALL))
    
    # Estimate and display scan duration
    minutes, seconds = estimate_scan_duration(start_port, end_port)
    display_slowly(Fore.CYAN + f"Estimated scan duration: {Fore.WHITE}{minutes}{Fore.CYAN} minutes and {Fore.WHITE}{seconds}{Fore.CYAN} seconds.", 0.01)
    time.sleep(2)

    # Perform port scan using threading
    display_slowly(Fore.CYAN + f"Scanning ports from [{Fore.WHITE}{start_port}{Fore.CYAN}] to [{Fore.WHITE}{end_port}{Fore.CYAN}] on [{Fore.WHITE}{target_ip}{Fore.CYAN}]..." + Style.RESET_ALL, 0.01)
    manage_threads(target_ip, start_port, end_port, open_ports_global)

    # Print open ports at the end of the scan with delay
    if open_ports_global:
        print_ports_table(open_ports_global, start_port, end_port)
    else:
        display_slowly(Fore.RED + "No open ports found." + Style.RESET_ALL, 0.01)

    # Calculate and print data usage with delay
    final_data_usage = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
    data_used = final_data_usage - initial_data_usage
    display_slowly(Fore.CYAN + f"Data used by this script: {Fore.WHITE}{data_used / 1024 / 1024:.2f}{Fore.CYAN} MB" + Style.RESET_ALL, 0.01)

    # Ask the user if they want to run the program again
    run_again = input(Fore.CYAN + "Do you want to run the program again? (y/n): " + Style.RESET_ALL)
    if run_again.lower() != "y":
        break
    else:
        display_slowly(Fore.CYAN + "Please wait a second for the code to run again...", 0.01)
