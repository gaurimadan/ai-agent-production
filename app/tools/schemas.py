TOOL_SCHEMAS = [

    {
        "name": "get_order",
        "description": "Get order information",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string"
                }
            },
            "required": ["order_id"]
        }
    },

    {
        "name": "cancel_order",
        "description": "Cancel a shipped order",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string"
                }
            },
            "required": ["order_id"]
        }
    },

    {
        "name": "refund_order",
        "description": "Initiate a refund",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string"
                }
            },
            "required": ["order_id"]
        }
    }
]