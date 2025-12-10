class Requirement(BaseModel):
    id: str
    name: str
    description: str

    criterion_template: CriterionTemplate
    applicability: ApplicabilityRules
    inherit_mode: InheritMode           # INHERIT, OVERRIDE, SKIP
    enabled: bool = True
    overrides: List[str] = []
