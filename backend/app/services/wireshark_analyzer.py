import subprocess

class WiresharkAnalyzer:
    @staticmethod
    def analyze_pcap(file_path: str) -> list:
        """Runs tshark to extract network traffic data."""
        cmd = [
            "tshark", "-r", file_path,
            "-T", "fields",
            "-e", "ip.src", "-e", "ip.dst", "-e", "tcp.srcport", "-e", "tcp.dstport", "-e", "frame.protocols",
            "-E", "separator=,", "-E", "header=y"
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2: return []
            
            keys = lines[0].split(',')
            traffic_data = []
            for line in lines[1:101]: # Limit to 100 packets for API response
                values = line.split(',')
                traffic_data.append(dict(zip(keys, values)))
            return traffic_data
        except Exception as e:
            return [{"error": str(e)}]