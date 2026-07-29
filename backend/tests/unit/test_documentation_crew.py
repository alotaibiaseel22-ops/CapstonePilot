from app.infrastructure.agents.crews.documentation_crew import DocumentAnalysisSchema


def test_defaults_are_empty_not_none():
    analysis = DocumentAnalysisSchema()

    assert analysis.project_title == ""
    assert analysis.problem_statement == ""
    assert analysis.project_objectives == []
    assert analysis.target_users == []
    assert analysis.functional_requirements == []
    assert analysis.non_functional_requirements == []
    assert analysis.main_modules == []
    assert analysis.deliverables == []
    assert analysis.constraints == []
    assert analysis.technologies == []
    assert analysis.important_keywords == []


def test_round_trips_a_real_extraction_shaped_payload():
    payload = {
        "project_title": "Smart Campus Parking",
        "problem_statement": "Drivers waste time searching for open spots.",
        "project_objectives": ["Reduce search time", "Increase spot utilization"],
        "target_users": ["Students", "Faculty"],
        "functional_requirements": ["Predict spot occupancy", "Route drivers to open spots"],
        "non_functional_requirements": ["Respond within 2 seconds"],
        "main_modules": ["Sensor Ingestion", "Occupancy Prediction", "Mobile App"],
        "deliverables": ["Mobile app", "Backend API"],
        "constraints": ["Must run on existing campus WiFi"],
        "technologies": ["Python", "React Native"],
        "important_keywords": ["IoT", "occupancy prediction"],
    }

    analysis = DocumentAnalysisSchema.model_validate(payload)

    assert analysis.model_dump() == payload


def test_two_instances_with_the_same_data_serialize_identically():
    payload = {"project_title": "X", "main_modules": ["Auth", "Billing"]}

    first = DocumentAnalysisSchema.model_validate(payload)
    second = DocumentAnalysisSchema.model_validate(payload)

    assert first.model_dump_json() == second.model_dump_json()
