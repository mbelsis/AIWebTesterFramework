class SampleHook:
    def after_generate(self, plan, context):
        plan["name"] = "from-file"
        return plan


HOOKS = [SampleHook()]
