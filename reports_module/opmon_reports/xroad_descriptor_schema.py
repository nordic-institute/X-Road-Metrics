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
