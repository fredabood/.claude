class Criterion(BaseModel):
    # ... existing fields ...

    def evaluate(self, activity_log: List[ActivityLogEntry]) -> bool:
        """
        Evaluate criterion and log if non-required.

        Non-required criteria:
        - Always logged to activity_log (met or not)
        - Emit warning if not met
        - Return True regardless (don't block)
        """
        satisfied = self.target.is_satisfied()

        if not self.required:
            activity_log.append(ActivityLogEntry(
                timestamp=datetime.now(timezone.utc),
                type=ActivityType.CRITERION_EVALUATED,
                description=f"Non-required criterion '{self.id}': {'met' if satisfied else 'not met'}",
                entity_type="criterion",
                entity_id=self.id,
                context={"criterion_id": self.id, "met": satisfied, "required": False}
            ))
            if not satisfied:
                logger.warning(f"Non-required criterion not met: {self.description}")
            return True  # Non-required always passes

        return satisfied
