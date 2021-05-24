#  The MIT License
#  Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
#  Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

xroad_descriptor_schema = {
    "type": "array",
    "items": {"$ref": "#/$defs/xroad-subsystem"},

    "$defs": {

        "xroad-subsystem": {
            "type": "object",
            "required": [
                "x_road_instance",
                "member_class",
                "member_code",
                "subsystem_code"
            ],
            "properties": {
                "x_road_instance": {"type": "string"},
                "member_class": {"type": "string"},
                "member_code": {"type": "string"},
                "member_name": {"type": "string"},
                "subsystem_code": {"type": "string"},
                "subsystem_name": {"$ref": "#/$defs/subsystem-name"},
                "email": {"$ref": "#/$defs/email"}
            }
        },


        "email": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "email"],
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"}
                }
            }
        },


        "subsystem-name": {
            "type": "object",
            "minProperties": 1,
            "additionalProperties": {
                "type": "string"
            }
        }
    }
}
