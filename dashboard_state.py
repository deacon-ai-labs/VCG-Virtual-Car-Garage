def apply_vehicle_selection(
    current_vehicle_id,
    selected_vehicle_id,
    active_conversation_id,
) -> dict:
    """Return dashboard state after a vehicle-card selection."""

    if selected_vehicle_id == current_vehicle_id:
        return {
            "active_vehicle_id": current_vehicle_id,
            "active_conversation_id": active_conversation_id,
        }

    return {
        "active_vehicle_id": selected_vehicle_id,
        "active_conversation_id": None,
    }
