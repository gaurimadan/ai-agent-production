ORDERS = {
    "ORD001": {
        "id": "ORD001",
        "customer": "Gauri",
        "status": "shipped",
        "amount": 1299,
        "item": "Wireless Headphones"
    },
    "ORD002": {
        "id": "ORD002",
        "customer": "Gauri",
        "status": "delivered",
        "amount": 2499,
        "item": "Smart Watch"
    }
}


def get_order(order_id: str):

    order = ORDERS.get(order_id)

    if not order:
        return {
            "success": False,
            "error": "Order not found"
        }

    return {
        "success": True,
        "order": order
    }


def cancel_order(order_id: str):

    order = ORDERS.get(order_id)

    if not order:
        return {
            "success": False,
            "error": "Order not found"
        }

    if order["status"] != "shipped":
        return {
            "success": False,
            "error": "Only shipped orders can be cancelled"
        }

    order["status"] = "cancelled"

    return {
        "success": True,
        "message": f"Order {order_id} cancelled"
    }


def refund_order(order_id: str):

    order = ORDERS.get(order_id)

    if not order:
        return {
            "success": False,
            "error": "Order not found"
        }

    return {
        "success": True,
        "message": f"Refund initiated for {order_id}",
        "amount": order["amount"]
    }