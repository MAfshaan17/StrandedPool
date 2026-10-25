from app.services.demo_simulation import run_demo_simulation


def test_demo_simulation_respects_capacity_and_compares_same_dataset():
    result = run_demo_simulation()
    comparison = result["allocation_comparison"]
    pooled = comparison["pooling"]
    independent = comparison["non_pooling"]

    assert result["data_label"] == "SIMULATED demo only"
    assert comparison["same_travellers_and_constraints"] is True
    assert pooled["assigned_travellers"] == independent["assigned_travellers"] == 3
    assert len(pooled["assignments"]) == 1
    assert pooled["assignments"][0]["passenger_count"] <= pooled["assignments"][0]["capacity"]
    assert len(pooled["assignments"][0]["traveller_ids"]) == len(
        set(pooled["assignments"][0]["traveller_ids"])
    )
    assert len(independent["assignments"]) == 3
    assert len(
        {assignment["option_id"] for assignment in independent["assignments"]}
    ) == len(independent["assignments"])
    assert all(
        assignment["passenger_count"] <= assignment["capacity"]
        for assignment in independent["assignments"]
    )
    assert pooled["total_additional_cost"] == 300
    assert pooled["average_additional_cost_per_assigned_traveller"] == 100
    assert independent["total_additional_cost"] == 1500
    assert independent["average_additional_cost_per_assigned_traveller"] == 500
    assert result["metrics"]["downstream_bookings_identified"] == 2
    assert result["metrics"]["recovery_plan_generation_ms"] >= 0
    assert result["recovery_itinerary"]["booking_changes_made"] is False
    assert result["editable_action_drafts"]["hotel_late_checkin"]["sent"] is False
