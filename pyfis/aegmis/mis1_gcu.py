"""
Copyright (C) 2020 Julian Metzler

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import serial
import time


class MIS1GCUDisplay:
    ALIGN_LEFT = 0x00
    ALIGN_RIGHT = 0x01
    ALIGN_CENTER = 0x02
    ALIGN_SCROLL = 0x03 # apparently not supported
    
    ATTR_BLINK = 0x01
    ATTR_INVERT = 0x02
    ATTR_BLINK_INV = 0x08
    
    DATE_FORMAT_DISABLE = 0x00
    DATE_FORMAT_DDMMYY = 0x01
    DATE_FORMAT_MMDDYY = 0x02
    DATE_FORMAT_YYMMDD = 0x03
    
    TIME_FORMAT_DISABLE = 0x00
    TIME_FORMAT_24H = 0x01
    TIME_FORMAT_12H_AM_PM = 0x02
    TIME_FORMAT_12H = 0x03
    
    def __init__(self, port, address = 1, baudrate = 9600, exclusive = False):
        self.address = address
        self.port = serial.Serial(port, baudrate=baudrate, bytesize=8, parity="E", stopbits=1, exclusive=exclusive)

    def checksum(self, data):
        checksum = 0x00
        for i, byte in enumerate(data):
            checksum += byte
        return (checksum % 256) | 0x80

    def escape(self, data):
        escaped = []
        for byte in data:
            if byte in (0x02, 0x03, 0x04, 0x05, 0x10):
                escaped += [0x10, byte]
            else:
                escaped.append(byte)
        return escaped
    
    def send_raw_telegram(self, data):
        telegram = [0x04, (0x80 | self.address), 0x02] + self.escape(data) + [0x03] + [self.checksum(data + [0x03])]
        print([hex(b) for b in telegram])
        self.port.setRTS(1)
        self.port.write(telegram)
        time.sleep(0.1)
        self.port.setRTS(0)
    
    def send_command(self, code, subcode, data):
        return self.send_raw_telegram([code, subcode] + data)
    
    def merge_attributes(self, text):
        if type(text) in (tuple, list):
            merged = ""
            for t, attrs in text:
                merged += "\x00" + chr(attrs) + t
            return merged
        return text

    def simple_text(self, page, row, col, text, align = ALIGN_LEFT):
        text = self.merge_attributes(text)
        text = text.encode("CP437")
        data = [align, page, row, col] + list(text)
        return self.send_command(0x11, 0x00, data)

    def text(self, page, row, col_start, col_end, text, align = ALIGN_LEFT):
        text = self.merge_attributes(text)
        text = text.encode("CP437")
        data = [align, page, row, col_start >> 8, col_start & 0xFF, col_end >> 8, col_end & 0xFF] + list(text)
        return self.send_command(0x15, 0x00, data)
    
    def set_pages(self, pages):
        flat_pages = [item for sublist in pages for item in sublist]
        data = [0x00] + flat_pages
        return self.send_command(0x24, 0x00, data)
    
    def set_page(self, page):
        return self.set_pages([(page, 255)])
    
    def set_clock(self, year, month, day, hour, minute, second):
        # apparently unsupported
        data = list(divmod(second, 10)[::-1])
        data += divmod(minute, 10)[::-1]
        data += divmod(hour, 10)[::-1]
        data += divmod(day, 10)[::-1]
        data += divmod(month, 10)[::-1]
        data += divmod(year, 10)[::-1]
        data += [0x00] # weekday, unused
        return self.send_command(0x3A, 0x00, data)
    
    def set_clock_display(self, date_format, date_row, date_col_start, date_col_end, time_format, time_row, time_col_start, time_col_end):
        # apparently unsupported
        data = [date_format, date_row]
        data += [date_col_start >> 8, date_col_start & 0xFF]
        data += [date_col_end >> 8, date_col_end & 0xFF]
        data += [time_format, time_row]
        data += [time_col_start >> 8, time_col_start & 0xFF]
        data += [time_col_end >> 8, time_col_end & 0xFF]
        return self.send_command(0x3D, 0x00, data)
