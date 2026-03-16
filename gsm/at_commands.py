"""
AT command constants and helper functions.
"""
# Basic commands
AT = "AT"
ATE0 = "ATE0"  # Echo off
AT_CSQ = "AT+CSQ"  # pyqtSignal quality
AT_COPS = "AT+COPS?"  # Operator selection
AT_CREG = "AT+CREG?"  # Network registration
AT_CGREG = "AT+CGREG?"  # GPRS registration
AT_CEREG = "AT+CEREG?"  # EPS registration

# SIM related (vendor specific, example for Quectel)
AT_QUICSEL = "AT+QUICSEL"  # Quectel SIM switch

# Call control
ATD = "ATD{};"  # Dial
ATH = "ATH"  # Hang up

# SMS
AT_CMGF = "AT+CMGF={}"  # Set SMS mode (1=text)
AT_CMGS = "AT+CMGS=\"{}\""  # Send SMS

def parse_csq(response: str) -> int:
    """Extract RSSI from +CSQ response. Returns 0-31 or -1 if invalid."""
    try:
        if '+CSQ:' in response:
            parts = response.split(':')[1].strip().split(',')
            rssi = int(parts[0])
            return rssi
    except:
        pass
    return -1

def parse_cops(response: list) -> dict:
    """Parse +COPS response to extract operator info."""
    info = {'operator': 'Unknown', 'mode': 'Unknown', 'format': 'Unknown'}
    for line in response:
        if '+COPS:' in line:
            # +COPS: <mode>[, <format>[, <oper>][, <act>]]
            parts = line.split(':')[1].strip().split(',')
            if len(parts) >= 3:
                info['mode'] = parts[0].strip()
                info['format'] = parts[1].strip()
                info['operator'] = parts[2].strip().strip('"')
            break
    return info
